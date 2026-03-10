#!/usr/bin/env python3
"""
Fake camera server — streams portrait photos from randomuser.me.
Downloads a batch of face portraits on startup, then loops through them.
No overlays, no bounding boxes — just clean face images for recognition testing.

Endpoints:
  GET /stream    — MJPEG live stream
  GET /snapshot  — latest JPEG still
  GET /health    — 200 once ready, 503 before that
  GET /people    — JSON list of names in current batch
"""

import os
import time
import threading
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
STREAM_PORT       = 8080
CACHE_DIR         = "/images/cache"
BATCH_SIZE        = 20
SECONDS_PER_PHOTO = 5
MJPEG_FPS         = 2
FRAME_DELAY       = 1.0 / MJPEG_FPS
IMG_W, IMG_H      = 640, 480
# ─────────────────────────────────────────────────────────────────────────────

current_frame = None
frame_lock    = threading.Lock()
people        = []   # list of {"name": str, "path": str}


def download_batch():
    os.makedirs(CACHE_DIR, exist_ok=True)
    url = f"https://randomuser.me/api/?results={BATCH_SIZE}&inc=name,picture&nat=us,gb,au,ca"
    try:
        print(f"[FakeCam] Fetching {BATCH_SIZE} portraits from randomuser.me ...")
        req = urllib.request.Request(url, headers={"User-Agent": "FakeCam/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[FakeCam] Failed to fetch people list: {e}")
        return []

    results = []
    for u in data.get("results", []):
        name    = f"{u['name']['first']} {u['name']['last']}"
        img_url = u["picture"]["large"]
        fname   = img_url.split("/")[-1]
        path    = os.path.join(CACHE_DIR, fname)

        if not os.path.exists(path):
            try:
                img_req = urllib.request.Request(img_url, headers={"User-Agent": "FakeCam/1.0"})
                with urllib.request.urlopen(img_req, timeout=15) as r:
                    with open(path, "wb") as f:
                        f.write(r.read())
                print(f"[FakeCam] Downloaded: {name}")
                time.sleep(0.2)
            except Exception as e:
                print(f"[FakeCam] Failed {name}: {e}")
                continue
        else:
            print(f"[FakeCam] Cached: {name}")

        results.append({"name": name, "path": path})

    print(f"[FakeCam] {len(results)} portraits ready")
    return results


def build_frame(path):
    """Resize portrait to stream dimensions — no overlays."""
    if PIL_AVAILABLE:
        try:
            img = Image.open(path).convert("RGB")
            img = img.resize((IMG_W, IMG_H), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=92)
            return buf.getvalue()
        except Exception as e:
            print(f"[FakeCam] Image error: {e}")
    with open(path, "rb") as f:
        return f.read()


def frame_generator():
    global current_frame
    index = 0
    tick  = 0
    frames_per_photo = max(1, int(SECONDS_PER_PHOTO / FRAME_DELAY))

    while True:
        if not people:
            time.sleep(0.5)
            continue

        person = people[index % len(people)]
        try:
            jpeg = build_frame(person["path"])
        except Exception as e:
            print(f"[FakeCam] Frame error: {e}")
            index += 1
            time.sleep(1)
            continue

        with frame_lock:
            current_frame = jpeg

        try:
            with open("/images/latest.jpg", "wb") as f:
                f.write(jpeg)
        except Exception:
            pass

        tick += 1
        if tick >= frames_per_photo:
            tick = 0
            index = (index + 1) % len(people)
            print(f"[FakeCam] Now showing: {people[index % len(people)]['name']}")

        time.sleep(FRAME_DELAY)


class MJPEGHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path in ("/stream", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    with frame_lock:
                        frame = current_frame
                    if frame:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                    time.sleep(FRAME_DELAY)
            except (BrokenPipeError, ConnectionResetError):
                pass

        elif self.path == "/snapshot":
            with frame_lock:
                frame = current_frame
            if frame:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
            else:
                self.send_response(503)
                self.end_headers()

        elif self.path == "/health":
            with frame_lock:
                ready = current_frame is not None
            self.send_response(200 if ready else 503)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK" if ready else b"NOT READY")

        elif self.path == "/people":
            payload = json.dumps([p["name"] for p in people]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs("/images", exist_ok=True)

    batch = download_batch()
    if not batch:
        print("[FakeCam] ERROR: No portraits downloaded — check network access.")
    people.extend(batch)

    t = threading.Thread(target=frame_generator, daemon=True)
    t.start()

    print("[FakeCam] Waiting for first frame ...")
    for _ in range(30):
        with frame_lock:
            if current_frame:
                break
        time.sleep(0.5)

    print(f"[FakeCam] Ready — streaming {len(people)} people")
    print(f"[FakeCam]   Stream:   http://0.0.0.0:{STREAM_PORT}/stream")
    print(f"[FakeCam]   Snapshot: http://0.0.0.0:{STREAM_PORT}/snapshot")
    print(f"[FakeCam]   People:   http://0.0.0.0:{STREAM_PORT}/people")

    server = HTTPServer(("0.0.0.0", STREAM_PORT), MJPEGHandler)
    server.serve_forever()