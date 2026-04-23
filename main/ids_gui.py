"""
SecurityGUI - The IDS Command Center
This module provides a real-time graphical user interface for the RobotGateKeeper.
It utilizes a multi-threaded approach to host a local secure socket server that
listens for encrypted alerts from the monitoring service (ids_engine) and displays them
with color-coded priority levels.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time


class IdsGUI:
    def __init__(self, root):
        self.root = root
        self.server = None  # Will be set by CommandCenterServer
        self.root.title("Aegis-FTC | Secure Command Center")
        self.root.geometry("900x650")

        # Setup Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        self.screen_monitor = ttk.Frame(self.notebook)
        self.screen_network = ttk.Frame(self.notebook)
        self.screen_history = ttk.Frame(self.notebook)

        self.notebook.add(self.screen_monitor, text="  LIVE MONITOR  ")
        self.notebook.add(self.screen_network, text="  NETWORK HUB  ")
        self.notebook.add(self.screen_history, text="  SECURITY LOGS  ")

        self._setup_monitor_screen()
        self._setup_network_screen()
        self._setup_history_screen()

    def set_server_reference(self, server_instance):
        self.server = server_instance

    def _setup_monitor_screen(self):
        tk.Label(self.screen_monitor, text="REAL-TIME SECURITY FEED",
                 font=("Arial", 14, "bold")).pack(pady=10)
        self.monitor_log = tk.Text(self.screen_monitor, height=25, width=95, state='disabled',
                                   bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.monitor_log.pack(padx=20, pady=10)

        # Tags for severity colors
        self.monitor_log.tag_config("ACTIVE", foreground="#4ec9b0")
        self.monitor_log.tag_config("STALE", foreground="#ce9178")
        self.monitor_log.tag_config(
            "CRITICAL", foreground="#f44747", font=("Consolas", 10, "bold"))

    def _setup_network_screen(self):
        tk.Label(self.screen_network, text="MANAGED ROBOT NODES",
                 font=("Arial", 14, "bold")).pack(pady=10)

        btn_frame = ttk.Frame(self.screen_network)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Manual Refresh",
                   command=self._manual_refresh).grid(row=0, column=0, padx=5)

        self.node_listbox = tk.Listbox(
            self.screen_network, bg="#1e1e1e", fg="white", width=70, height=15, font=("Arial", 11))
        self.node_listbox.pack(pady=10)
        self.node_listbox.bind('<Double-1>', self._on_node_select)

    def _setup_history_screen(self):
        tk.Label(self.screen_history, text="SECURITY EVENT ARCHIVE",
                 font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Button(self.screen_history, text="Fetch History",
                   command=self._fetch_db_history).pack(pady=5)
        self.history_box = tk.Text(self.screen_history, height=18,
                                   width=90, bg="#1e1e1e", fg="#85c1e9", font=("Consolas", 9))
        self.history_box.pack(padx=20, pady=10)

    # --- Communication Methods (Called by Server) ---

    def add_to_monitor(self, robot_id, text, status):
        """Directly adds security events to the live monitor."""
        self.root.after(0, self._update_monitor_ui, robot_id, text, status)

    def _update_monitor_ui(self, robot_id, text, status):
        self.monitor_log.config(state='normal')
        ts = time.strftime('%H:%M:%S')
        self.monitor_log.insert(
            tk.END, f"[{ts}] {robot_id} | {text}\n", status)
        self.monitor_log.see(tk.END)
        self.monitor_log.config(state='disabled')

    def refresh_network_hub(self, active_nodes):
        """Updates the interactive node list using the server's source of truth."""
        self.root.after(0, self._update_node_list_ui, active_nodes)

    def _update_node_list_ui(self, nodes):
        self.node_listbox.delete(0, tk.END)
        for rid, data in nodes.items():
            ts = time.strftime('%H:%M:%S', time.localtime(data['last_seen']))
            self.node_listbox.insert(
                tk.END, f" {rid} | IP: {data['ip']} | Last: {ts} | [{data['status']}]")

    # --- Interactive Features ---

    def _on_node_select(self, event):
        selection = self.node_listbox.curselection()
        if selection:
            node_info = self.node_listbox.get(selection[0])
            messagebox.showinfo(
                "Node Audit", f"Detailed status for selected unit:\n\n{node_info}")

    def _manual_refresh(self):
        if self.server:
            self.refresh_network_hub(self.server.get_active_nodes())

    def _fetch_db_history(self):
        if self.server and self.server.db:
            events = self.server.db.query_logs(limit=20)
            self.history_box.delete('1.0', tk.END)
            for e in events:
                self.history_box.insert(tk.END, f"{e}\n")
