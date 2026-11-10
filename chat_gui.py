import socket
import threading
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, PhotoImage
from utils import (
    caesar_encrypt, xor_encrypt, fernet_encrypt,
    caesar_decrypt, xor_decrypt, fernet_decrypt,
    encrypt_image, decrypt_image, load_key
)
from PIL import Image, ImageTk

HOST = '127.0.0.1'
PORT = 12345

# ─── Color Palette (Light) ────────────────────────────────────────────────────
BG           = "#f8fafc"
BG2          = "#ffffff"
BG3          = "#f1f5f9"
ACCENT       = "#2563eb"
ACCENT_HOVER = "#1d4ed8"   # hover tombol
ACCENT2      = "#047857"
ACCENT3      = "#a21caf"   # ungu (XOR, label gambar)
ON_ACCENT    = "#ffffff"   # teks di atas tombol ACCENT
MUTED        = "#64748b"
TEXT         = "#0f172a"
TEXT2        = "#475569"
DANGER       = "#dc2626"
SENT_BG      = "#dbeafe"
RECV_BG      = "#dcfce7"
SYSTEM       = "#fef3c7"
BORDER       = "#cbd5e1"
SELECT_BG    = "#bfdbfe"   # latar teks yang diblok

FONT_MONO  = ("Consolas", 11)
FONT_UI    = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI Semibold", 13)
FONT_BADGE = ("Consolas", 9)


BASE_RECEIVED_FOLDER = "received"

def generate_user_folder(owner, sender):
    folder_path = os.path.join(BASE_RECEIVED_FOLDER, owner, sender)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def generate_image_filename(owner, sender):
    folder = generate_user_folder(owner, sender)
    index = 1
    while True:
        full_path = os.path.join(folder, f"received_{sender}_{index}.png")
        if not os.path.exists(full_path):
            return full_path
        index += 1
        
class LoginWindow:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login
        self.root.title("SecureChat — Login")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self._center(480, 640)
        self._build()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        pad = dict(padx=32, pady=0)

        # Header
        header = tk.Frame(self.root, bg=BG2, pady=20)
        header.pack(fill="x")
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((170, 170), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(logo)
        tk.Label(header, image=self.logo_img, bg=BG2).pack()
        tk.Label(header, text="SecureChat", font=("Segoe UI Semibold", 18),
                 bg=BG2, fg=TEXT).pack(pady=(2, 2))
        tk.Label(header, text="End-to-end encrypted messaging",
                 font=FONT_SMALL, bg=BG2, fg=TEXT2).pack()

        body = tk.Frame(self.root, bg=BG, pady=24)
        body.pack(fill="both", expand=True)

        # Username
        tk.Label(body, text="USERNAME", font=FONT_BADGE, bg=BG,
                 fg=TEXT2).pack(anchor="w", **pad)
        self.user_var = tk.StringVar()
        user_frame = tk.Frame(body, bg=BORDER)
        user_frame.pack(fill="x", padx=32, pady=(4, 16))
        inner = tk.Frame(user_frame, bg=BG3)
        inner.pack(fill="x", padx=1, pady=1)
        self.user_entry = tk.Entry(inner, textvariable=self.user_var,
                                   font=FONT_UI, bg=BG3, fg=TEXT,
                                   insertbackground=ACCENT, relief="flat")
        self.user_entry.pack(fill="x", padx=12, ipady=10)

        # Password
        tk.Label(body, text="PASSWORD", font=FONT_BADGE, bg=BG,
                 fg=TEXT2).pack(anchor="w", **pad)
        self.pass_var = tk.StringVar()
        pass_frame = tk.Frame(body, bg=BORDER)
        pass_frame.pack(fill="x", padx=32, pady=(4, 16))
        inner2 = tk.Frame(pass_frame, bg=BG3)
        inner2.pack(fill="x", padx=1, pady=1)
        self.pass_entry = tk.Entry(inner2, textvariable=self.pass_var,
                                   font=FONT_UI, bg=BG3, fg=TEXT,
                                   insertbackground=ACCENT, show="●",
                                   relief="flat")
        self.pass_entry.pack(fill="x", padx=12, ipady=10)

        # Encryption method
        tk.Label(body, text="ENCRYPTION METHOD", font=FONT_BADGE, bg=BG,
                 fg=TEXT2).pack(anchor="w", **pad)
        self.method_var = tk.StringVar(value="fernet")
        method_row = tk.Frame(body, bg=BG)
        method_row.pack(fill="x", padx=32, pady=(4, 24))
        for m, label, color in [("fernet", "Fernet", ACCENT2),
                                  ("caesar", "Caesar", ACCENT),
                                  ("xor",    "XOR",    ACCENT3)]:
            rb = tk.Radiobutton(method_row, text=label, variable=self.method_var,
                                value=m, font=FONT_UI, bg=BG, fg=color,
                                selectcolor=BG3, activebackground=BG,
                                activeforeground=color, relief="flat",
                                cursor="hand2")
            rb.pack(side="left", padx=(0, 16))

        # Login button
        btn = tk.Button(body, text="Connect  →", font=("Segoe UI Semibold", 11),
                        bg=ACCENT, fg=ON_ACCENT, relief="flat",
                        activebackground=ACCENT_HOVER, activeforeground=ON_ACCENT,
                        cursor="hand2", pady=4,
                        command=self._attempt_login)
        btn.pack(fill="x", padx=32)

        # Status
        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(body, textvariable=self.status_var,
                                   font=FONT_SMALL, bg=BG, fg=DANGER)
        self.status_lbl.pack(pady=(12, 0))

        self.pass_entry.bind("<Return>", lambda e: self._attempt_login())
        self.user_entry.focus_set()

    def _attempt_login(self):
        username = self.user_var.get().strip().upper()
        password = self.pass_var.get().strip()
        method   = self.method_var.get()
        password = ''.join(c for c in password if c.isalnum())

        if not username or not password:
            self.status_var.set("Username and password are required.")
            return

        self.status_var.set("Connecting…")
        self.root.update()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            login_msg = f"LOGIN||{username}||{password}\n"
            sock.sendall(login_msg.encode())
            response = sock.recv(1024).decode().strip()
            if response != "LOGIN SUKSES":
                self.status_var.set("Login failed. Check credentials.")
                sock.close()
                return
            if method == "fernet":
                load_key()
            self.on_login(sock, username, method)
        except ConnectionRefusedError:
            self.status_var.set(f"Cannot connect to {HOST}:{PORT}")
        except Exception as e:
            self.status_var.set(f"Error: {e}")


class ChatWindow:
    def __init__(self, root, sock, username, method):
        self.root = root
        self.sock = sock
        self.username = username
        self.method = method
        self.running = True

        self.root.title(f"SecureChat — {username}  [{method.upper()}]")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center(780, 580)
        self._build()
        self._start_receiver()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # ── Top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=BG2, pady=12)
        topbar.pack(fill="x")

        tk.Label(topbar, text="🔐 SecureChat", font=FONT_TITLE,
                 bg=BG2, fg=TEXT).pack(side="left", padx=16)

        # Badges
        badge_frame = tk.Frame(topbar, bg=BG2)
        badge_frame.pack(side="left", padx=8)

        method_color = {
            "fernet": ACCENT2, "caesar": ACCENT, "xor": ACCENT3
        }.get(self.method, TEXT2)
        self._badge(badge_frame, self.method.upper(), method_color)
        self._badge(badge_frame, self.username, TEXT2)

        # Online indicator
        dot_frame = tk.Frame(topbar, bg=BG2)
        dot_frame.pack(side="right", padx=16)
        tk.Label(dot_frame, text="●", font=("Segoe UI", 8),
                 bg=BG2, fg=ACCENT2).pack(side="left")
        tk.Label(dot_frame, text=" Connected", font=FONT_SMALL,
                 bg=BG2, fg=TEXT2).pack(side="left")

        # ── Chat area ────────────────────────────────────────────────────────
        chat_outer = tk.Frame(self.root, bg=BORDER, pady=1)
        chat_outer.pack(fill="both", expand=True, padx=12, pady=(8, 4))
        chat_inner = tk.Frame(chat_outer, bg=BG2)
        chat_inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.chat_display = scrolledtext.ScrolledText(
            chat_inner, font=FONT_MONO, bg=BG2, fg=TEXT,
            relief="flat", state="disabled", wrap="word",
            padx=16, pady=12, cursor="arrow",
            selectbackground=SELECT_BG, selectforeground=TEXT
        )
        self.chat_display.pack(fill="both", expand=True)

        # Tag styles
        self.chat_display.tag_config("sent",    background=SENT_BG, foreground=ACCENT,    lmargin1=8, lmargin2=8, rmargin=8, spacing1=4, spacing3=4)
        self.chat_display.tag_config("recv",    background=RECV_BG, foreground=ACCENT2,   lmargin1=8, lmargin2=8, rmargin=8, spacing1=4, spacing3=4)
        self.chat_display.tag_config("system",  background=SYSTEM,  foreground=TEXT2,      lmargin1=8, lmargin2=8, rmargin=8, spacing1=2, spacing3=2)
        self.chat_display.tag_config("img",     background=BG3,     foreground=ACCENT3,  lmargin1=8, lmargin2=8, rmargin=8, spacing1=4, spacing3=4)
        self.chat_display.tag_config("name_sent", foreground=ACCENT,  font=("Segoe UI Semibold", 10))
        self.chat_display.tag_config("name_recv", foreground=ACCENT2, font=("Segoe UI Semibold", 10))
        self.chat_display.tag_config("cipher",    foreground=MUTED,   font=("Consolas", 9))

        # ── Input row ────────────────────────────────────────────────────────
        input_frame = tk.Frame(self.root, bg=BG, pady=0)
        input_frame.pack(fill="x", padx=12, pady=(0, 12))

        # Image button
        img_btn = tk.Button(input_frame, text="📎", font=("Segoe UI", 14),
                            bg=BG3, fg=TEXT2, relief="flat", width=3,
                            activebackground=BG2, activeforeground=ACCENT,
                            cursor="hand2", command=self._send_image)
        img_btn.pack(side="left", padx=(0, 6))

        # Text entry
        entry_border = tk.Frame(input_frame, bg=BORDER, pady=1)
        entry_border.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry_inner = tk.Frame(entry_border, bg=BG3)
        entry_inner.pack(fill="x", padx=1, pady=1)

        self.msg_var = tk.StringVar()
        self.msg_entry = tk.Entry(entry_inner, textvariable=self.msg_var,
                                  font=FONT_MONO, bg=BG3, fg=TEXT,
                                  insertbackground=ACCENT, relief="flat")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        self.msg_entry.bind("<Return>", lambda e: self._send_message())
        self.msg_entry.focus_set()

        # Send button
        send_btn = tk.Button(input_frame, text="Send →",
                             font=("Segoe UI Semibold", 10),
                             bg=ACCENT, fg=ON_ACCENT, relief="flat",
                             activebackground=ACCENT_HOVER, activeforeground=ON_ACCENT,
                             cursor="hand2", padx=18, pady=10,
                             command=self._send_message)
        send_btn.pack(side="left")

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value=f"  {self.method.upper()} encryption active")
        tk.Label(self.root, textvariable=self.status_var,
                 font=FONT_SMALL, bg=BG, fg=MUTED,
                 anchor="w").pack(fill="x", padx=16, pady=(0, 6))

        self._append_system(f"Connected as {self.username} using {self.method.upper()} encryption.")

    def _badge(self, parent, text, color):
        f = tk.Frame(parent, bg=BG3, padx=8, pady=3)
        f.pack(side="left", padx=3)
        tk.Label(f, text=text, font=FONT_BADGE, bg=BG3, fg=color).pack()

    # ── Message display helpers ───────────────────────────────────────────────

    def _append_system(self, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  ⚡ {text}\n", "system")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _append_sent(self, text, cipher_preview=""):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  {self.username} (you)  ", "name_sent")
        self.chat_display.insert("end", f"{text}\n", "sent")
        if cipher_preview:
            self.chat_display.insert("end", f"  ↳ encrypted: {cipher_preview[:60]}…\n", "cipher")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _append_recv(self, sender, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"  {sender}  ", "name_recv")
        self.chat_display.insert("end", f"{text}\n", "recv")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _append_img(self, sender, filepath):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"\n  {sender} sent an image  \n", "name_recv")
        
        try:
            img = Image.open(filepath)
            img.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(img)

            if not hasattr(self, "_images"):
                self._images = []

            self._images.append(photo)

            self.chat_display.image_create("end", image=photo)
            self.chat_display.insert("end", "\n", "recv")

        except Exception as e:
            self.chat_display.insert("end", f"  [Error displaying image: {e}]\n")

        self.chat_display.insert("end", f"📷 Saved as: {filepath}\n", "img")

        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    # ── Send ─────────────────────────────────────────────────────────────────

    def _send_message(self):
        pesan = self.msg_var.get().strip()
        if not pesan:
            return
        self.msg_var.set("")

        try:
            if self.method == "caesar":
                terenkripsi = caesar_encrypt(pesan, 3)
            elif self.method == "xor":
                terenkripsi = xor_encrypt(pesan, 'kunci')
            elif self.method == "fernet":
                terenkripsi = fernet_encrypt(pesan)
            else:
                return

            kirim = f"{self.username}||{self.method}||{terenkripsi}\n"
            self.sock.sendall(kirim.encode())
            self._append_sent(pesan, terenkripsi)
        except Exception as e:
            self._append_system(f"Send error: {e}")

    def _send_image(self):
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All", "*.*")]
        )
        if not path or not os.path.exists(path):
            return
        try:
            self._append_system(f"Encrypting image: {os.path.basename(path)}…")
            self.root.update()
            encrypted_image = encrypt_image(path)
            kirim = f"{self.username}||IMAGE||{encrypted_image}\n"
            self.sock.sendall(kirim.encode())
            self._append_sent(f"📷 Image sent: {os.path.basename(path)}")
            self.status_var.set(f"  Image sent: {os.path.basename(path)}")
        except Exception as e:
            self._append_system(f"Image send error: {e}")

    # ── Receive ──────────────────────────────────────────────────────────────

    def _start_receiver(self):
        t = threading.Thread(target=self._receive_loop, daemon=True)
        t.start()

    def _receive_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    break
                buffer += data

                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if "||" not in message:
                        continue
                    try:
                        pengirim, metode, encrypted = message.split("||", 2)
                    except ValueError:
                        continue

                    if metode == "IMAGE":
                        try:
                            filename = generate_image_filename(self.username, pengirim)
                            decrypt_image(encrypted, filename)

                            self.root.after(0, self._append_img, pengirim, filename)

                        except Exception as e:
                            self.root.after(0, self._append_system,
                                            f"Image decrypt error: {e}")
                            
                    else:
                        try:
                            if metode == "caesar":
                                decrypted = caesar_decrypt(encrypted, 3)
                            elif metode == "xor":
                                decrypted = xor_decrypt(encrypted, 'kunci')
                            elif metode == "fernet":
                                decrypted = fernet_decrypt(encrypted)
                            else:
                                decrypted = encrypted
                            self.root.after(0, self._append_recv, pengirim, decrypted)
                        except Exception as e:
                            self.root.after(0, self._append_system,
                                            f"Decrypt error: {e}")
            except Exception:
                break

        if self.running:
            self.root.after(0, self._append_system, "Disconnected from server.")

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass
        self.root.destroy()


# ── App entry ─────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()

    def launch_chat(sock, username, method):
        
        for w in root.winfo_children():
            w.destroy()
        root.resizable(True, True)
        ChatWindow(root, sock, username, method)

    LoginWindow(root, on_login=launch_chat)
    root.mainloop()

if __name__ == "__main__":
    main()
