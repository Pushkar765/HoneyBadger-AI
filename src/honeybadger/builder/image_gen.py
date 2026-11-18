import base64
import logging
import os
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

IMAGE_DIR = Path(__file__).resolve().parent / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

HUGGINGFACE_MODEL = "runwayml/stable-diffusion-v1-5"
HUGGINGFACE_API_URL = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"


def _slugify(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.lower())
    return safe.strip("-")[:120]


def _save_image_bytes(image_bytes: bytes, prompt: str, out_path: Optional[Path] = None) -> Path:
    filename = out_path or IMAGE_DIR / f"image-{_slugify(prompt)}.png"
    with open(filename, "wb") as fh:
        fh.write(image_bytes)
    return filename


def generate_image(prompt: str, out_path: Optional[str] = None) -> Path:
    path = Path(out_path) if out_path else None
    try:
        import importlib

        diffusers = importlib.import_module("diffusers")
        torch = importlib.import_module("torch")
        StableDiffusionPipeline = diffusers.StableDiffusionPipeline

        model_id = "runwayml/stable-diffusion-v1-5"
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe.enable_attention_slicing()
        pipe.to("cpu")

        image = pipe(prompt, guidance_scale=7.5, num_inference_steps=30).images[0]
        save_path = path or IMAGE_DIR / f"image-{_slugify(prompt)}.png"
        image.save(save_path)
        logger.info("Generated local image for prompt: %s", prompt)
        return save_path
    except Exception as exc:
        logger.warning("Local diffusion generation failed (%s), falling back to Hugging Face Inference API.", exc)
        return _generate_image_cloud(prompt, path)


def _generate_image_cloud(prompt: str, out_path: Optional[Path] = None) -> Path:
    api_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    response = requests.post(
        HUGGINGFACE_API_URL,
        headers=headers,
        json={"inputs": prompt, "options": {"wait_for_model": True}},
        timeout=120,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "image" in content_type:
        image_bytes = response.content
    else:
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"Hugging Face API error: {data['error']}")
        if isinstance(data, str):
            image_bytes = base64.b64decode(data)
        elif isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("generated_image"):
            image_bytes = base64.b64decode(data[0]["generated_image"])
        else:
            raise RuntimeError("Unexpected Hugging Face image response format.")

    save_path = out_path or IMAGE_DIR / f"image-{_slugify(prompt)}.png"
    return _save_image_bytes(image_bytes, prompt, save_path)
