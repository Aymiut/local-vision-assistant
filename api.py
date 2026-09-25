import asyncio
import io
import os
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
from PIL import Image, UnidentifiedImageError


MODELE = os.environ.get("MODELE", "mlx-community/gemma-4-e4b-it-4bit")
QUESTION_PAR_DEFAUT = "Décris cette image. Combien de personnes ? Quel contexte ?"

# MLX lie son travail GPU au thread qui l'a lancé : on charge le modèle et on génère
# toujours dans ce même thread unique. Les requêtes attendent leur tour dans une file.
gpu = ThreadPoolExecutor(max_workers=1)
modele = {}


def charger():
    modele["model"], modele["processor"] = load(MODELE)
    modele["config"] = load_config(MODELE)


def decrire(image, question):
    prompt = apply_chat_template(modele["processor"], modele["config"], question, num_images=1)
    resultat = generate(modele["model"], modele["processor"], prompt, [image], max_tokens=300)
    return resultat.text


@asynccontextmanager
async def lifespan(app):
    # Chargé une seule fois au démarrage, pas à chaque requête.
    await asyncio.get_running_loop().run_in_executor(gpu, charger)
    yield
    gpu.shutdown()


app = FastAPI(title="local-vision-assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "modele": MODELE}


@app.post("/describe")
async def describe(image: UploadFile = File(...), question: str = Form(QUESTION_PAR_DEFAUT)):
    try:
        img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Le fichier envoyé n'est pas une image.")

    debut = time.perf_counter()
    texte = await asyncio.get_running_loop().run_in_executor(gpu, decrire, img, question)
    return {"description": texte, "duree_s": round(time.perf_counter() - debut, 2)}
