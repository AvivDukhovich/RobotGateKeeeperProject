# threat_simulator.py
import socket
import time
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT, COMMAND_CENTER_IP

def simulate_threat(robot_name, threat_type):
    sec = SecureSocket(key=SECRET_KEY)
    
    messages = {
        "unauthorized": f"{robot_name} | UNAUTHORIZED: 192.168.43.99 (REACHABLE)",
        "spoof": f"{robot_name} | CRITICAL: MAC Spoofing detected on Hub!",
        "heartbeat": f"{robot_name} | System Status: OK"
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            print(f"[*] Connecting to Command Center at {COMMAND_CENTER_IP}...")
            s.connect((COMMAND_CENTER_IP, SERVER_PORT))
            
            payload = messages.get(threat_type, messages["heartbeat"])
            s.sendall(sec.encrypt_message(payload))
            print(f"[+] Sent '{threat_type}' alert to Command Center.")
    except Exception as e:
        print(f"[!] Simulation failed: {e}")

if __name__ == "__main__":
    # You can change these values to test different scenarios
    simulate_threat("Barnyard-Test-Bot", "unauthorized")