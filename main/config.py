"""
RobotGateKeeper - Global Configuration
This module centralizes all environment-specific constants, paths, and 
cryptographic keys. Modifying these values allows for quick pivoting 
between different hardware setups or security parameters.
"""

# ROBOT identifier (change to 2/3/etc depending on the pc)
ROBOT_ID = "ROBOT_1"

# Path to the Android Debug Bridge (ADB) executable used to interface with the Hub
ADB_PATH = r"C:\Users\PMW\Documents\Tracker\experiments\RobotGateKeeeperProject\platform-tools\adb.exe"

# Network identity of the REV Control Hub
HUB_IP = "192.168.43.1"
ADB_PORT = 5555

# GUI_SERVER_IP
COMMAND_CENTER_IP = "127.0.0.1"

# Storage location for intrusion detection history and system events
LOG_FILE = "security_log.txt"

# AES-256 Fernet key used by SecureSocket for encrypting inter-process communication
# This ensures that alerts sent from the monitor to the GUI cannot be intercepted locally.
SECRET_KEY = b'yx0k4DLySC4S0MHfAUVPQzNw3cQBspQ9R8mkZUSh7oQ='

# Dedicated TCP port for the local socket server (Monitor-to-GUI communication)
SERVER_PORT = 8989

ALLOWED_IPS = {"192.168.43.1", "192.168.43.104"}