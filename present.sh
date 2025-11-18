#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
# activate venv if exists
if [ -f venv_bad/bin/activate ]; then
  source venv_bad/bin/activate
fi
# ensure pendrive logs dir exists (best-effort)
[ -d /mnt/secure_usb/logs ] || sudo mkdir -p /mnt/secure_usb/logs || true
sudo chown $(id -u -n):$(id -u -n) /mnt/secure_usb/logs 2>/dev/null || true
# start dashboard in background
python3 dashboard_app.py &>/dev/null &
sleep 1
# open demo page
xdg-open ~/demo_bank/index.html || true
echo "Dashboard started (http://127.0.0.1:5000). Demo page opened."
echo "Use the dashboard Start Capture button to begin capture (only records when DemoBank window is active)."
