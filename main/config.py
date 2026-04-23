"""
RobotGateKeeper - Global Configuration
This module centralizes all environment-specific constants, paths, and 
cryptographic keys. Modifying these values allows for quick pivoting 
between different hardware setups or security parameters.
"""

# ==========================================
# THE ONLY LINE YOU CHANGE ON EACH PC:
MY_IDENTITY = "ROBOT_1"
# ==========================================

# Global Constants (Standard for FTC/Barnyard hardware)
HUB_IP = "192.168.43.1"
ADB_PORT = 5555
SERVER_PORT = 8989
SECRET_KEY = b'yx0k4DLySC4S0MHfAUVPQzNw3cQBspQ9R8mkZUSh7oQ='
LOG_FILE = "security_log.txt"

# Network Permissions
# Add the IPs of all "friendly" devices (Hub, PCs, Phones, Driver Station)
ALLOWED_IPS = {
    "192.168.43.1",    # The Control Hub
    "192.168.11.105",   # PC #2
    "192.168.11.226",    # PC #1
    "127.0.0.1"        # Localhost
}

# The WiFi 2 IP of PC1 (Command Center)
MASTER_NETWORK_IP = "192.168.11.226"

# Configuration Mapping for Machine-Specific Paths
ROBOT_CONFIGS = {
    "ROBOT_1": {
        "master": True,
        "adb": r"D:\AACoding\school\scapyShit\RobotGateKeeeperProject\platform-tools\adb.exe"
    },
    "ROBOT_2": {
        "master": False,
        "adb": r"C:\Users\Barnyard\Documents\working\Aviv shi\RobotGateKeeeperProject\platform-tools\adb.exe"
    },
    "ROBOT_3": {
        "master": False,
        "adb": r"D:\ADB\platform-tools\adb.exe"
    }
}

# --- Automatic Logic ---
ROBOT_ID = MY_IDENTITY
IS_MASTER = ROBOT_CONFIGS[MY_IDENTITY]["master"]
ADB_PATH = ROBOT_CONFIGS[MY_IDENTITY]["adb"]

# Routing: Local vs Remote
COMMAND_CENTER_IP = "127.0.0.1" if IS_MASTER else MASTER_NETWORK_IP
