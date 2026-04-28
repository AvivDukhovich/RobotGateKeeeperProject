import tkinter as tk
from tkinter import ttk, messagebox
import time

class IdsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RobotGateKeeper Command Center")
        self.server = None # Will be set by main.py
        
        # --- 1. THE DARK THEME SETUP ---
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e1e")
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#333333", foreground="white", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#4a4a4a")])
        style.configure("TFrame", background="#1e1e1e")
        
        # --- 2. CREATE THE NOTEBOOK ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Define the Frames
        self.tab_monitor = ttk.Frame(self.notebook)
        self.tab_hub = ttk.Frame(self.notebook)
        self.tab_logs = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_monitor, text="LIVE MONITOR")
        self.notebook.add(self.tab_hub, text="NETWORK HUB")
        self.notebook.add(self.tab_logs, text="SECURITY LOGS")
        
        # --- 3. RUN SETUP FOR EACH TAB ---
        self._setup_monitor_tab()
        self._setup_hub_tab()
        self._setup_logs_tab()

    def _setup_monitor_tab(self):
        tk.Label(self.tab_monitor, text="REAL-TIME SECURITY FEED", 
                 font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)
        
        # Added highlightthickness for the border
        self.monitor_log = tk.Text(self.tab_monitor, height=25, width=95, state='disabled',
                                   bg="#000000", fg="#d4d4d4", font=("Consolas", 10),
                                   borderwidth=0, 
                                   highlightthickness=2, 
                                   highlightbackground="#444444") # Medium gray border
        self.monitor_log.pack(padx=20, pady=10)
        
        self.monitor_log.tag_config("ACTIVE", foreground="#4ec9b0")
        self.monitor_log.tag_config("INFO", foreground="#85c1e9")
        self.monitor_log.tag_config("CRITICAL", foreground="#f44747", font=("Consolas", 10, "bold"))

    def _setup_hub_tab(self):
        tk.Label(self.tab_hub, text="MANAGED ROBOT NODES", 
                 font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)
        
        # Consistent styling: Pure black background and charcoal border
        self.node_listbox = tk.Listbox(
            self.tab_hub, 
            bg="#000000",        # Pure black to match other tabs
            fg="white", 
            font=("Consolas", 11), 
            borderwidth=0, 
            highlightthickness=2, 
            highlightbackground="#444444", # Matching border color
            selectbackground="#333333"     # Subtle gray when a node is clicked
        )
        # Using fill="both" and expand=True keeps the square consistent
        self.node_listbox.pack(expand=True, fill="both", padx=20, pady=20)
        self.node_listbox.bind('<Double-1>', self._on_node_select)

    def _setup_logs_tab(self):
        tk.Label(self.tab_logs, text="SECURITY EVENT ARCHIVE", 
                 font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)
        
        ttk.Button(self.tab_logs, text="Fetch History", command=self._fetch_db_history).pack(pady=5)
        
        # Matching border style here
        self.history_box = tk.Text(self.tab_logs, height=18, width=90, 
                                   bg="#000000", fg="#85c1e9", font=("Consolas", 9),
                                   borderwidth=0, 
                                   highlightthickness=2, 
                                   highlightbackground="#444444")
        self.history_box.pack(padx=20, pady=10)

    # --- UI UPDATE METHODS ---

    def _update_monitor_ui(self, robot_id, text, status):
        """Now correctly references self.monitor_log"""
        self.monitor_log.config(state='normal')
        ts = time.strftime('%H:%M:%S')
        # Use robot_id: text format we established
        self.monitor_log.insert(tk.END, f"[{ts}] {robot_id} | {text}\n", status)
        self.monitor_log.see(tk.END)
        self.monitor_log.config(state='disabled')

    def add_to_monitor(self, robot_id, text, status):
        self.root.after(0, self._update_monitor_ui, robot_id, text, status)

    def create_node_button(self, text):
        """Creates a styled button for the node list."""
        btn = tk.Button(self.node_listbox, text=text, 
                        bg="#000000", fg="white", font=("Consolas", 11), 
                        borderwidth=0, highlightthickness=0, anchor="w")
        self.node_listbox.insert(tk.END, text) # Add to Listbox
        return btn

    def _update_node_list_ui(self, nodes):
        """Updates the sidebar with clean 'PC X: ID: ROBOT_X' names."""
        # Clear existing list items in the GUI container
        # self.clear_node_list_container() 

        for robot_id, info in nodes.items():
            # Get the clean display string you requested
            display_text = f"{info['display_name']}: ID: {info['id']}"
            
            # Create the button/label in the GUI
            node_btn = self.create_node_button(display_text)
            
            # When clicked, show the DETAILED box with the IP and Timestamp
            node_btn.bind("<Button-1>", lambda e, r_id=robot_id: self.show_node_details(r_id))
            
    def _fetch_db_history(self):
        if self.server and self.server.db:
            events = self.server.db.query_logs(limit=20)
            self.history_box.delete('1.0', tk.END)
            for ts, mac, desc in events:
                self.history_box.insert(tk.END, f"[{ts}] {mac} | {desc}\n")

    def _on_node_select(self, event):
        selection = self.node_listbox.curselection()
        if selection:
            node_info = self.node_listbox.get(selection[0])
            messagebox.showinfo("Node Audit", f"Detailed status for selected unit:\n\n{node_info}")

    def set_server_reference(self, server_instance):
        self.server = server_instance