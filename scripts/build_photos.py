"""Сборка фотографий сайта: скачивание, ресайз, манифест.

Запуск:
    python scripts/build_photos.py [--groups review,candidate,gallery]

Источники:
    data/photos-source.csv        - ссылки из карточки Яндекс Карт (group, url)
    data/reviews-photos-source.csv - автор/дата/оценка для фото из отзывов

Результат:
    assets/img/photos/<id>.jpg        - полный размер (не длиннее 1400 px)
    assets/img/photos/<id>-thumb.jpg  - превью (не длиннее 640 px)
    data/photos.json                  - манифест для сайта
"""
import argparse
import csv
import json
import os
import sys
import urllib.request

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "assets", "img", "photos")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

FULL_MAX = 1400
THUMB_MAX = 640
QUALITY = 82

CAPTIONS = {
    "review": "Фото из отзыва на Яндекс Картах",
    "candidate": "Фото гостей кофейни — подборка карточки на Яндекс Картах",
    "gallery": "Фото кофейни — фотогалерея карточки на Яндекс Картах",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh, delimiter=";"))
    head = rows[0]
    return head, [dict(zip(head, r)) for r in rows[1:] if len(r) == len(head)]


def load_sources():
    head, photos = read_csv(os.path.join(DATA, "photos-source.csv"))
    _, revs = read_csv(os.path.join(DATA, "reviews-photos-source.csv"))
    meta = {}
    for r in revs:
        # связываем по ссылке: id в отзывах у части фото не совпадает с id в карточке
        meta[r["url_orig"]] = r
    return photos, meta


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def save_jpeg(img, path, max_side):
    img = ImageOps.exif_transpose(img)
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return img.size


def build(groups):
    photos, rev_meta = load_sources()
    os.makedirs(IMG, exist_ok=True)
    manifest = []
    skipped = []
    for row in photos:
        group = row.get("group", "")
        if group not in groups:
            continue
        pid = row["photo_id"]
        url = row.get("url_orig") or row.get("url_XXXL")
        try:
            raw = fetch(url)
            img = Image.open(__import__("io").BytesIO(raw))
            full_path = os.path.join(IMG, pid + ".jpg")
            thumb_path = os.path.join(IMG, pid + "-thumb.jpg")
            fw, fh = save_jpeg(img, full_path, FULL_MAX)
            tw, th = save_jpeg(img, thumb_path, THUMB_MAX)
        except Exception as exc:  # noqa: BLE001
            skipped.append("%s: %s" % (pid, exc))
            continue
        rv = rev_meta.get(row.get("url_orig"), {})
        caption = CAPTIONS.get(group, CAPTIONS["gallery"])
        author = rv.get("author", "")
        date = rv.get("date", "")
        if author:
            caption = "Фото из отзыва %s%s" % (author, ", " + date if date else "")
        manifest.append({
            "id": pid,
            "group": group,
            "file": "assets/img/photos/%s.jpg" % pid,
            "thumb": "assets/img/photos/%s-thumb.jpg" % pid,
            "width": fw,
            "height": fh,
            "thumbWidth": tw,
            "thumbHeight": th,
            "author": author,
            "date": date,
            "rating": rv.get("rating", ""),
            "caption": caption,
            "source": url,
        })
    manifest.sort(key=lambda p: (p["group"] != "gallery", p["date"] or "0000", p["id"]))
    with open(os.path.join(DATA, "photos.json"), "w", encoding="utf-8") as fh:
        json.dump({"items": manifest}, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA, "photos-build.log"), "w", encoding="utf-8") as fh:
        fh.write("ok=%d skipped=%d\n" % (len(manifest), len(skipped)))
        fh.write("\n".join(skipped))
    print("photos ok=%d skipped=%d" % (len(manifest), len(skipped)))
    for s in skipped:
        print("  skip", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", default="review,candidate,gallery")
    args = ap.parse_args()
    build(set(g.strip() for g in args.groups.split(",") if g.strip()))


if __name__ == "__main__":
    sys.exit(main())
