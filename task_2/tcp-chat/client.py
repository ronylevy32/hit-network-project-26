import socket
import threading
import sys
from protocol import send_line, recv_line

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


def receiver(sock: socket.socket):
    try:
        while True:
            line = recv_line(sock)
            print(line)
    except Exception:
        print("SYS Disconnected from server.")
        try:
            sock.close()
        except:
            pass
        sys.exit(0)


def main():
    name = input("Enter your name: ").strip()
    if not name:
        print("Name is required.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))

    t = threading.Thread(target=receiver, args=(sock,), daemon=True)
    t.start()

    send_line(sock, f"HELLO {name}")

    try:
        while True:
            msg = input()
            send_line(sock, msg)
            if msg == "/quit":
                break
    except KeyboardInterrupt:
        send_line(sock, "/quit")
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    main()
