# utils.py
from cryptography.fernet import Fernet
import os
import base64

# Enkripsi Caesar Cipher
def caesar_encrypt(plaintext, shift):
    result = ''
    for char in plaintext:
        if char.isalpha():
            offset = 65 if char.isupper() else 97
            result += chr((ord(char) + shift - offset) % 26 + offset)
        else:
            result += char
    return result

# Dekripsi Caesar Cipher
def caesar_decrypt(ciphertext, shift):
    result = ''
    for char in ciphertext:
        if char.isalpha():
            offset = 65 if char.isupper() else 97
            result += chr((ord(char) - shift - offset) % 26 + offset)
        else:
            result += char
    return result

# Enkripsi XOR Cipher
def xor_encrypt(plaintext, key):
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(plaintext))

# Dekripsi XOR Cipher
def xor_decrypt(ciphertext, key):
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(ciphertext))


# Generate and save a key (run this once)
def generate_key():
    key = Fernet.generate_key()
    with open("fernet_key.key", "wb") as key_file:
        key_file.write(key)

# Generate and save Fernet key if it doesn't exist
def generate_key():
    key = Fernet.generate_key()
    with open("fernet_key.key", "wb") as key_file:
        key_file.write(key)

# Load or create Fernet key
def load_key():
    if not os.path.exists("fernet_key.key"):
        generate_key()
    return open("fernet_key.key", "rb").read()

# Fernet Encryption
def fernet_encrypt(message: str) -> str:
    key = load_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return encrypted.decode()  # Convert bytes to string for easier handling

# Fernet Decryption
def fernet_decrypt(encrypted_message: str) -> str:
    key = load_key()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_message.encode())
    return decrypted.decode()

#image support(base64 + Fernet)
#file -> base64 string
def file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')
    
#base64 -> file
def base64_to_file(b64_string: str, output_path: str):
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64_string.encode('utf-8')))

#encrypt image (return string)
def encrypt_image(file_path: str) -> str:
    b64_data = file_to_base64(file_path)
    return fernet_encrypt(b64_data)

#decrypt image -> save file
def decrypt_image(encrypted_data: str,output_path: str):
    decrypted_b64 = fernet_decrypt(encrypted_data)
    base64_to_file(decrypted_b64, output_path)