from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_data(data: bytes) -> bytes:
    key = load_key()
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(token: bytes) -> bytes:
    key = load_key()
    f = Fernet(key)
    return f.decrypt(token)

if __name__ == "__main__":
    # Demo usage
    secret = b"my super secret data"
    enc = encrypt_data(secret)
    print("Encrypted:", enc)
    dec = decrypt_data(enc)
    print("Decrypted:", dec) 