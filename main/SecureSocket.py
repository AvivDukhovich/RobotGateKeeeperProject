import socket
from cryptography.fernet import Fernet

class SecureSocket:
    def __init__(self, key=None):
        # Requirement: Encryption of sensitive data
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        self.cipher = Fernet(self.key)

    def encrypt_message(self, message):
        return self.cipher.encrypt(message.encode())

    def decrypt_message(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()