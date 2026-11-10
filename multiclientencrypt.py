import socket
import threading
import getpass
import os
from utils import caesar_encrypt, xor_encrypt, fernet_encrypt, caesar_decrypt, xor_decrypt,fernet_decrypt,encrypt_image,decrypt_image

HOST = '127.0.0.1'
PORT = 12345

def input_password(prompt="PASSWORD: "):
    pw = getpass.getpass(prompt)
    print("*" * len(pw))  # tampilkan ***** setelah input
    return pw

def kirim_pesan(sock, metode, username):
    while True:
        try:
            pesan = input()
        except KeyboardInterrupt:
            print("\n[EXIT] Client Keluar")
            sock.close()
            break

        try:
            #IMAGE
            if pesan.startswith("/img "):
                file_path = pesan[5:].strip()

                if not os.path.exists(file_path):
                    print("[ERROR] File tidak ditemukan.")
                    continue

                print("[INFO] Encrypting Image...")
                encrypted_image = encrypt_image(file_path)

                kirim = f"{username}||IMAGE||{encrypted_image}\n"
                sock.sendall(kirim.encode())

                print("[INFO] Gambar berhasil dikirim")
                continue

            #CHAT
            if metode == "caesar":
                terenkripsi = caesar_encrypt(pesan, 3)
            elif metode == "xor":
                terenkripsi = xor_encrypt(pesan, 'kunci')
            elif metode == "fernet":
                terenkripsi = fernet_encrypt(pesan)
            else:
                print("Metode enkripsi tidak valid.")
                continue
            
            kirim = f"{username}||{metode}||{terenkripsi}\n"
            sock.sendall(kirim.encode())

        except Exception as e:
            print(f"Error: {e}")
            break

def terima_pesan(sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode()
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
                        saved_path = save_image_per_user(pengirim, encrypted)
                        print(f"\n{pengirim} mengirim gambar -> disimpan sebagai {saved_path}")
                    except Exception as e:
                        print(f"[ERROR] Gagal decrypt gambar: {e}")
                
                else:
                    if metode == "caesar":
                        decrypted = caesar_decrypt(encrypted, 3)
                    elif metode == "xor":
                        decrypted = xor_decrypt(encrypted, 'kunci')
                    elif metode == "fernet":
                        decrypted = fernet_decrypt(encrypted)
                    else:
                        decrypted = encrypted
                        
                    # #tester enkripsi
                    # print("raw msg = ", repr(message))

                    print(f"\n{pengirim}: {decrypted}")

        except Exception as e:
            print(f"Error menerima pesan: {e}")
            break

BASE_FOLDER = "received"

def save_image_per_user(sender, encrypted_data):

    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)
    
    user_folder = os.path.join(BASE_FOLDER, sender)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    index = 1
    while True:
        filename = f"received_{sender}_{index}.png"
        full_path = os.path.join(user_folder, filename)

        if not os.path.exists(full_path):
            break
        index += 1

    decrypted_image = decrypt_image(encrypted_data, full_path)

    return full_path

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
        
    username = input("USERNAME (AD, AL, AU): ").strip().upper()
    password = input_password("PASSWORD: ").strip()
    password = ''.join(c for c in password if c.isalnum())

    login_msg = f"LOGIN||{username}||{password}\n"
    sock.sendall(login_msg.encode())

    response = sock.recv(1024).decode().strip()
    if response != "LOGIN SUKSES":
        print("LOGIN GAGAL")
        sock.close()
        return
    
    print(f"LOGIN BERHASIL SEBAGAI {username}")
     
    print("Pilihan metode enkripsi: caesar, xor, fernet")
    metode = input("Pilih metode enkripsi: ").strip().lower()

    if metode not in ["caesar", "xor", "fernet"]:
        print("Metode tidak valid, menggunakan fernet sebagai default")
        metode = "fernet"

        # Generate key if it doesn't exist (only for Fernet)
    if metode == "fernet":
        from utils import load_key
        load_key()  # This will create the key file if missing
        
    threading.Thread(target=terima_pesan, args=(sock,), daemon=True).start()

    try:
        kirim_pesan(sock, metode, username)
    except KeyboardInterrupt:
        print("\n[Client Closed]")
    finally:
        sock.close()

if __name__ == "__main__":
    main()