# agent.py
"""
Standalone wrapper to run the capture controller from the terminal.
This lets you run:
    python3 agent.py
and you will capture keystrokes until Ctrl+C.
"""
import sys
from capture_controller import controller

def main():
    print("[agent] starting...")
    controller.start()
    try:
        # just block while controller runs; flusher thread handles writes
        while True:
            # sleep main thread to avoid busy loop
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("[agent] stopped by user.")
        controller.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
