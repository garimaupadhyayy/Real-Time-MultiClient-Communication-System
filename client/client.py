import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import datetime

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9090

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.sock = None
        self.username = ""
        self.running = False

        self.root.title("Simple Chat App")
        self.root.geometry("700x600")       # bigger window
        self.root.configure(bg="#2b2b2b")
        self.root.resizable(True, True)     # resizable ON

        self._build_ui()

    def _build_ui(self):
        title = tk.Label(self.root, text="💬 Simple Chat",
                         font=("Arial", 14, "bold"),
                         bg="#1e1e1e", fg="white", pady=8)
        title.pack(fill="x")

        self.chat_area = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word",
            bg="#1e1e1e", fg="#e0e0e0", font=("Consolas", 11),
            relief="flat", padx=10, pady=8)
        self.chat_area.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        self.chat_area.tag_config("system", foreground="#888888")
        self.chat_area.tag_config("private", foreground="#f9e87f")
        self.chat_area.tag_config("normal", foreground="#e0e0e0")
        self.chat_area.tag_config("error", foreground="#ff6b6b")

        # ── username + connect row ────────────────────────────────────────
        conn_row = tk.Frame(self.root, bg="#2b2b2b")
        conn_row.pack(fill="x", padx=8, pady=8)

        tk.Label(conn_row, text="Username:", bg="#2b2b2b",
                 fg="#aaaaaa", font=("Arial", 11)).pack(side="left")

        self.user_entry = tk.Entry(conn_row, width=16, font=("Consolas", 11),
                                   bg="#3c3c3c", fg="white",
                                   insertbackground="white", relief="flat")
        self.user_entry.pack(side="left", padx=6, ipady=5)
        self.user_entry.bind("<Return>", self._connect)

        self.conn_btn = tk.Button(conn_row, text="Connect",
                                  bg="#43b581", fg="white",
                                  font=("Arial", 11, "bold"),
                                  relief="flat", padx=14, pady=5,
                                  command=self._connect)
        self.conn_btn.pack(side="left", padx=4)

        self.disc_btn = tk.Button(conn_row, text="Disconnect",
                                  bg="#f04747", fg="white",
                                  font=("Arial", 11, "bold"),
                                  relief="flat", padx=14, pady=5,
                                  state="disabled",
                                  command=self._disconnect)
        self.disc_btn.pack(side="left", padx=4)

        # ── message input row ─────────────────────────────────────────────
        bottom = tk.Frame(self.root, bg="#2b2b2b")
        bottom.pack(fill="x", padx=8, pady=(0, 10))

        self.msg_entry = tk.Entry(bottom, font=("Consolas", 11),
                                  bg="#3c3c3c", fg="white",
                                  insertbackground="white", relief="flat")
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 6))
        self.msg_entry.bind("<Return>", self._send)
        self.msg_entry.config(state="disabled")

        self.send_btn = tk.Button(bottom, text="Send",
                                  bg="#5865f2", fg="white",
                                  font=("Arial", 11, "bold"),
                                  relief="flat", padx=16, pady=7,
                                  command=self._send)
        self.send_btn.pack(side="right")
        self.send_btn.config(state="disabled")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _connect(self, event=None):
        username = self.user_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Enter a username first.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.running = True
            self.username = username

            t = threading.Thread(target=self._receive_loop, daemon=True)
            t.start()

            self.conn_btn.config(state="disabled")
            self.disc_btn.config(state="normal")
            self.msg_entry.config(state="normal")
            self.send_btn.config(state="normal")
            self.user_entry.config(state="disabled")
            self.msg_entry.focus()

        except ConnectionRefusedError:
            messagebox.showerror("Error", "Cannot connect!\nIs server.py running?")

    def _receive_loop(self):
        buffer = ""
        self.sock.sendall((self.username + "\n").encode())

        while self.running:
            try:
                chunk = self.sock.recv(1024).decode(errors="ignore")
                if not chunk:
                    break
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._show_message(line)
            except:
                break

        self.running = False
        self._show_message("*** Disconnected from server ***", tag="error")
        self.root.after(0, self._reset_ui)

    def _send(self, event=None):
        text = self.msg_entry.get().strip()
        if not text or not self.running:
            return

        if not text.startswith("/"):
            ts = datetime.datetime.now().strftime("%H:%M")
            self._show_message(f"[{ts}] You: {text}", tag="normal")

        self.sock.sendall((text + "\n").encode())
        self.msg_entry.delete(0, "end")

    def _show_message(self, text, tag=None):
        if tag is None:
            if text.startswith("***"):
                tag = "system"
            elif "[PM" in text:
                tag = "private"
            elif text.startswith("ERROR"):
                tag = "error"
            else:
                tag = "normal"

        def do_insert():
            self.chat_area.config(state="normal")
            self.chat_area.insert("end", text + "\n", tag)
            self.chat_area.config(state="disabled")
            self.chat_area.see("end")

        self.root.after(0, do_insert)

    def _disconnect(self):
        self.running = False
        try:
            self.sock.sendall("/quit\n".encode())
            self.sock.close()
        except:
            pass
        self._reset_ui()

    def _reset_ui(self):
        self.conn_btn.config(state="normal")
        self.disc_btn.config(state="disabled")
        self.msg_entry.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.user_entry.config(state="normal")

    def _on_close(self):
        self._disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()