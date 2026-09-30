#!/usr/bin/env bash
# Starts the whole project with one command. Ctrl+C stops everything, camera included.
# - On the Mac: the API (MLX needs the Apple GPU) and ffmpeg (needs the webcam),
#   because the Docker VM can see neither.
# - In Docker: MediaMTX and the sampler (docker-compose.yml).
# Each piece starts once what it depends on is ready: API, MediaMTX, webcam stream, sampler.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

cleanup() {
    echo "Stopping everything..."
    # Stopping ffmpeg turns the camera off; stopping the API frees the model's RAM.
    kill ${LOGS_PID:-} ${FFMPEG_PID:-} ${API_PID:-} 2>/dev/null || true
    docker compose down
    wait 2>/dev/null || true
}
trap cleanup EXIT
# Ctrl+C or `kill`: exit normally, so that the EXIT trap above runs.
trap 'exit 130' INT TERM

echo "Starting the API (loading the model takes a few seconds)..."
camenv/bin/uvicorn api:app --host 127.0.0.1 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
until curl -s -o /dev/null localhost:8000/health; do
    kill -0 "$API_PID" 2>/dev/null || { echo "The API failed to start, see logs/api.log"; exit 1; }
    sleep 1
done

echo "Starting MediaMTX..."
docker compose up -d mediamtx
# ffmpeg gives up at once if the server isn't there: wait until MediaMTX answers an RTSP request.
until curl -s -o /dev/null rtsp://localhost:8554; do sleep 1; done

echo "Streaming the webcam..."
ffmpeg -nostdin -f avfoundation -framerate 30 -video_size 1280x720 -i "0" \
    -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -g 30 \
    -rtsp_transport tcp -f rtsp rtsp://localhost:8554/webcam > logs/ffmpeg.log 2>&1 &
FFMPEG_PID=$!
until ffprobe -v quiet -rtsp_transport tcp rtsp://localhost:8554/webcam; do
    kill -0 "$FFMPEG_PID" 2>/dev/null || { echo "ffmpeg failed to start, see logs/ffmpeg.log"; exit 1; }
    sleep 1
done

echo "Starting the sampler..."
docker compose up -d --build sampler

echo "Descriptions every 10 s below. Ctrl+C stops everything."
# In the background + wait: a signal interrupts `wait` at once, whereas bash would wait
# for a foreground `logs -f` (which never ends) before running the trap.
docker compose logs -f sampler &
LOGS_PID=$!
wait "$LOGS_PID"
