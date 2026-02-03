import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


HOST = "localhost"
PORT = 8080


class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Chat App")

        self.username = None
        self.sock = socket.socket()

        # ---------- CONNECT TO SERVER ----------
        try:
            self.sock.connect((HOST, PORT))
        except Exception as e:
            self.fatal_error(f"Could not connect: {e}")
            return

        # ---------- ASK FOR USERNAME ----------
        self.username_window()

    # ---------------- USERNAME WINDOW -----------------
    def username_window(self):
        self.top = tk.Toplevel(self.master)
        self.top.title("Enter Username")
        self.top.geometry("300x150")
        self.top.grab_set()

        tk.Label(self.top, text="Choose a username:",
                 font=("Segoe UI", 12)).pack(pady=10)

        self.username_entry = ttk.Entry(self.top, font=("Segoe UI", 12))
        self.username_entry.pack(padx=20, pady=5)
        self.username_entry.bind("<Return>", self.submit_username)

        ttk.Button(self.top, text="Join", command=self.submit_username).pack(pady=10)

    def submit_username(self, event=None):
        name = self.username_entry.get().strip()
        if not name:
            return

        self.username = name
        self.top.destroy()

        # Wait for server's "USERNAME?" message
        self.sock.recv(1024)

        # Send username
        self.sock.send(self.username.encode())

        # Launch chat UI
        self.build_chat_ui()

        # Start listening
        threading.Thread(target=self.receive_messages, daemon=True).start()

    # ---------------- CHAT UI -----------------
    def build_chat_ui(self):
        self.master.geometry("600x600")
        self.master.configure(bg="#f1f3f6")

        # Header
        header = tk.Frame(self.master, bg="#4a90e2", height=60)
        header.pack(fill="x")
        tk.Label(header,
                 text=f"💬 Chat – {self.username}",
                 font=("Segoe UI", 20, "bold"),
                 fg="white",
                 bg="#4a90e2").pack(pady=10)

        # Chat box
        self.chat_box = ScrolledText(self.master,
                                     wrap=tk.WORD,
                                     font=("Segoe UI", 12),
                                     height=20,
                                     bg="white",
                                     relief="flat")
        self.chat_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.chat_box.config(state="disabled")

        # Message entry row
        bottom = tk.Frame(self.master, bg="#f1f3f6")
        bottom.pack(fill="x", padx=10, pady=10)

        self.entry = ttk.Entry(bottom)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        ttk.Button(bottom, text="➤ Send", command=self.send_message).pack(side="right")

    # ---------- Message Handling ----------
    def add_message(self, msg, tag="msg"):
        self.chat_box.config(state="normal")

        color = "#000000" if tag == "msg" else "#777777"
        self.chat_box.insert(tk.END, msg, (tag,))
        self.chat_box.tag_config(tag, foreground=color)

        self.chat_box.config(state="disabled")
        self.chat_box.yview(tk.END)

    def receive_messages(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                self.add_message(data)
            except:
                break

    def send_message(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            try:
                self.sock.send(msg.encode())
            except:
                self.add_message("[Failed to send message]\n", "system")
            self.entry.delete(0, tk.END)

    def fatal_error(self, message):
        tk.messagebox.showerror("Error", message)
        self.master.destroy()


def main():
    root = tk.Tk()
    ChatClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
