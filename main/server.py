import socket
import threading
from main.SecureSocket import SecureSocket

class SecurityServer:
    def __init__(self, host='0.0.0.0', port=5005):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        # Use a fixed key for testing so Client and Server match
        self.sec = SecureSocket(key=b'YOUR_FIXED_32_BYTE_KEY_HERE=') 

    def start(self):
        print(f"Server listening on port 5005...")
        # Requirement: Usage of Threads
        threading.Thread(target=self.receive_data, daemon=True).start()

    def receive_data(self):
        while True:
            client, addr = self.server_socket.accept()
            data = client.recv(1024)
            # Requirement: Decryption of incoming data
            decrypted_msg = self.sec.decrypt_message(data)
            print(f"ALERT FROM MONITOR: {decrypted_msg}")