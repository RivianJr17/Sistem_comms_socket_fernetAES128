import socket
import threading
import bcrypt

HOST = '127.0.0.1'
PORT = 12345

USERS = {
    "AD" : b'$2b$12$8tE6KRBZARtun2kW5REtB.34hYfb/jS6WqbwLGnXp.dE1ObgHTULu',
    "AL" : b'$2b$12$XLVzsX5we3HJ5eW8u6WJu.2EbvpM/ca50WD1CldIW8cr0IudW4eZO',
    "AU" : b'$2b$12$RAPudmY237d/pjSQJMDwj.bUIGjsvdiYbbBYAR5N7O/HY2nZpjX1a'
}

clients = {}

def broadcast(message, sender):
    for client in list(clients):
        if client != sender:
            try:
                client.sendall(message)
            except:
                client.close()
                if client in clients:
                    del clients[client]

def handle_client(conn, addr):
    print(f"[TERHUBUNG] Client {addr} terhubung.")

    try:
        # LOGIN
        data = conn.recv(1024).decode()
        # TEST
        print("login raw data: ", repr(data))

        if not data.startswith("LOGIN||"):
            conn.sendall(b"LOGIN FAIL\n")
            return
        
        login_line = data.strip()
        _, username, password = login_line.split("||", 2)

        username = username.strip().upper()
        password = ''.join(c for c in password if c.isalnum())

        stored_hash = USERS.get(username)

        # print("TEST DIRECT:", bcrypt.checkpw(b"ad123", stored_hash))

        if not stored_hash:
            conn.sendall(b"LOGIN FAIL\n")
            print(f"[LOGIN GAGAL - USER]{addr}")
            return
        
        result = bcrypt.checkpw(password.encode(), stored_hash)
        print("[DEBUG] result:", result)

        if not result:
            conn.sendall(b"LOGIN FAIL\n")
            print(f"[LOGIN GAGAL - PASSWORD]{addr}")
            return
        
        # LOGIN SUKSES
        clients[conn] = username
        conn.sendall(b"LOGIN SUKSES\n")
        print(f"[LOGIN SUKSES] {username} dari {addr}")

        # LOOP CHAT (support image & msg panjang)
        buffer = ""
        
        while True:
            data = conn.recv(4096).decode()
            if not data:
                break

            buffer += data

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
            
                print(f"[{username}] ciphertext diterima ({len(message)} chars)")
                broadcast((message + "\n").encode(), conn)

    except Exception as e:
        print("ERROR:", e)

    finally:
        if conn in clients:
            print(f"[TERPUTUS] {clients[conn]} keluar")
            del clients[conn]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER AKTIF] Menunggu koneksi di {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True)
        thread.start()

if __name__ == "__main__":
    start_server()
