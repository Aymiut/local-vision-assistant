# Local camera assistant


## What works

- Phase 1: a local API (FastAPI + Gemma via MLX) receives an image and returns a description of it.
- Phase 2: the webcam is streamed over RTSP through MediaMTX, running in Docker.
- Phase 2: a sampler container grabs a frame from the stream every 10 s, sends it to the API and logs the description.

## Running the API

```bash
python3 -m venv camenv && source camenv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8000
curl -F "image=@photo.jpg" localhost:8000/describe
```
