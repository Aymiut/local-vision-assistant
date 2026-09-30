import io
import os
import signal
import sys
import time

import av
import requests


# Every setting comes from the environment: docker compose, then Kubernetes, will set them.
# From inside a container, the Mac is reachable as host.docker.internal.
STREAM_URL = os.environ.get("STREAM_URL", "rtsp://host.docker.internal:8554/webcam")
API_URL = os.environ.get("API_URL", "http://host.docker.internal:8000/describe")
INTERVAL_S = float(os.environ.get("INTERVAL_S", "10"))
# Keep it short: one sentence takes ~5-7 s, a detailed description ~24 s (longer than the interval).
QUESTION = os.environ.get("QUESTION", "In one sentence: what do you see?")


def grab_frame():
    """Connect to the stream, decode the first frame, disconnect. Returns a PIL image."""
    with av.open(STREAM_URL, options={"rtsp_transport": "tcp"}) as container:
        for frame in container.decode(video=0):
            img = frame.to_image()
            return img


def to_jpeg(image):
    """Encode a PIL image as JPEG bytes, in memory: nothing is written to disk."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def describe(jpeg):
    """Send the image to the API and return its JSON answer: {"description": ..., "duration_s": ...}."""
    response = requests.post(
        API_URL,
        files={"image": ("frame.jpg", jpeg, "image/jpeg")},
        data={"question": QUESTION},
        # Without a timeout, a stuck API would block the loop forever.
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def main():
    # In a container the script runs as PID 1, which ignores SIGTERM unless it handles it:
    # without this, `docker stop` waits 10 s and then kills it.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    print(f"Sampling {STREAM_URL} every {INTERVAL_S:g} s, sending to {API_URL}")
    while True:
        start = time.monotonic()
        try:
            result = describe(to_jpeg(grab_frame()))
            print(f"{time.strftime('%H:%M:%S')} ({result['duration_s']} s) {result['description']}")
        except Exception as error:
            # The stream or the API can be down for a while (startup, restart): log it and try again.
            print(f"{time.strftime('%H:%M:%S')} error: {error!r}")

        # One request at a time, one round every INTERVAL_S seconds.
        # If the round took longer than the interval, the next one starts right away.
        time.sleep(max(0, INTERVAL_S - (time.monotonic() - start)))


if __name__ == "__main__":
    main()
