# Frigate + CompreFace + Double-Take + Home Assistant — Test Stack

A fully wired local test environment for face recognition with NVR.

```
fake-camera (MJPEG)
       ↓
   Frigate  ──── MQTT ────► Double-Take ──► CompreFace
       │                         │
       │                    MQTT results
       │                         ↓
       └──────────────► Home Assistant
```

---

## Quick Start

### 1. Start the stack

```bash
docker compose up -d --build
```

> First run takes a few minutes — CompreFace and Frigate are large images.

### 2. Wait for services to be healthy

```bash
docker compose ps
```

All services should show `healthy` or `running`.

---

## Service URLs

| Service        | URL                        | Notes                          |
|----------------|----------------------------|--------------------------------|
| Fake Camera    | http://localhost:8090      | /stream  /snapshot  /health    |
| Frigate UI     | http://localhost:5000      | NVR dashboard                  |
| CompreFace UI  | http://localhost:8000      | Face management                |
| Double-Take UI | http://localhost:3000      | Recognition events             |
| Home Assistant | http://localhost:8123      | HA dashboard                   |
| MQTT Broker    | localhost:1883             | Use any MQTT client to inspect |

---

## Setup Steps (after containers start)

### Step 1 — CompreFace: Create a Recognition Service

1. Open http://localhost:8000
2. Register an account (first user becomes admin)
3. Click **Create Application** → name it `frigate-test`
4. Inside the application, click **Create Service** → choose **Recognition**
5. Name it `people` → note the **API Key** shown

### Step 2 — Double-Take: Add the API Key

Edit `config/double-take/config.yml`:

```yaml
detectors:
  compreface:
    api_key: "PASTE-YOUR-API-KEY-HERE"   # ← replace this
```

Then restart Double-Take:

```bash
docker compose restart double-take
```

### Step 3 — CompreFace: Train Faces

You need to add at least one face before recognition works.

**Option A — via CompreFace UI:**
1. Open http://localhost:8000 → your application → Recognition service
2. Click **Add Subject** → enter a name (e.g. `Alice`)
3. Upload face photos for that subject

**Option B — via curl API:**
```bash
curl -X POST "http://localhost:8000/api/v1/recognition/faces" \
  -H "x-api-key: YOUR_API_KEY" \
  -F "file=@/path/to/face.jpg" \
  -F "subject=Alice"
```

### Step 4 — Home Assistant: Onboarding

1. Open http://localhost:8123
2. Complete the setup wizard (create account, set location)
3. HA will auto-discover MQTT sensors defined in `configuration.yaml`
4. Go to **Developer Tools → States** to see:
   - `binary_sensor.fake_cam_motion`
   - `binary_sensor.fake_cam_person_detected`
   - `sensor.double_take_last_match`
   - `camera.fake_camera`

---

## Using Your Own Images as the Fake Camera

Drop `.jpg` / `.png` images into `fake-camera/images/`:

```bash
cp ~/my-test-photos/*.jpg fake-camera/images/
docker compose restart fake-camera
```

The camera will cycle through them at ~5 FPS. Place images that include faces
to properly test the full recognition pipeline.

---

## MQTT Credentials

| User            | Password          | Used by         |
|-----------------|-------------------|-----------------|
| frigate         | frigate123        | Frigate         |
| doubletake      | doubletake123     | Double-Take     |
| homeassistant   | homeassistant123  | Home Assistant  |
| admin           | admin123          | Testing/debug   |

**Monitor all MQTT traffic:**
```bash
docker exec mosquitto mosquitto_sub \
  -h localhost -u admin -P admin123 \
  -t '#' -v
```

**Monitor just recognition results:**
```bash
docker exec mosquitto mosquitto_sub \
  -h localhost -u admin -P admin123 \
  -t 'double-take/#' -v
```

---

## Stopping / Resetting

```bash
# Stop all services
docker compose down

# Full reset (wipes all data/volumes)
docker compose down -v
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Frigate not detecting | Check stream: `http://localhost:5000` → Cameras tab |
| CompreFace returns 401 | Wrong API key in double-take config.yml |
| Double-Take not receiving events | Check MQTT credentials and that Frigate is publishing |
| HA MQTT sensors unavailable | Confirm HA MQTT integration is connected (Settings → Integrations) |
| No faces recognized | Make sure you added + trained faces in CompreFace first |
