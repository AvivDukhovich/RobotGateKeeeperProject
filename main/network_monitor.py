"""
NetworkMonitor - ADB-Based Hardware Interface
This module provides a low-level interface between the IDS Engine and the 
REV Control Hub. It uses the Android Debug Bridge (ADB) to execute shell 
commands on the Hub's Android OS to retrieve real-time network states.

Key Strategy:
The module utilizes the 'ip neighbor' command with the 'nud reachable' filter. 
This acts as a "Golden Filter," ensuring that the system only reports devices 
actively communicating with the Hub, effectively ignoring stale or 
disconnected ARP entries.
"""

import subprocess
from config import ADB_PATH, HUB_IP, ADB_PORT

class NetworkMonitor:
    def __init__(self, mode="usb"):
        """
        Initializes the monitor with a specific connection strategy.
        
        Args:
            mode (str): 'usb' for direct tethering, 'wifi' for remote monitoring.
        """
        self.mode = mode
        self.hub_address = f"{HUB_IP}:{ADB_PORT}"

        self.serial = "cafe98eae8910ac4"


    def connect_to_hub(self):
        """
        Attempts to establish or verify the connection to the REV Control Hub.
        
        Returns:
            bool: True if the Hub is responsive and recognized as a 'device'.
        """
        if self.mode == "wifi":
            result = self._run_adb(["connect", self.hub_address])
            return "connected" in result.stdout.lower()
        else:
            # USB Mode: Parses the 'adb devices' list for an active hardware link
            result = self._run_adb(["devices"])
            lines = result.stdout.strip().splitlines()
            return any("device" in l and "List" not in l for l in lines)

    def _run_adb(self, args):
        """
        Modified helper to ensure we target the specific USB serial.
        Original: ['shell', 'ip', ...]
        New: ['-s', 'cafe98eae8910ac4', 'shell', 'ip', ...]
        """
        import subprocess
        full_cmd = ["adb", "-s", self.serial] + args
        
        # Use a timeout so the GUI doesn't hang if the USB is flaky
        return subprocess.run(
            full_cmd, 
            capture_output=True, 
            text=True, 
            timeout=5
        )

    def get_connected_devices(self):
        """
        Queries the Hub for active participants with a non-blocking discovery step.
        """
        try:
            # 1. Non-Blocking Discovery
            # We remove the timeout for this specific call or make it very short (1s)
            # and we don't check the result. We just fire it and move on.
            try:
                self._run_adb_quick(["shell", "ping", "-c", "1", "-b", "192.168.43.255"])
            except:
                pass # If broadcast ping is blocked, we don't want to crash

            # 2. Query Neighbor Table (The important part)
            # We give this a dedicated timeout and strict error checking
            result = self._run_adb(["shell", "ip", "neighbor", "show", "nud", "reachable"])
        
            if result.returncode != 0:
                return None 
            
            devices = []
            if result.stdout:
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) < 1: continue
                    
                    ip = parts[0]
                    if "192.168.43." in ip and ip != "192.168.43.1":
                        devices.append((ip, "ACTIVE"))
                        
            return devices

        except Exception as e:
            # This is likely where your 'ENGINE ERROR' was coming from
            print(f"[DEBUG] Hub polling failed: {e}")
            return None

    def _run_adb_quick(self, args):
        """A faster version of _run_adb that doesn't wait for a response."""
        full_cmd = ["adb", "-s", self.serial] + args
        return subprocess.run(full_cmd, capture_output=True, text=True, timeout=1.5)