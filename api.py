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


MODEL = os.environ.get("MODEL", "mlx-community/gemma-4-e4b-it-4bit")
DEFAULT_QUESTION = "Describe this image. How many people? What is the context?"

# MLX binds its GPU work to the thread that started it: the model is always loaded and
# run in this single thread. Requests wait for their turn in a queue.
gpu = ThreadPoolExecutor(max_workers=1)
model = {}


def load_model():
    model["model"], model["processor"] = load(MODEL)
    model["config"] = load_config(MODEL)


def describe_image(image, question):
    prompt = apply_chat_template(model["processor"], model["config"], question, num_images=1)
    result = generate(model["model"], model["processor"], prompt, [image], max_tokens=300)
    return result.text


@asynccontextmanager
async def lifespan(app):
    # Loaded once at startup, not on every request.
    await asyncio.get_running_loop().run_in_executor(gpu, load_model)
    yield
    gpu.shutdown()


app = FastAPI(title="local-vision-assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/describe")
async def describe(image: UploadFile = File(...), question: str = Form(DEFAULT_QUESTION)):
    try:
        img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="The uploaded file is not an image.")

    start = time.perf_counter()
    text = await asyncio.get_running_loop().run_in_executor(gpu, describe_image, img, question)
    return {"description": text, "duration_s": round(time.perf_counter() - start, 2)}
