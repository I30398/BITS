"""
Chat Room Client Application
Distributed application that uses DME middleware for mutual exclusion
"""

import socket
import json
import sys
from datetime import datetime
import logging
from dme_middleware import RicartAgrawala

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [APP] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('ChatApp')


class ChatClient:
    """
    Chat Room Client Application
    Uses DME middleware for write access control
    """

    def __init__(self, node_id, user_name, node_config, server_config):
        """
        Initialize chat client

        Args:
            node_id: Unique node identifier (e.g., 'node1')
            user_name: Display name for this user
            node_config: DME node configuration
            server_config: (host, port) tuple for file server
        """
        self.node_id = node_id
        self.user_name = user_name
        self.server_host, self.server_port = server_config

        # Initialize DME middleware
        logger.info(f"Initializing DME middleware for {node_id}")
        self.dme = RicartAgrawala(node_id, node_config)

        print(f"\n{'='*50}")
        print(f"CHAT ROOM CLIENT - {user_name}")
        print(f"{'='*50}")
        print(f"Node ID: {node_id}")
        print(f"Server: {self.server_host}:{self.server_port}")
        print(f"\nCommands:")
        print(f"  view              - View all messages")
        print(f"  post <message>    - Post a new message")
        print(f"  exit              - Exit the application")
        print(f"{'='*50}\n")

    def _send_to_server(self, request):
        """Send request to file server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((self.server_host, self.server_port))
            sock.send(json.dumps(request).encode())
            response = json.loads(sock.recv(65536).decode())
            sock.close()
            return response
        except Exception as e:
            logger.error(f"Server communication error: {e}")
            return {'status': 'error', 'message': str(e)}

    def view(self):
        """
        View command - read messages from server
        No mutual exclusion needed for reads (multiple viewers allowed)
        """
        logger.info("Executing VIEW command")
        response = self._send_to_server({'command': 'view'})

        if response.get('status') == 'ok':
            content = response.get('content', '')
            if content.strip():
                print("\n" + "-"*40)
                print(content.rstrip())
                print("-"*40 + "\n")
            else:
                print("\n[No messages yet]\n")
        else:
            print(f"\n[Error: {response.get('message')}]\n")

    def post(self, message):
        """
        Post command - write message to server
        Uses DME for mutual exclusion (only one writer at a time)
        """
        if not message.strip():
            print("[Error: Message cannot be empty]")
            return

        logger.info(f"Executing POST command: '{message}'")

        # Get current timestamp BEFORE requesting CS (as per requirement)
        timestamp = datetime.now().strftime("%d %b %I:%M%p")

        print("[Requesting write access...]")
        logger.info("Requesting critical section for POST")

        # Request critical section using DME
        self.dme.request_cs()

        try:
            logger.info("In critical section - sending POST to server")
            print("[Write access granted - posting message...]")

            request = {
                'command': 'post',
                'timestamp': timestamp,
                'user_id': self.user_name,
                'text': message
            }
            response = self._send_to_server(request)

            if response.get('status') == 'ok':
                print("[Message posted successfully]")
            else:
                print(f"[Error: {response.get('message')}]")

        finally:
            # Always release critical section
            logger.info("Releasing critical section")
            self.dme.release_cs()
            print("[Write access released]\n")

    def run(self):
        """Main command loop"""
        try:
            while True:
                try:
                    user_input = input(f"{self.user_name}> ").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()

                if command == 'view':
                    self.view()

                elif command == 'post':
                    if len(parts) < 2:
                        print("[Usage: post <message>]")
                    else:
                        # Remove surrounding quotes if present
                        message = parts[1].strip('"\'')
                        self.post(message)

                elif command == 'exit':
                    print("Goodbye!")
                    break

                else:
                    print(f"[Unknown command: {command}]")
                    print("[Commands: view, post <message>, exit]")

        except KeyboardInterrupt:
            print("\nGoodbye!")
        finally:
            self.dme.shutdown()


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python chat_client.py <node_id> <user_name>")
        print("  node_id: 'node1' or 'node2'")
        print("  user_name: Your display name")
        print("\nExample: python chat_client.py node1 Lucy")
        sys.exit(1)

    node_id = sys.argv[1]
    user_name = sys.argv[2]

    # ===========================================
    # CONFIGURATION - UPDATE THESE IP ADDRESSES
    # ===========================================
    # Replace with actual IP addresses of your servers
    SERVER_IP = '192.168.1.10'    # IP of file server machine
    NODE1_IP = '192.168.1.11'     # IP of node1 machine
    NODE2_IP = '192.168.1.12'     # IP of node2 machine

    node_config = {
        'node1': (NODE1_IP, 5001),  # DME port for node1
        'node2': (NODE2_IP, 5002),  # DME port for node2
    }

    # File server configuration
    server_config = (SERVER_IP, 5000)

    if node_id not in node_config:
        print(f"Error: Unknown node_id '{node_id}'")
        print("Valid node IDs: node1, node2")
        sys.exit(1)

    # Create and run client
    client = ChatClient(node_id, user_name, node_config, server_config)
    client.run()


if __name__ == "__main__":
    main()
