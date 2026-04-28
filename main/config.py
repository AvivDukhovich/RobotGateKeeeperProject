"""
RobotGateKeeper - Global Configuration
This module centralizes all environment-specific constants, paths, and 
cryptographic keys. Modifying these values allows for quick pivoting 
between different hardware setups or security parameters.
"""

import os

# ==========================================
# THE ONLY LINE YOU CHANGE ON EACH PC:
MY_IDENTITY = "ROBOT_1" 
# ==========================================

# --- DYNAMIC PATH CALCULATION ---
# Get the folder where config.py is (the 'main' folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# Path to ADB relative to this project's location
LOCAL_ADB_PATH = os.path.join(PROJECT_ROOT, "platform-tools", "adb.exe")

# --- GLOBAL CONSTANTS ---
HUB_IP = "192.168.43.1"
ADB_PORT = 5555
SERVER_PORT = 8989
SECRET_KEY = b'yx0k4DLySC4S0MHfAUVPQzNw3cQBspQ9R8mkZUSh7oQ='
LOG_FILE = "security_log.txt"

# --- NETWORK PERMISSIONS ---
ALLOWED_MACS = {
    "30:7b:c9:52:db:f4",    # The Control Hub
    "28:59:23:b6:9b:30",
    "192.168.9.19",  # PC #2
    "192.168.11.204",  # PC #1 (Master)
    "127.0.0.1"        # Localhost
}

# --- CONNECTION SETTINGS ---
# Set to "usb" for ADB-over-USB testing, or "wifi" for direct network monitoring
CONNECTION_MODE = "usb"

# The actual network IP of the Command Center (ROBOT_1)
# Secondary robots will use this to find the Master over Wi-Fi.
MASTER_NETWORK_IP = "192.168.11.204"

# --- SYSTEM LOGIC ---
ROBOT_ID = MY_IDENTITY

# Check if this specific node is the Master
IS_MASTER = (ROBOT_ID == "ROBOT_1")

# Use the dynamic path we calculated at the top
ADB_PATH = LOCAL_ADB_PATH

# Routing: Localhost if we are the Master, otherwise use the Master's network IP
COMMAND_CENTER_IP = "127.0.0.1" if IS_MASTER else MASTER_NETWORK_IP

# --- DEBUG PRINT (Optional) ---
# print(f"[*] Identity: {ROBOT_ID} | Master: {IS_MASTER} | ADB: {ADB_PATH}")