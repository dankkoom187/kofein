"""Собирает каталог цветочной студии и фото букетов.

    python scripts/build_flowers.py

Источники:
    yandex.ru/maps/org/76375131364/menu/     — 151 позиция: название, состав, цена
    yandex.ru/maps/org/76375131364/reviews/  — фото букетов из отзывов

Результат:
    data/flowers.json                     — категории и товары
    assets/img/flowers/<id>.jpg + -thumb  — фото
    data/flowers-photos.json              — манифест фото
"""
import html
import io
import json
import os
import re
import urllib.request

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "assets", "img", "flowers")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
ORG = "76375131364"

TYPE_RULES = [
    ("Свадебные", ("свадеб",)),
    ("Флорариумы", ("флорариум",)),
    ("Корзины", ("корзина",)),
    ("Коробки", ("коробка", "короб")),
    ("Ящики", ("ящик",)),
    ("Букеты", ("букет",)),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def kind(title):
    low = title.lower()
    for name, keys in TYPE_RULES:
        if any(k in low for k in keys):
            return name
    return "Композиции"


def parse_catalog():
    page = get("https://yandex.ru/maps/org/%s/menu/" % ORG)
    heads = [(m.start(), html.unescape(m.group(1)).strip()) for m in
             re.finditer(r'business-full-items-grouped-view__title"[^>]*>([^<]{1,80})<', page)]
    items = []
    for index, (start, group) in enumerate(heads):
        end = heads[index + 1][0] if index + 1 < len(heads) else len(page)
        chunk = page[start:end]
        for m in re.finditer(
                r'related-item-list-view__title" title="([^"]+)">.*?'
                r'related-item-list-view__description" title="([^"]*)"',
                chunk, re.S):
            title = html.unescape(m.group(1)).strip()
            composition = html.unescape(m.group(2)).strip()
            price = chunk[m.end():m.end() + 600]
            price_match = re.search(r'related-item-list-view__price">([\d\s]+)\s*₽', price)
            if not price_match:
                continue
            items.append({
                "title": title,
                "composition": composition,
                "price": int(re.sub(r"\D", "", price_match.group(1))),
                "group": group,
                "kind": kind(title),
            })
    # дедупликация по названию и цене
    seen = set()
    unique = []
    for item in items:
        key = (item["title"], item["price"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def save_img(raw, pid):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    full = os.path.join(IMG, pid + ".jpg")
    thumb = os.path.join(IMG, pid + "-thumb.jpg")
    img.thumbnail((1200, 1200), Image.LANCZOS)
    img.save(full, "JPEG", quality=82, optimize=True, progressive=True)
    img.thumbnail((560, 560), Image.LANCZOS)
    img.save(thumb, "JPEG", quality=80, optimize=True, progressive=True)
    return full, thumb


def parse_photos(limit=30):
    page = get("https://yandex.ru/maps/org/%s/reviews/" % ORG)
    start = page.find('"reviews":[{')
    if start == -1:
        return []
    arr_start = page.find("[", start)
    depth = 0
    in_str = False
    esc = False
    end = -1
    for pos in range(arr_start, len(page)):
        ch = page[pos]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    try:
        reviews = json.loads(page[arr_start:end])
    except Exception:  # noqa: BLE001
        return []

    photos = []
    seen = set()
    for review in reviews:
        author = (review.get("author") or {}).get("name", "")
        date = (review.get("updatedTime") or "")[:10]
        for photo in review.get("photos") or []:
            url = photo.get("urlTemplate", "").replace("{size}", "orig")
            pid = url.rstrip("/").split("/")[-2] + "_" + url.rstrip("/").split("/")[-1]
            if not url or pid in seen:
                continue
            seen.add(pid)
            photos.append({"id": pid, "url": url, "author": author, "date": date})
            if len(photos) >= limit:
                return photos
    return photos


def main():
    os.makedirs(IMG, exist_ok=True)
    items = parse_catalog()
    with open(os.path.join(DATA, "flowers.json"), "w", encoding="utf-8") as fh:
        json.dump({"org": ORG, "items": items}, fh, ensure_ascii=False, indent=1)
    print("catalog: %d items" % len(items))

    photos = parse_photos()
    manifest = []
    for photo in photos:
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(photo["url"], headers={"User-Agent": UA}), timeout=60).read()
            full, thumb = save_img(raw, photo["id"])
        except Exception as exc:  # noqa: BLE001
            print("skip", photo["id"], exc)
            continue
        manifest.append({
            "file": os.path.relpath(full, ROOT).replace("\\", "/"),
            "thumb": os.path.relpath(thumb, ROOT).replace("\\", "/"),
            "caption": ("Фото из отзыва %s, %s" % (photo["author"], photo["date"])) if photo["author"]
                       else "Фото студии",
        })
    with open(os.path.join(DATA, "flowers-photos.json"), "w", encoding="utf-8") as fh:
        json.dump({"items": manifest}, fh, ensure_ascii=False, indent=1)
    print("photos: %d" % len(manifest))


if __name__ == "__main__":
    main()
