# utils_image.py
import os

from PIL import Image


def load_image_resized(path: str):
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGB").resize((224, 224))
    return img
