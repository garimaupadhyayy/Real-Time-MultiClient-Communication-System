"""
Simple Chat Server
"""

import socket
import threading
import datetime
import os

HOST = "127.0.0.1"
PORT = 9090

clients = {}
lock = threading.Lock()

os.makedirs("logs", exist_ok=True)
LOG_FILE = open("logs/chat.log", "a", encoding="utf-8")

def log(text):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {text}"
    print(line)
    LOG_FILE.write(line + "\n")
    LOG_FILE.flush()

def send_to(sock, message):
    try:
        sock.sendall((message + "\n").encode())
    except:
        pass

def broadcast(message, exclude=None):
    with lock:
        for uname, sock in clients.items():
            if uname != exclude:
                send_to(sock, message)

def handle_client(conn, addr):
    username = ""
    try:
        send_to(conn, "Enter your username: ")
        username = conn.recv(1024).decode().strip()

        with lock:
            if username in clients:
                send_to(conn, "ERROR: Username already taken. Bye!")
                conn.close()
                return
            clients[username] = conn

        log(f"{username} joined from {addr[0]}")
        send_to(conn, f"Welcome {username}! Type /msg <user> <text> for private message.")
        broadcast(f"*** {username} joined the chat ***", exclude=username)

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            if data.startswith("/msg "):
                parts = data.split(" ", 2)
                if len(parts) < 3:
                    send_to(conn, "Usage: /msg <username> <message>")
                    continue
                target = parts[1]
                text = parts[2]
                with lock:
                    target_sock = clients.get(target)
                if target_sock:
                    ts = datetime.datetime.now().strftime("%H:%M")
                    send_to(target_sock, f"[{ts}] [PM from {username}]: {text}")
                    send_to(conn, f"[{ts}] [PM to {target}]: {text}")
                    log(f"PM: {username} -> {target}: {text}")
                else:
                    send_to(conn, f"User '{target}' not found or offline.")

            elif data == "/users":
                with lock:
                    user_list = ", ".join(clients.keys())
                send_to(conn, f"Online users: {user_list}")

            elif data == "/help":
                send_to(conn, "Commands: /msg <user> <text>  |  /users  |  /help  |  /quit")

            elif data == "/quit":
                break

            else:
                ts = datetime.datetime.now().strftime("%H:%M")
                msg = f"[{ts}] {username}: {data}"
                broadcast(msg, exclude=username)
                log(f"GROUP: {username}: {data}")

    except (ConnectionResetError, BrokenPipeError):
        pass

    finally:
        with lock:
            clients.pop(username, None)
        if username:
            broadcast(f"*** {username} left the chat ***")
            log(f"{username} disconnected")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    log(f"Server started on {HOST}:{PORT}")
    print(f"Waiting for clients... (Ctrl+C to stop)\n")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()