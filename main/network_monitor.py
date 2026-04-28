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
from config import LOCAL_ADB_PATH, HUB_IP, ADB_PORT

class NetworkMonitor:
    def __init__(self, mode="usb"):
        """
        Initializes the monitor with a specific connection strategy.
        
        Args:
            mode (str): 'usb' for direct tethering, 'wifi' for remote monitoring.
        """
        self.mode = mode
        self.hub_address = f"{HUB_IP}:{ADB_PORT}"
        self.adb_path = LOCAL_ADB_PATH



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

    def _run_adb(self, args, timeout=5):
        """Standard helper to run ADB commands using the local path."""
        full_cmd = [self.adb_path] + args
        try:
            # We return the actual result object if it works
            return subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            # Print the error so you know WHY it failed
            label = "TIMEOUT" if isinstance(e, subprocess.TimeoutExpired) else "MISSING EXE"
            print(f"[!] ADB {label}: {e}")
            return None

    def get_connected_devices(self):
        """Source of truth for the engine."""
        # 1. Run the command
        result = self._run_adb(["shell", "ip", "neighbor", "show", "nud", "reachable"])
        
        # 2. Handle the "None" case immediately
        if result is None or result.returncode != 0:
            return None
        
        # 3. Process stdout safely
        devices = []
        seen_macs = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            if parts:
                ip = parts[0]
                mac = parts[4] if len(parts) > 4 else "UNKNOWN"
                device = {
                    "ip": ip,
                    "mac": mac,
                    "status": "ACTIVE"
                }
                # if "192.168.43." in ip and ip != "192.168.43.1":
                if mac not in seen_macs:
                    seen_macs.add(mac)
                    devices.append(device)
        
        return devices