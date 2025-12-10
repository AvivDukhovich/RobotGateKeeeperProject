import socket
import threading

HOST = "localhost"
PORT = 8080

def receive_messages(sock):
    """Receive and print all messages from the server."""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                print("\n[Server disconnected]")
                break

            print("\n" + data)  # always print messages on a new line

        except:
            break

def main():
    s = socket.socket()
    s.connect((HOST, PORT))

    # Start receiver thread
    threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

    # Only SEND — never print here
    while True:
        try:
            guess = input()     # no prompt text here
            s.send(guess.encode())
        except:
            break

    s.close()

if __name__ == "__main__":
    main()
