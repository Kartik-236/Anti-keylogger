Anti-Keylogger & Real-Time Monitoring System

A modular, Python-based anti-keylogger and activity monitoring system designed for cybersecurity research and defensive security. The project securely captures keystrokes, monitors connected devices, encrypts logs, and provides a real-time web dashboard for safe analysis.

Features

Anti-Keylogging Engine
Captures keystrokes and converts them into obfuscated text before storing, preventing leakage of sensitive information.

Secure Encryption Layer
All processed logs pass through a cryptographic wrapper for safe local storage.

Real-Time Monitoring Dashboard
Flask-based dashboard for live preview, log inspection, and system monitoring.

Device Activity Detection
Identifies newly connected USB/HID devices and alerts on suspicious keyboard-like hardware.

Selective Log Deletion
Tools to delete logs by age, size, or via full cleanup.

Modular Architecture
Each feature is implemented in a dedicated Python module for easier understanding and extension.

Project Structure
anti-keylogger/
│
├── agent.py                # Main runner
├── capture_controller.py   # Keyboard capture logic
├── device_monitor.py       # USB/HID monitoring
├── dashboard_app.py        # Flask dashboard server
├── encrypt_utils.py        # Encryption and obfuscation utilities
├── selective_delete.py     # Log cleanup utilities
│
├── static/                 # CSS, JS
├── templates/              # HTML templates for dashboard
│
├── requirements.txt        # Project dependencies
└── present.sh              # Optional script for launching services

Installation
1. Clone the Repository
git clone https://github.com/<your-username>/anti-keylogger.git
cd anti-keylogger

2. Create a Virtual Environment (Recommended)
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

3. Install Dependencies
pip install -r requirements.txt

Usage
Start the Anti-Keylogger Agent

(Requires sudo/root permissions on Linux)

sudo python3 agent.py

Launch the Real-Time Dashboard
python3 dashboard_app.py


Open in browser:
http://127.0.0.1:5000

Run Selective Log Cleanup
python3 selective_delete.py

How It Works
Keyboard Capture

The capture_controller.py module listens to low-level keyboard events and immediately obfuscates all captured input.

Encryption Layer

encrypt_utils.py encrypts logs using a secure key. No raw keystrokes are ever stored.

Monitoring Dashboard

The Flask dashboard renders live output, system status, and device changes, ensuring safe real-time monitoring.

Device Activity Tracking

device_monitor.py tracks newly connected or removed devices to detect potential hardware keyloggers or rogue USB inputs.

Log Management

selective_delete.py provides functions to purge outdated or oversized logs based on user-defined rules.

Technologies Used

Python 3

Flask

PyCryptodome / Fernet

Linux input event handling (/dev/input/)

HTML, CSS, JavaScript

Security & Ethics Disclaimer

This project is built only for educational, research, and defensive purposes.
Do not use it to capture keystrokes on systems without proper authorization. Misuse may violate privacy laws and cybersecurity regulations.
You are solely responsible for ethical use.

Contribution Guidelines

Contributions are welcome.
You may help by improving:

UI/UX of the dashboard

Device monitoring logic

Multi-platform support (Windows/Mac)

Documentation and examples

Please open an issue or submit a PR for discussion.

Support

If you find this project helpful, consider starring ⭐ the repository.
