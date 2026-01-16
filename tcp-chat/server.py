import socket
import threading
from protocol import send_line, recv_line

HOST = "0.0.0.0"
PORT = 5000

clients_lock = threading.Lock()
clients = {}    # name -> socket
partners = {}   # name -> partner_name


def set_partner(a: str, b: str) -> None:
    partners[a] = b
    partners[b] = a


def end_chat_for(name: str, reason_to_name: str = "Chat ended", reason_to_partner: str = None) -> None:
    """
    Ends active chat for 'name' (if exists) and notifies both sides.
    Must be called while holding clients_lock.
    """
    partner = partners.get(name)
    if not partner:
        return

    a_sock = clients.get(name)
    b_sock = clients.get(partner)

    # Clear mappings
    partners.pop(name, None)
    partners.pop(partner, None)

    # Notify
    if a_sock:
        try:
            send_line(a_sock, f"SYS {reason_to_name}")
        except:
            pass

    if b_sock:
        msg = reason_to_partner if reason_to_partner is not None else f"{name} left the chat"
        try:
            send_line(b_sock, f"SYS {msg}")
        except:
            pass


def handle_client(conn: socket.socket, addr):
    name = None
    try:
        send_line(conn, "SYS Welcome. Identify with: HELLO <name>")
        first = recv_line(conn).strip()
        if not first.startswith("HELLO "):
            send_line(conn, "ERR Expected HELLO <name>")
            return

        name = first.split(" ", 1)[1].strip()
        if not name:
            send_line(conn, "ERR Empty name not allowed")
            return

        with clients_lock:
            if name in clients:
                send_line(conn, "ERR Name already in use")
                return
            clients[name] = conn

        send_line(conn, f"SYS Hello {name}. Commands: /chat <name>, /leave, /quit")
        print(f"[+] {name} connected from {addr}")

        while True:
            line = recv_line(conn).strip()
            if not line:
                continue

            # ===== Commands =====
            if line.startswith("/chat "):
                target = line.split(" ", 1)[1].strip()

                with clients_lock:
                    if target not in clients:
                        send_line(conn, f"ERR User '{target}' not connected")
                        continue
                    if target == name:
                        send_line(conn, "ERR Cannot chat with yourself")
                        continue

                    # ✅ target busy? do NOT cancel their chat
                    if target in partners:
                        send_line(conn, f"ERR User '{target}' is busy")
                        continue

                    # If I'm already in a chat, I can switch by my choice
                    if name in partners:
                        end_chat_for(
                            name,
                            reason_to_name="Switching chat",
                            reason_to_partner=f"{name} switched to another chat",
                        )

                    set_partner(name, target)
                    send_line(clients[name], f"SYS Chat opened with {target}")
                    send_line(clients[target], f"SYS Chat opened with {name}")
                continue

            if line == "/leave":
                with clients_lock:
                    if name not in partners:
                        send_line(conn, "ERR No active chat to leave")
                        continue
                    end_chat_for(name, reason_to_name="You left the chat")
                continue

            if line == "/quit":
                send_line(conn, "SYS Bye")
                return

            # ===== Normal message =====
            with clients_lock:
                partner = partners.get(name)
                if not partner:
                    send_line(conn, "ERR No active chat. Use /chat <name>")
                    continue

                partner_sock = clients.get(partner)

            if not partner_sock:
                # Partner disconnected unexpectedly
                with clients_lock:
                    end_chat_for(name, reason_to_name="Partner disconnected")
                continue

            # Relay message through the server
            try:
                send_line(partner_sock, f"FROM {name} {line}")
                send_line(conn, "SYS delivered")
            except Exception:
                # If sending failed, end chat
                with clients_lock:
                    end_chat_for(name, reason_to_name="Partner disconnected")
                continue

    except ConnectionError:
        print(f"[-] Client disconnected unexpectedly: {name} {addr}")
    except Exception as e:
        print(f"[!] Error with client {name} {addr}: {e}")
    finally:
        if name:
            with clients_lock:
                # End chat and notify partner if needed
                end_chat_for(name, reason_to_name="Disconnected", reason_to_partner=f"{name} disconnected")
                # Remove from clients
                if clients.get(name) is conn:
                    clients.pop(name, None)
        try:
            conn.close()
        except:
            pass


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(10)
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
