"""Готовит картинку для превью ссылки (Open Graph): 1200×630.

    python scripts/build_og.py

Берёт фото из data/business.json → photos.hero, режет по центру под 1200×630,
сохраняет assets/img/og.jpg.
"""
import json
import os

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "assets", "img", "og.jpg")
SIZE = (1200, 630)


def main():
    with open(os.path.join(DATA, "business.json"), encoding="utf-8") as fh:
        business = json.load(fh)
    with open(os.path.join(DATA, "photos.json"), encoding="utf-8") as fh:
        photos = json.load(fh)

    hero_id = business["photos"]["hero"]
    hero = next(p for p in photos["items"] if p["id"] == hero_id)
    src = os.path.join(ROOT, hero["file"])

    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    img = ImageOps.fit(img, SIZE, method=Image.LANCZOS, centering=(0.55, 0.5))
    img.save(OUT, "JPEG", quality=84, optimize=True, progressive=True)
    print("og.jpg: %d bytes %s" % (os.path.getsize(OUT), SIZE))


if __name__ == "__main__":
    main()
