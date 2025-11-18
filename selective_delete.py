# selective_delete.py
import os
import time

ARCHIVE_DIR = "archive"
THRESH_DAYS = 7

def secure_delete(path, passes=1):
    try:
        size = os.path.getsize(path)
        with open(path, "rb+") as f:
            for _ in range(passes):
                f.seek(0)
                f.write(b"\x00" * size)
                f.flush()
        os.remove(path)
        print(f"secure deleted {path}")
    except Exception as e:
        print("failed to delete", path, e)

if __name__ == "__main__":
    cutoff = time.time() - THRESH_DAYS * 86400
    for fname in os.listdir(ARCHIVE_DIR):
        if not fname.endswith(".enc.bak"):
            continue
        path = os.path.join(ARCHIVE_DIR, fname)
        if os.path.getmtime(path) < cutoff:
            secure_delete(path)
