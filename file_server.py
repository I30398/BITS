"""
File Server Node
Maintains the shared chat file and provides read/write APIs
"""

import socket
import threading
import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [SERVER] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FileServer')

SHARED_FILE = "chat_messages.txt"


class FileServer:
    """
    File Server that maintains the shared chat file
    Provides view and post APIs via TCP
    """

    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.file_lock = threading.Lock()
        self.running = True

        # Initialize shared file
        if not os.path.exists(SHARED_FILE):
            with open(SHARED_FILE, 'w') as f:
                f.write("")
            logger.info(f"Created shared file: {SHARED_FILE}")

    def _handle_client(self, conn, addr):
        """Handle client request"""
        try:
            data = conn.recv(4096).decode()
            request = json.loads(data)

            command = request.get('command')
            logger.info(f"Received '{command}' request from {addr}")

            if command == 'view':
                response = self._handle_view()
            elif command == 'post':
                response = self._handle_post(request)
            else:
                response = {'status': 'error', 'message': 'Unknown command'}

            conn.send(json.dumps(response).encode())

        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            try:
                conn.send(json.dumps({'status': 'error', 'message': str(e)}).encode())
            except:
                pass
        finally:
            conn.close()

    def _handle_view(self):
        """Handle view command - read shared file"""
        with self.file_lock:
            try:
                with open(SHARED_FILE, 'r') as f:
                    content = f.read()
                logger.info(f"View: returning {len(content)} bytes")
                return {'status': 'ok', 'content': content}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

    def _handle_post(self, request):
        """Handle post command - append to shared file"""
        timestamp = request.get('timestamp', 'Unknown')
        user_id = request.get('user_id', 'Unknown')
        text = request.get('text', '')

        with self.file_lock:
            try:
                with open(SHARED_FILE, 'a') as f:
                    line = f"{timestamp} {user_id}: {text}\n"
                    f.write(line)
                logger.info(f"Post: appended message from {user_id}")
                return {'status': 'ok', 'message': 'Posted successfully'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

    def start(self):
        """Start the file server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)

        logger.info(f"File Server started on {self.host}:{self.port}")
        logger.info(f"Shared file: {SHARED_FILE}")
        print(f"\n{'='*50}")
        print(f"CHAT ROOM FILE SERVER")
        print(f"{'='*50}")
        print(f"Host: {self.host}:{self.port}")
        print(f"File: {SHARED_FILE}")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*50}\n")

        try:
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    threading.Thread(target=self._handle_client,
                                   args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        finally:
            server_socket.close()


if __name__ == "__main__":
    import sys

    host = 'localhost'
    port = 5000

    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server = FileServer(host, port)
    server.start()
