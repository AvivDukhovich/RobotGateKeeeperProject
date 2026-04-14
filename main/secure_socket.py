"""
SecureSocket - Symmetric Encryption Layer
This module implements the Fernet (AES-128 in CBC mode) encryption standard 
to secure inter-process communication. It ensures that data transmitted 
between the network monitor and the GUI remains confidential and tamper-proof.
"""

from cryptography.fernet import Fernet


class SecureSocket:
    def __init__(self, key=None):
        """
        Initializes the cryptographic cipher with a provided or generated key.

        Args:
            key (bytes, optional): A 32-byte base64-encoded key. If None, a 
                                   new key is generated for the session.
        """
        # Requirement: Encryption of sensitive data to prevent local sniffing
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key

        # Initialize the Fernet cipher suite (Symmetric Encryption)
        self.cipher = Fernet(self.key)

    def encrypt_message(self, message):
        """
        Encrypts a plaintext string into a secure ciphertext.

        Args:
            message (str): The raw alert or data string to be secured.

        Returns:
            bytes: The encrypted token (ciphertext).
        """
        return self.cipher.encrypt(message.encode())

    def decrypt_message(self, encrypted_data):
        """
        Decrypts a ciphertext token back into its original plaintext string.

        Args:
            encrypted_data (bytes): The encrypted message received from the socket.

        Returns:
            str: The original decoded message string.
        """
        return self.cipher.decrypt(encrypted_data).decode()
