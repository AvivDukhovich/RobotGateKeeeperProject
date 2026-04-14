"""
ThreatSimulator - Security Testing Utility
This module simulates network intrusion events by generating mock connection 
data. It is used to validate the response time, encryption integrity, and 
alerting accuracy of the RobotGateKeeper IDS without requiring a live 
network attack.
"""

import time
import socket
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT


class ThreatSimulator:
    def __init__(self):
        """
        Initializes the simulator with the shared cryptographic key
        to ensure the GUI can successfully decrypt the 'attack' data.
        """
        self.sec = SecureSocket(key=SECRET_KEY)
        self.target_host = '127.0.0.1'  # Sending to the local GUI server
        self.target_port = SERVER_PORT

    def simulate_intrusion(self, fake_ip):
        """
        Crafts and sends an encrypted 'Unauthorized' alert to the GUI.

        Args:
            fake_ip (str): The mock IP address of the 'intruder'.
        """
        print(f"[TEST] Simulating intrusion from: {fake_ip}")

        # Formatting the message to match the NetworkMonitor's output
        # This tests if the GUI's regex/tagging logic works
        test_msg = f"[ACTIVE] UNAUTHORIZED: {fake_ip}"

        try:
            # Encrypt the mock alert
            encrypted_alert = self.sec.encrypt_message(test_msg)

            # Establish connection to the GUI's listener
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.target_host, self.target_port))
                s.sendall(encrypted_alert)

            print(f"[SUCCESS] Intrusion alert for {fake_ip} transmitted.")
        except ConnectionRefusedError:
            print("[ERROR] Simulation failed: Is the Security GUI running?")
        except Exception as e:
            print(f"[ERROR] Unexpected simulation error: {e}")

    def run_scenario(self):
        """
        Executes a pre-defined attack pattern to stress-test the IDS.
        """
        print("--- Starting Threat Simulation Scenario ---")
        mock_attackers = [
            "192.168.43.99",
            "192.168.43.250",
            "10.0.0.5"  # Testing an IP outside the robot subnet
        ]

        for ip in mock_attackers:
            self.simulate_intrusion(ip)
            time.sleep(3)  # Wait between 'attacks' to check GUI refresh rate


if __name__ == "__main__":
    simulator = ThreatSimulator()
    simulator.run_scenario()
