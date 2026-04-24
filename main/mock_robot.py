import socket
import time
import random
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT

# Simulation Settings
MASTER_IP = "127.0.0.1"
SIM_ROBOT_ID = "ROBOT_SIM_01"


def send_mock_event(event_text):
    """Encrypts the message and sends it via a standard socket."""
    try:
        # 1. Create the encryption tool
        # Your class takes (self, key=None). So we pass SECRET_KEY.
        crypto = SecureSocket(key=SECRET_KEY)

        # 2. Prepare and Encrypt the message
        raw_message = f"{SIM_ROBOT_ID} | {event_text}"
        encrypted_bytes = crypto.encrypt_message(raw_message)

        # 3. Create a standard network socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((MASTER_IP, SERVER_PORT))

        # 4. Send the encrypted bytes
        sock.sendall(encrypted_bytes)

        print(f"[SENT] {raw_message}")
        sock.close()
    except Exception as e:
        print(f"[ERROR] {e}")


def run_simulation():
    print(f"--- Starting Simulation for {SIM_ROBOT_ID} ---")
    send_mock_event("STATUS: CONNECTED")

    try:
        count = 0
        while True:
            time.sleep(10)
            count += 1
            if count % 5 == 0:
                send_mock_event(
                    f"UNAUTHORIZED DEVICE DETECTED: 192.168.1.{random.randint(100, 200)}")
            else:
                send_mock_event("STATUS: HEARTBEAT")
    except KeyboardInterrupt:
        print("\n--- Simulation Ended ---")


if __name__ == "__main__":
    run_simulation()
