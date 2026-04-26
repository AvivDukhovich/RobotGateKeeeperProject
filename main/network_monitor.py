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

    def _run_adb(self, args):
        """
        Internal wrapper for subprocess to execute ADB commands.
        
        Args:
            args (list): The list of ADB arguments (e.g., ['shell', 'ls']).
            
        Returns:
            CompletedProcess: The result of the command execution.
        """
        cmd = [ADB_PATH]
        # In Wi-Fi mode, we must target a specific serial/IP via the -s flag
        if self.mode == "wifi":
            cmd += ["-s", self.hub_address]
        
        try:
            return subprocess.run(cmd + args, capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 1, "", "Timeout")

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

    def get_connected_devices(self):
        """
        Queries the Hub for currently active network participants.
        
        Logic:
        1. Broadcast Ping: Wakes up sleeping devices and forces an ARP refresh.
        2. Neighbor Show: Inspects the Hub's ARP table for 'REACHABLE' states.
        
        Returns:
            list: A list of tuples containing (IP_ADDRESS, "ACTIVE").
        """
        # 1. Force discovery: Pings the subnet broadcast to elicit responses from peers
        self._run_adb(["shell", "ping", "-c", "1", "-b", "192.168.43.255"])
        
        # 2. Query Neighbor Table: 
        # 'nud reachable' is used to filter out STALE, DELAY, or FAILED entries.
        result = self._run_adb(["shell", "ip", "neighbor", "show", "nud", "reachable"])
    
        # NEW: Check if ADB actually succeeded
        # If the cable is out, result.returncode will be non-zero
        if result.returncode != 0:
            raise ConnectionError("Control Hub is physically unreachable via ADB")
        
        devices = []
        if result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split()
                if not parts: continue
                
                ip = parts[0]
                # Filter to ensure we only care about devices on the Robot controller's subnet
                if "192.168.43." in ip and ip != "192.168.43.1":
                    devices.append((ip, "ACTIVE"))
                    
        return devices