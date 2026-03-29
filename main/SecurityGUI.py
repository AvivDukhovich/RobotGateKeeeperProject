import socket
import threading
import time
import tkinter as tk
from SecureSocket import SecureSocket # Your class from before

class SecurityGUI:
    def __init__(self, root):
        self.root = root  # <--- CRITICAL: This line must exist!
        self.root.title("Aegis-FTC Command Center")
        
        # UI Setup
        tk.Label(self.root, text="Live Network Monitor", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.monitor_log = tk.Text(self.root, height=15, width=60, state='disabled', bg="black", fg="white")
        self.monitor_log.pack(padx=10, pady=10)
        
        # Define colors for our tags
        self.monitor_log.tag_config("ACTIVE", foreground="lime")
        self.monitor_log.tag_config("STALE", foreground="orange")
        self.monitor_log.tag_config("UNAUTH", foreground="red", font=("Arial", 10, "bold"))
        
        # Start the background network thread
        self.start_network_thread()

    def update_status(self, text):
        self.monitor_log.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {text}\n"
        
        # Determine which color tag to use
        tag = None
        if "UNAUTHORIZED" in text:
            tag = "UNAUTH"
        elif "[ACTIVE]" in text:
            tag = "ACTIVE"
        elif "[STALE]" in text:
            tag = "STALE"
            
        self.monitor_log.insert(tk.END, full_message, tag)
        self.monitor_log.see(tk.END)
        self.monitor_log.config(state='disabled')

    def start_network_thread(self):
        # Requirement: Usage of Threads
        # target=self.run_server means "run this function in the background"
        # daemon=True means "kill this thread when the window closes"
        net_thread = threading.Thread(target=self.run_server, daemon=True)
        net_thread.start()

    def run_server(self):
        from config import SECRET_KEY, SERVER_PORT
        import socket
        
        sec = SecureSocket(key=SECRET_KEY)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('127.0.0.1', SERVER_PORT))
            server.listen(5)
            print(f"[*] GUI Server listening on port {SERVER_PORT}")
        except Exception as e:
            print(f"Bind Error: {e}")
            return

        while True:
            try:
                client, addr = server.accept()
                data = client.recv(4096)
                if data:
                    message = sec.decrypt_message(data)                    
                    # Schedule the update on the Main Thread
                    # This is how the background thread talks to the UI thread
                    self.root.after(0, self.update_status, message)
                client.close()
            except Exception as e:
                print(f"Server Loop Error: {e}")

# --- Launching the App ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityGUI(root)
    root.mainloop() # The Main Thread stays here