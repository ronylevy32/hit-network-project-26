import socket

ENCODING = "utf-8"

def send_line(sock: socket.socket, line: str) -> None:
    data = (line + "\n").encode(ENCODING)
    sock.sendall(data)

def recv_line(sock: socket.socket) -> str:
    """
    קורא עד newline. פשוט ללמידה; מספיק לפרויקט.
    """
    buf = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            # חיבור נסגר
            raise ConnectionError("Socket closed")
        if chunk == b"\n":
            return buf.decode(ENCODING, errors="replace")
        buf.extend(chunk)
