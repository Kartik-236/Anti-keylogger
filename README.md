Anti-Keylogger & Real-Time Monitoring System

A modular Python-based defensive security tool for researching and detecting keylogging behavior and suspicious input devices. The system captures keyboard activity in a privacy-preserving manner, encrypts all logs, monitors connected devices, and provides a real-time web dashboard for safe analysis.

Key Features

Anti-Keylogging Engine
Captures keyboard events and immediately obfuscates input — no raw keystrokes are stored.

Secure Encryption Layer
All logs are encrypted before local storage using AES encryption.

Real-Time Monitoring Dashboard
Flask-based dashboard for live activity preview, log inspection, and system status.

Selective Log Management
Delete logs by age, size, or perform full cleanup.

Modular Architecture
Each feature is implemented as a separate Python module for clarity and extensibility.

Project Structure
anti-keylogger/
├── agent.py                # Main runner
├── capture_controller.py   # Keyboard capture logic
├── device_monitor.py       # USB/HID monitoring
├── dashboard_app.py        # Flask dashboard
├── encrypt_utils.py        # Encryption & obfuscation
├── selective_delete.py     # Log cleanup
├── static/                 # CSS, JS
├── templates/              # Dashboard HTML
├── requirements.txt
└── present.sh

Installation
git clone https://github.com/<your-username>/anti-keylogger.git
cd anti-keylogger
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

Usage

Start the agent (Linux requires root for input events):

sudo python3 agent.py


Launch dashboard:

python3 dashboard_app.py


Open: http://127.0.0.1:5000

Log cleanup:

python3 selective_delete.py

Technologies

Python 3

Flask

PyCryptodome / Fernet

Linux /dev/input event handling

HTML, CSS, JavaScript

Security & Ethics

This project is intended only for educational, research, and defensive security purposes.
Do not use it without proper authorization. You are responsible for ethical and legal use.

Contributions

Contributions are welcome, especially for:

UI/UX improvements

Enhanced device monitoring

Documentation
