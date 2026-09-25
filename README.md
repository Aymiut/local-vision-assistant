# Projet assistant caméra local


## Ce qui marche

- Phase 1 : une API locale (FastAPI + Gemma via MLX) reçoit une image et renvoie sa description.

## Lancer l'API

```bash
python3 -m venv camenv && source camenv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8000
curl -F "image=@photo.jpg" localhost:8000/describe
```
