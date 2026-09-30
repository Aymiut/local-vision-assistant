# Sampler image: grabs one frame from the RTSP stream every 10 s and sends it to the API.
# Build from the repo root: docker build -t sampler sampler/

# Slim variant: fewer packages, so a smaller image and fewer findings for Trivy.
FROM python:3.14-slim

WORKDIR /app

# Without a terminal, Python buffers its output and `docker logs` stays empty.
ENV PYTHONUNBUFFERED=1

# Dependencies before the code: editing sampler.py doesn't invalidate the pip install layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sampler.py .

# The --system option creates a system user not meant to be used by humans, with no home directory and no password. The app runs as this user, not root.
RUN useradd --system app
USER app

# JSON form: python runs as PID 1 and receives SIGTERM from `docker stop` directly.
CMD ["python", "sampler.py"]
