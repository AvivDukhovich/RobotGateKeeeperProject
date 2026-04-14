"""
NetworkMonitor - REV Control Hub Interface
This module handles communication with the REV Control Hub via Android Debug Bridge (ADB).
It provides methods to establish connections and query the ARP table for active network neighbors.
"""

import subprocess
from config import ADB_PATH, HUB_IP, ADB_PORT


class NetworkMonitor:
    def __init__(self):
        """
        Initializes the monitor with the target Hub address.
        """
        self.hub_address = f"{HUB_IP}:{ADB_PORT}"

    def _run_adb(self, args):
        """
        Internal helper to execute ADB commands using subprocess.

        Args:
            args (list): List of command arguments to pass to ADB.

        Returns:
            CompletedProcess: The result of the command execution.
        """
        try:
            return subprocess.run(
                [ADB_PATH] + args,
                capture_output=True,
                text=True,
                timeout=5  # Short timeout to keep the UI responsive
            )
        except subprocess.TimeoutExpired:
            print(f"ADB command timed out! Failed on: {args}")
            return subprocess.CompletedProcess(args, 1, "", "Timeout")

    def connect_to_hub(self):
        """
        Establishes a TCP/IP connection to the REV Control Hub over the network.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        print(f"Connecting to REV Control Hub at {self.hub_address}...")
        result = self._run_adb(["connect", self.hub_address])
        print(result.stdout.strip())
        # Connection is successful if 'already connected' or 'connected to' is in stdout
        return "connected" in result.stdout.lower()

    def get_connected_devices(self):
        """
        Queries the Hub's neighbor table (ARP cache) for active devices.
        Uses NUD (Neighbor Unreachability Detection) to filter out disconnected devices.

        Returns:
            list: A list of tuples containing (ip_address, status).
        """
        # 'nud reachable' tells the kernel to only return devices confirmed to be active
        result = self._run_adb(
            ["-s", self.hub_address, "shell", "ip", "neighbor", "show", "nud", "reachable"])
        devices = []

        if not result.stdout:
            return devices

        for line in result.stdout.splitlines():
            # Filter specifically for the robot's subnet
            if "192.168.43." in line:
                parts = line.split()
                if len(parts) > 0:
                    ip = parts[0]
                    # Since we use 'nud reachable', we classify these as ACTIVE
                    devices.append((ip, "ACTIVE"))

        return devices
