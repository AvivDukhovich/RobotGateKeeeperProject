import socket
import threading

HOST = "localhost"
PORT = 8080

clients = []
usernames = {}
lock = threading.Lock()


def broadcast(message, _from=None):
    """Send message to all connected clients."""
    for c in clients:
        if c != _from:   # don't echo to sender
            try:
                c.send(message.encode())
            except:
                pass


def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")

    # Step 1: Receive username
    conn.send("USERNAME?\n".encode())
    username = conn.recv(1024).decode().strip()
    usernames[conn] = username

    with lock:
        clients.append(conn)

    broadcast(f"📢 {username} joined the chat!\n")

    # Step 2: Listen for messages
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break

            text = msg.decode().strip()
            broadcast(f"{username}: {text}\n", _from=conn)

        except:
            break

    # Disconnect cleanup
    with lock:
        clients.remove(conn)
    broadcast(f"❌ {username} left the chat.\n")
    conn.close()
    print(f"[-] Client disconnected: {addr}")


def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[+] Chat server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
