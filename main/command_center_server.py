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
import re
from datetime import datetime, timezone, timedelta
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
        self.connection_counter = 0

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', SERVER_PORT))
        self.server_socket.listen(5)

        # Link the GUI to this server instance
        self.gui.set_server_reference(self)

    def _get_israel_time_str(self):
        """Helper to get a perfectly formatted timestamp forced to Israel Time (UTC+3)"""
        israel_tz = timezone(timedelta(hours=3))
        return datetime.now(israel_tz).strftime("[%Y-%m-%d %H:%M:%S]")

    def register_node(self, robot_id, data):
        if robot_id not in self.active_nodes:
            self.connection_counter += 1
            israel_time = timezone(timedelta(hours=3))
            self.active_nodes[robot_id] = {
                "display_name": f"PC {self.connection_counter}",
                "id": robot_id,
                "ip": data['ip'],
                "last_seen": datetime.now(israel_time).strftime("%H:%M:%S")
            }

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
            # 1. TRIPLE SPLIT: ROBOT_ID | IP:xxx | MESSAGE
            parts = decrypted_data.split(" | ")
            
            if len(parts) < 3:
                robot_id = parts[0]
                reported_ip = sender_ip
                content = parts[1] if len(parts) > 1 else ""
            else:
                robot_id = parts[0]
                reported_ip = parts[1].replace("IP:", "")
                content = parts[2]

            # 2. ASSIGN / RETRIEVE PC NAME
            if robot_id not in self.active_nodes:
                self.connection_counter += 1
                display_name = f"PC {self.connection_counter}"
            else:
                display_name = self.active_nodes[robot_id].get("display_name", "Unknown PC")

            # 3. DETERMINE STATUS
            msg_upper = content.upper()
            is_intruder = "UNAUTHORIZED" in msg_upper or "INTRUDER" in msg_upper
            is_lost = "LINK LOST" in msg_upper or "OFFLINE" in msg_upper
            
            current_status = "Online"
            if is_intruder:
                current_status = "Alerting"
            elif is_lost:
                current_status = "Offline"

            # 4. UPDATE STATE (Forced to current accurate epoch time)
            self.active_nodes[robot_id] = {
                "display_name": display_name,
                "id": robot_id,
                "ip": reported_ip,
                "last_seen": time.time(),
                "status": current_status
            }

            # Refresh GUI Sidebar
            self.gui._update_node_list_ui(self.active_nodes)

            # 5. MESSAGE ROUTING
            if "CONNECTED" in msg_upper and not is_intruder:
                self.gui.add_to_monitor(display_name, "ESTABLISHED LINK", "ACTIVE")
            else:
                status_level = "CRITICAL" if (is_intruder or is_lost) else "INFO"
                self._handle_security_event(robot_id, content, reported_ip, status_level)

        except Exception as e:
            print(f"[SERVER ERROR] Message processing failed: {e}")

    def _determine_status(self, content):
        if "UNAUTHORIZED" in content:
            return "CRITICAL"
        if "STALE" in content or "LOST" in content:
            return "STALE"
        return "ACTIVE"

    def _handle_security_event(self, robot_id, content, sender_ip, status):
        # Generate the live Israel Timestamp
        time_stamp = self._get_israel_time_str()

        # 1. LOG CLEANUP (Prepend the precise Israel Time)
        name = self.active_nodes[robot_id]["display_name"]
        display_msg = f"{time_stamp} {name} ({robot_id}): {content}"    
        
        # 2. Update GUI
        self.gui.add_to_monitor(robot_id, content, status)

        # 3. Update Database & Text Logs with explicit Israel Time
        self.db.log_event(sender_ip, display_msg)
        self.logger.log(display_msg)

        # 4. NOTIFY
        if status == "CRITICAL":
            ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
            actual_intruder_ip = ip_match.group(0) if ip_match else "Unknown IP"

            self.notifier.send_alert(
                f"SECURITY BREACH: {robot_id}", 
                f"Time: {time_stamp} | Intruder: {actual_intruder_ip}"
            )

    def get_active_nodes(self):
        return self.active_nodes