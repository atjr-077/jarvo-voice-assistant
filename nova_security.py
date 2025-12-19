"""
NOVA Security Module
- Device locking
- Access key management
- Tamper detection
- Setup walkthrough
- Warnings/FAQs
"""
import os
import uuid
import hashlib
import json
from cryptography.fernet import Fernet, InvalidToken

SECURE_DIR = os.path.expanduser("~/.nova_secure")
DEVICE_ID_FILE = os.path.join(SECURE_DIR, "device_id")
KEY_FILE = os.path.join(SECURE_DIR, "access_key.enc")
ACTIVATION_FILE = os.path.join(SECURE_DIR, "activated.json")
TAMPER_HASH_FILE = os.path.join(SECURE_DIR, "file_hashes.json")
FERNET_KEY_FILE = os.path.join(SECURE_DIR, "fernet.key")

FAQ = """
NOVA Setup & Security
- Do not uninstall NOVA after activation.
- Do not share your access key. It is bound to this device.
- Tampering with files disables the assistant.
- For support, contact: support@nova-assistant.local
"""

MOCK_VALID_KEYS = {"NOVA-1234-5678-ABCD": False, "NOVA-0000-1111-2222": False}  # False = not used

# --- Encryption helpers ---
def get_fernet():
    if not os.path.exists(FERNET_KEY_FILE):
        key = Fernet.generate_key()
        os.makedirs(SECURE_DIR, exist_ok=True)
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

def encrypt_data(data: str) -> bytes:
    return get_fernet().encrypt(data.encode())

def decrypt_data(token: bytes) -> str:
    return get_fernet().decrypt(token).decode()

# --- Device ID ---
def get_device_id():
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            return f.read().strip()
    device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, os.environ.get("COMPUTERNAME", "NOVA")))
    os.makedirs(SECURE_DIR, exist_ok=True)
    with open(DEVICE_ID_FILE, "w") as f:
        f.write(device_id)
    return device_id

# --- Tamper Detection ---
def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_tracked_files():
    # Track main.py and actions.py for tamper detection
    return ["main.py", "actions.py"]

def save_file_hashes():
    os.makedirs(SECURE_DIR, exist_ok=True)
    hashes = {f: hash_file(f) for f in get_tracked_files() if os.path.exists(f)}
    with open(TAMPER_HASH_FILE, "w") as f:
        json.dump(hashes, f)

def check_tamper():
    if not os.path.exists(TAMPER_HASH_FILE):
        save_file_hashes()
        return False
    with open(TAMPER_HASH_FILE, "r") as f:
        old_hashes = json.load(f)
    for f in get_tracked_files():
        if not os.path.exists(f):
            return True
        if hash_file(f) != old_hashes.get(f):
            return True
    return False

# --- Access Key Management ---
def is_first_run():
    return not os.path.exists(ACTIVATION_FILE)

def validate_access_key(input_key):
    device_id = get_device_id()
    # Mock: check if key is valid and unused
    if input_key in MOCK_VALID_KEYS and not MOCK_VALID_KEYS[input_key]:
        MOCK_VALID_KEYS[input_key] = True  # Mark as used
        # Store activation info
        activation = {"device_id": device_id, "key": input_key}
        with open(ACTIVATION_FILE, "w") as f:
            json.dump(activation, f)
        # Store encrypted key
        with open(KEY_FILE, "wb") as f:
            f.write(encrypt_data(input_key))
        save_file_hashes()
        return True
    return False

def check_activation():
    if not os.path.exists(ACTIVATION_FILE) or not os.path.exists(KEY_FILE):
        return False
    with open(ACTIVATION_FILE, "r") as f:
        activation = json.load(f)
    device_id = get_device_id()
    if activation.get("device_id") != device_id:
        return False
    try:
        with open(KEY_FILE, "rb") as f:
            key = decrypt_data(f.read())
        if key != activation.get("key"):
            return False
    except Exception:
        return False
    return True

# --- Setup Walkthrough ---
def run_setup_walkthrough():
    print("\n=== Welcome to NOVA Secure Assistant ===")
    print(FAQ)
    print("\nStep 1: Enter your access key (format: NOVA-XXXX-XXXX-XXXX)")
    for _ in range(3):
        key = input("Access Key: ").strip()
        if validate_access_key(key):
            print("Activation successful! This device is now bound to your key.")
            return True
        else:
            print("Invalid or already-used key. Please try again.")
    print("Activation failed. Exiting.")
    exit(1)

# --- Update System (Mock) ---
def check_for_updates():
    print("Checking for updates... (mock)")
    # In real use, fetch version info from remote
    print("You are running the latest version.") 