import socket
import threading
import random

HOST = "localhost"
PORT = 8080

random_num = random.randint(1, 1000)
winner_found = False

clients = []
lock = threading.Lock()  # protects winner_found

def broadcast(message):
    """Send a message to all connected players."""
    for c in clients:
        try:
            c.send(message.encode())
        except:
            pass

def handle_client(conn, addr):
    global winner_found

    print(f"[+] New connection: {addr}")
    conn.send(b"Welcome! What's your guess?\n")

    while True:
        if winner_found:
            break

        data = conn.recv(1024)
        if not data:
            break

        try:
            guess = int(data.decode().strip())
        except:
            conn.send(b"Please send a number.\n")
            continue

        # Game logic
        if guess > random_num:
            conn.send(b"Lower\n")
        elif guess < random_num:
            conn.send(b"Higher\n")
        else:
            with lock:
                if not winner_found:
                    winner_found = True
                    conn.send(b"You guessed right! YOU WIN!\n")
                    broadcast(f"Player {addr} has WON!\n")
            break

    conn.close()
    with lock:
        if conn in clients:
            clients.remove(conn)
    print(f"[-] Connection closed: {addr}")


def main():
    global winner_found

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()

    print(f"[+] Server running on {HOST}:{PORT}")
    print("[Debug] Winning number:", random_num)

    while True:
        if winner_found:
            break
        s.settimeout(1.0)  # wait for connection with timeout
        try:
            conn, addr = s.accept()
        except socket.timeout:
            continue

        with lock:
            clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()

    s.close()
    print("Game over. Server shutting down.")


if __name__ == "__main__":
    main()
