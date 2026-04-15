import subprocess
from config import ADB_PATH, HUB_IP, ADB_PORT

class NetworkMonitor:
    def __init__(self, mode="usb"):
        self.mode = mode
        self.hub_address = f"{HUB_IP}:{ADB_PORT}"

    def _run_adb(self, args):
        cmd = [ADB_PATH]
        if self.mode == "wifi":
            cmd += ["-s", self.hub_address]
        
        try:
            return subprocess.run(cmd + args, capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 1, "", "Timeout")

    def connect_to_hub(self):
        if self.mode == "wifi":
            result = self._run_adb(["connect", self.hub_address])
            return "connected" in result.stdout.lower()
        else:
            # USB Mode: Just check if 'device' appears in the list
            result = self._run_adb(["devices"])
            lines = result.stdout.strip().splitlines()
            return any("device" in l and "List" not in l for l in lines)

    def get_connected_devices(self):
        # 1. Force a discovery ping to the broadcast address
        self._run_adb(["shell", "ping", "-c", "1", "-b", "192.168.43.255"])
        
        # 2. Use 'nud reachable' - this is the "Golden Filter"
        # It ONLY returns devices that are actively responding to the Hub
        result = self._run_adb(["shell", "ip", "neighbor", "show", "nud", "reachable"])
        
        devices = []
        if result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split()
                if not parts: continue
                
                ip = parts[0]
                if "192.168.43." in ip and ip != "192.168.43.1":
                    # In 'nud reachable' mode, we don't need to check the string
                    # because the Hub only returns active ones.
                    devices.append((ip, "ACTIVE"))
                    
        return devices