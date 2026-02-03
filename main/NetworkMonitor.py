import subprocess

# Use the FULL PATH to the exe.
# The 'r' before the quotes is important for Windows paths!
ADB_PATH = r"C:\Users\student\Documents\platform-tools\adb.exe"

# --- CLASS 2: NETWORK MONITOR ---
# Handles Requirement: Interaction with OS (Android/ADB)
class NetworkMonitor:
    def __init__(self, hub_ip="192.168.43.1"):
        self.hub_ip = hub_ip

    def connect_to_hub(self):
        """Attempts to connect ADB to the Control Hub."""
        print(f"Connecting to Hub at {self.hub_ip}...")
        result = subprocess.run([ADB_PATH, "connect", self.hub_ip], capture_output=True, text=True)
        return "connected" in result.stdout

    def get_connected_devices(self):
        """Queries the Hub's ARP table to see other connected devices."""
        # This command asks the Hub's Android OS for its network neighbors
        cmd = ["adb", "-s", f"{self.hub_ip}:5555", "shell", "ip", "neighbor", "show"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Simple parsing to extract IP addresses
        lines = result.stdout.strip().split('\n')
        found_ips = []
        for line in lines:
            if "REACHABLE" in line or "STALE" in line:
                ip = line.split()[0]
                found_ips.append(ip)
        return found_ips