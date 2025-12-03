import socket

HOST = "192.168.9.239"
PORT = 8080

s = socket.socket()
s.connect((HOST, PORT))

while True:
    # Receive from server
    data = s.recv(1024).decode()
    if not data:
        break

    print("SERVER:", data)

    # If someone won, stop
    if "WINNER" in data:
        break

    # Ask user for guess
    guess = input("Your guess: ")
    s.sendall(guess.encode())