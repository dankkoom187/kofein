"""Скачивает шрифты с Google Fonts и кладёт локально (woff2 + fonts.css).

    python scripts/fetch_fonts.py

Результат:
    assets/fonts/*.woff2
    assets/css/fonts.css  (@font-face с локальными путями и unicode-range)

Сайт не зависит от внешнего CDN: шрифты отдаются со своего хостинга.
"""
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(ROOT, "assets", "fonts")
CSS_OUT = os.path.join(ROOT, "assets", "css", "fonts.css")

FAMILIES = "family=Prata&family=Manrope:wght@400;500;600;700"
CSS_URL = "https://fonts.googleapis.com/css2?%s&display=swap" % FAMILIES
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    css = fetch(CSS_URL).decode("utf-8")

    blocks = re.findall(r"@font-face\s*\{[^}]+\}", css)
    out = ["/* Шрифты локально: Prata (заголовки) + Manrope (текст). Сгенерировано fetch_fonts.py */", ""]
    downloaded = 0
    for index, block in enumerate(blocks):
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not url:
            continue
        family = (re.search(r"font-family:\s*'([^']+)'", block) or [None, "font"])[1]
        weight = (re.search(r"font-weight:\s*(\d+)", block) or [None, "400"])[1]
        style = (re.search(r"font-style:\s*(\w+)", block) or [None, "normal"])[1]
        subset_comments = re.findall(r"/\*\s*([a-z0-9\-\[\]]+)\s*\*/", css[:css.find(block)])
        subset = subset_comments[-1] if subset_comments else "sub"
        name = "%s-%s-%s-%s-%02d.woff2" % (
            re.sub(r"\W+", "", family.lower()), weight, style,
            re.sub(r"\W+", "", subset) or "sub", index)
        with open(os.path.join(FONTS_DIR, name), "wb") as fh:
            fh.write(fetch(url.group(1)))
        downloaded += 1
        block = block.replace(url.group(1), "../fonts/" + name)
        out.append(block)
        out.append("")

    with open(CSS_OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("fonts: %d files, css %d bytes" % (downloaded, os.path.getsize(CSS_OUT)))
    print("cyrillic ranges:", css.count("U+0400") + css.count("U+04") > 0)


if __name__ == "__main__":
    main()
