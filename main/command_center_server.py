"""
CommandCenterServer - Network Distribution & Alert Hub
This module implements a multi-threaded TCP server designed to receive, 
decrypt, and route security alerts from remote sensor nodes. 

It serves as the central processing unit for the Master node, ensuring 
data is simultaneously pushed to the GUI, local logs, the SQLite database, 
and mobile notifications via ntfy.sh.
"""

import socket
import threading
import time
from secure_socket import SecureSocket
from config import SECRET_KEY, SERVER_PORT


class CommandCenterServer:
    def __init__(self, gui, db_manager, logger, notifier):
        self.gui = gui
        self.db = db_manager
        self.logger = logger
        self.notifier = notifier

        # Centralized State: Source of Truth for all robots
        # { "ROBOT_ID": {"ip": str, "last_seen": float, "status": str} }
        self.active_nodes = {}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', SERVER_PORT))
        self.server_socket.listen(5)

        # Link the GUI to this server instance
        self.gui.set_server_reference(self)

    def start(self):
        """Starts the main server listener loop in a background thread."""
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        print(f"[*] Master Server listening on port {SERVER_PORT}...")
        while True:
            client_sock, addr = self.server_socket.accept()
            # Each connection gets a dedicated handler thread
            threading.Thread(target=self._handle_client, args=(
                client_sock, addr), daemon=True).start()

    def _handle_client(self, client_sock, addr):
        sender_ip = addr[0]

        try:
            # 1. Receive the raw encrypted bytes from the network
            # 1024 bytes is plenty for our small status strings
            encrypted_data = client_sock.recv(1024)

            if encrypted_data:
                # 2. Initialize your encryption tool with the key
                crypto = SecureSocket(key=SECRET_KEY)

                # 3. Decrypt the bytes into a string
                decrypted_data = crypto.decrypt_message(encrypted_data)

                # 4. Process as usual
                self._process_message(decrypted_data, sender_ip)

        except Exception as e:
            print(f"[SERVER ERROR] Failed to handle client {sender_ip}: {e}")
        finally:
            client_sock.close()

    

    def _process_message(self, decrypted_data, sender_ip):
        try:
            parts = decrypted_data.split(" | ")
            if len(parts) < 2: return
                
            robot_id = parts[0]
            content = parts[1]

            # --- 1. TRACKING LOGIC ---
            current_status = "Online"
            if "UNAUTHORIZED" in content:
                current_status = "Alerting"
            elif "Link Lost" in content:
                current_status = "Offline"

            # Store the data exactly how your GUI function wants it
            self.active_nodes[robot_id] = {
                "ip": sender_ip,
                "last_seen": time.time(), # Sending raw Unix timestamp
                "status": current_status
            }

            # Call YOUR specific GUI function
            self.gui._update_node_list_ui(self.active_nodes)

            # --- 2. MESSAGE ROUTING ---
            if "CONNECTED" in content and "UNAUTHORIZED" not in content:
                # ... (your existing handshake logic) ...
                self.gui.add_to_monitor(robot_id, "CONNECTED TO MASTER", "ACTIVE")
                
            else:
                status = "CRITICAL" if "UNAUTHORIZED" in content or "Link Lost" in content else "INFO"
                self._handle_security_event(robot_id, content, sender_ip, status)

        except Exception as e:
            print(f"[SERVER ERROR] Message processing failed: {e}")

    def _determine_status(self, content):
        if "UNAUTHORIZED" in content:
            return "CRITICAL"
        if "STALE" in content or "LOST" in content:
            return "STALE"
        return "ACTIVE"

    def _handle_security_event(self, robot_id, content, sender_ip, status):
        # 1. LOG CLEANUP: Use robot_id: content (Removes the @127.0.0.1)
        display_msg = f"{robot_id}: {content}"
        
        # 2. Update GUI
        self.gui.add_to_monitor(robot_id, content, status)

        # 3. Update Database & Text Logs
        # We use sender_ip here just to know which Robot reported it
        self.db.log_event(sender_ip, display_msg)
        self.logger.log(display_msg)

        # 4. NOTIFY (THE FIX)
        if status == "CRITICAL":
            # 'content' looks like "CONNECTED: 192.168.43.7 (UNAUTHORIZED)"
            # We need to extract that 192... address so your phone shows the RIGHT IP
            import re
            ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
            actual_intruder_ip = ip_match.group(0) if ip_match else "Unknown IP"

            # This will now send the ACTUAL intruder IP to your phone, not 127.0.0.1
            self.notifier.send_alert(
                f"SECURITY BREACH: {robot_id}", 
                f"Intruder Detected: {actual_intruder_ip}"
            )

    def get_active_nodes(self):
        return self.active_nodes
