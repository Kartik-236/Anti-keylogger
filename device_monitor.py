import os
PENDRIVE_MOUNT = "/mnt/secure_usb"
PENDRIVE_LOG_DIR = os.path.join(PENDRIVE_MOUNT, "logs")
def is_connected():
    return os.path.ismount(PENDRIVE_MOUNT) and os.access(PENDRIVE_LOG_DIR, os.W_OK)
def ensure_log_dir():
    if not os.path.exists(PENDRIVE_LOG_DIR):
        try:
            os.makedirs(PENDRIVE_LOG_DIR, exist_ok=True)
            return True
        except Exception:
            return False
    return True
if __name__ == "__main__":
    print("connected:", is_connected())
    print("log dir exists:", os.path.exists(PENDRIVE_LOG_DIR))
