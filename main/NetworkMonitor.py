import subprocess
from config import ADB_PATH, HUB_IP, ADB_PORT

class NetworkMonitor:
    def __init__(self):
        self.hub_address = f"{HUB_IP}:{ADB_PORT}"

    def _run_adb(self, args):
        try:
            return subprocess.run(
                [ADB_PATH] + args,
                capture_output=True,
                text=True,
                timeout=5  # ⬅ MUCH shorter timeout
            )
        except subprocess.TimeoutExpired:
            print("ADB command timed out!")
            return subprocess.CompletedProcess(args, 1, "", "")

    def connect_to_hub(self):
        print(f"Connecting to REV Control Hub at {self.hub_address}...")
        result = self._run_adb(["connect", self.hub_address])
        print(result.stdout.strip())
        return "connected" in result.stdout.lower()

    def get_connected_devices(self):
        result = self._run_adb(["-s", self.hub_address, "shell", "ip", "neighbor", "show"])
        devices = []
        
        for line in result.stdout.splitlines():
            # Check for the status in the line
            status = None
            if "REACHABLE" in line:
                status = "ACTIVE"
            elif "STALE" in line or "DELAY" in line:
                status = "STALE"

            if status:
                parts = line.split()
                if len(parts) > 0:
                    ip = parts[0]
                    if ip.startswith("192.168.43."):
                        devices.append((ip, status)) # Return both as a pair
        return devices



