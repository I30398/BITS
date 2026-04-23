"""
Distributed Mutual Exclusion Middleware
Implements Ricart-Agrawala Algorithm
"""

import socket
import threading
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [DME] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('DME')


class RicartAgrawala:
    """
    Ricart-Agrawala Distributed Mutual Exclusion Algorithm

    Message Types:
    - REQUEST: Node requests access to critical section
    - REPLY: Node grants permission to requesting node
    """

    def __init__(self, node_id, node_config):
        """
        Initialize DME middleware

        Args:
            node_id: Unique identifier for this node (e.g., 'node1', 'node2')
            node_config: Dict mapping node_id -> (host, port) for all nodes
        """
        self.node_id = node_id
        self.node_config = node_config
        self.clock = 0  # Lamport logical clock
        self.request_clock = 0  # Timestamp of our request
        self.requesting = False  # Are we requesting CS?
        self.in_cs = False  # Are we in CS?
        self.replies_received = set()  # Nodes that replied to our request
        self.deferred_replies = []  # Requests we deferred replying to

        self.lock = threading.Lock()
        self.cs_lock = threading.Condition(self.lock)

        # Get other nodes (excluding self and server)
        self.other_nodes = [nid for nid in node_config.keys()
                          if nid != node_id and nid != 'server']

        # Start listener thread
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

        logger.info(f"Node {node_id} initialized. Other nodes: {self.other_nodes}")

    def _increment_clock(self):
        """Increment Lamport clock"""
        self.clock += 1
        return self.clock

    def _update_clock(self, received_clock):
        """Update clock based on received message"""
        self.clock = max(self.clock, received_clock) + 1

    def _listen(self):
        """Listen for incoming messages from other nodes"""
        _, port = self.node_config[self.node_id]
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))  # Listen on all interfaces
        server_socket.listen(5)
        server_socket.settimeout(1.0)

        logger.info(f"Listening on {host}:{port}")

        while self.running:
            try:
                conn, addr = server_socket.accept()
                threading.Thread(target=self._handle_message,
                               args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Listen error: {e}")

        server_socket.close()

    def _handle_message(self, conn):
        """Handle incoming message"""
        reply_to = None
        try:
            data = conn.recv(4096).decode()
            msg = json.loads(data)

            msg_type = msg['type']
            sender = msg['sender']
            msg_clock = msg['clock']

            with self.lock:
                self._update_clock(msg_clock)

                if msg_type == 'REQUEST':
                    logger.info(f"Received REQUEST from {sender} (clock={msg_clock})")
                    reply_to = self._handle_request(sender, msg_clock)

                elif msg_type == 'REPLY':
                    logger.info(f"Received REPLY from {sender}")
                    self.replies_received.add(sender)
                    self.cs_lock.notify_all()

        except Exception as e:
            logger.error(f"Handle message error: {e}")
        finally:
            conn.close()

        # Send reply outside the lock
        if reply_to:
            self._send_reply(reply_to)

    def _handle_request(self, sender, sender_clock):
        """
        Handle REQUEST message using Ricart-Agrawala rules:
        - If not requesting or in CS, send REPLY immediately
        - If requesting, compare timestamps:
          - If our request has lower timestamp, defer reply
          - Otherwise, send REPLY immediately

        Returns sender if should reply immediately, None if deferred
        """
        should_defer = False

        if self.requesting or self.in_cs:
            # Compare (clock, node_id) tuples
            our_priority = (self.request_clock, self.node_id)
            their_priority = (sender_clock, sender)

            if our_priority < their_priority:
                # Our request has higher priority (lower timestamp)
                should_defer = True
                logger.info(f"Deferring reply to {sender} (our priority: {our_priority} < their: {their_priority})")

        if should_defer:
            self.deferred_replies.append(sender)
            return None
        else:
            logger.info(f"Will send immediate REPLY to {sender}")
            return sender

    def _send_message(self, target_node, msg_type):
        """Send message to target node"""
        try:
            host, port = self.node_config[target_node]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))

            msg = {
                'type': msg_type,
                'sender': self.node_id,
                'clock': self.clock
            }
            sock.send(json.dumps(msg).encode())
            sock.close()
            return True
        except Exception as e:
            logger.error(f"Failed to send {msg_type} to {target_node}: {e}")
            return False

    def _send_reply(self, target_node):
        """Send REPLY message"""
        self._increment_clock_safe()
        logger.info(f"Sending REPLY to {target_node}")
        self._send_message(target_node, 'REPLY')

    def _increment_clock_safe(self):
        """Increment clock with lock"""
        with self.lock:
            self._increment_clock()

    def _send_requests(self):
        """Send REQUEST to all other nodes"""
        for node in self.other_nodes:
            logger.info(f"Sending REQUEST to {node}")
            self._send_message(node, 'REQUEST')

    def request_cs(self):
        """
        Request entry to critical section
        Blocks until access is granted
        """
        with self.lock:
            self.requesting = True
            self.request_clock = self._increment_clock()
            self.replies_received = set()

            logger.info(f"=== REQUESTING CS (clock={self.request_clock}) ===")

        # Send REQUEST to all other nodes
        self._send_requests()

        # Wait for all replies
        with self.cs_lock:
            while len(self.replies_received) < len(self.other_nodes):
                logger.info(f"Waiting for replies: {len(self.replies_received)}/{len(self.other_nodes)}")
                self.cs_lock.wait(timeout=1.0)

        with self.lock:
            self.in_cs = True
            self.requesting = False
            logger.info("=== ENTERED CRITICAL SECTION ===")

    def release_cs(self):
        """
        Release critical section
        Send deferred replies
        """
        with self.lock:
            self.in_cs = False
            deferred = self.deferred_replies.copy()
            self.deferred_replies = []

            logger.info(f"=== RELEASED CRITICAL SECTION ===")
            logger.info(f"Sending {len(deferred)} deferred replies")

        # Send deferred replies
        for node in deferred:
            logger.info(f"Sending deferred REPLY to {node}")
            self._send_reply(node)

    def shutdown(self):
        """Shutdown the middleware"""
        self.running = False
        logger.info("DME middleware shutdown")
