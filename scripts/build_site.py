"""Сборка index.html из шаблона и данных.

    python scripts/build_site.py

Источники:
    templates/index.html   - разметка с плейсхолдерами {{...}}
    data/business.json     - карточка, тексты секций, ссылки
    data/menu.json         - меню кофейни
    data/reviews.json      - отзывы гостей
    data/photos.json       - манифест фото кофейни
    data/flowers.json      - каталог цветочной студии
    data/flowers-photos.json - фото букетов
"""
import html
import json
import os
import re
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TEMPLATE = os.path.join(ROOT, "templates", "index.html")
OUT = os.path.join(ROOT, "index.html")

VISIBLE_ITEMS = 9

ICONS = {
    "phone": '<path d="M6 3h3l2 5-2.5 1.5a12 12 0 0 0 6 6L16 13l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2Z"/>',
    "route": '<circle cx="6" cy="17" r="2.5"/><circle cx="18" cy="8" r="2.5"/>'
             '<path d="M8.5 17h6a4 4 0 0 0 0-8H10a3 3 0 0 1 0-6h5.5"/>',
}


def icon(name, size=16):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (size, size, ICONS[name]))


def load(name):
    path = os.path.join(DATA, name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def esc(text):
    return html.escape(str(text), quote=True)


def money(value):
    return "{:,}".format(int(value)).replace(",", "\u00a0") + "\u00a0₽"


def nice_quotes(text):
    out = []
    opened = False
    for ch in text:
        if ch == '"':
            out.append("«" if not opened else "»")
            opened = not opened
        else:
            out.append(ch)
    return "".join(out)


def composition(text):
    text = re.sub(r"\s*\n\s*", ", ", text or "")
    text = re.sub(r"\s+", " ", text).strip(" ,")
    if text:
        text = text[0].upper() + text[1:]
    return text


def photo(photos, pid, fallback_group="gallery"):
    for item in photos["items"]:
        if item["id"] == pid:
            return item
    return next((p for p in photos["items"] if p["group"] == fallback_group), photos["items"][0])


def build_menu(menu):
    blocks = []
    for rubric in menu["rubrics"]:
        items = []
        for item in rubric["items"]:
            volume = ('<span class="menu-item__volume">%s</span>' % esc(item["volume"])) if item.get("volume") else ""
            items.append(
                '<li class="menu-item"><span class="menu-item__name">%s%s</span>'
                '<span class="menu-item__dots" aria-hidden="true"></span>'
                '<span class="menu-item__price">%s</span></li>'
                % (esc(item["title"]), volume, esc(item["price"]))
            )
        note = ('<p class="menu-group__note">%s</p>' % esc(rubric["note"])) if rubric.get("note") else ""
        blocks.append(
            '<section class="menu-group"><h3 class="menu-group__title">%s</h3>%s'
            '<ul class="menu-list">%s</ul></section>' % (esc(rubric["title"]), note, "".join(items))
        )
    return "\n          ".join(blocks)


def build_gallery(photos):
    gallery = sorted([p for p in photos["items"] if p["group"] == "gallery"], key=lambda p: p["id"])
    reviews = sorted([p for p in photos["items"] if p["group"] in ("review", "candidate")],
                     key=lambda p: (p["date"] or "", p["id"]), reverse=True)
    others = [p for p in photos["items"] if p["group"] not in ("gallery", "review", "candidate")]
    items = gallery + reviews + others
    blocks = []
    for item in items:
        caption = esc(item["caption"])
        blocks.append(
            '<li><button class="gallery__item" type="button" data-full="%s" data-caption="%s">'
            '<img src="%s" srcset="%s 640w, %s 1400w" sizes="(max-width: 560px) 46vw, '
            '(max-width: 1080px) 31vw, 24vw" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
            "<figcaption>%s</figcaption></button></li>"
            % (esc(item["file"]), caption, esc(item["thumb"]), esc(item["thumb"]), esc(item["file"]),
               item["width"], item["height"], caption, caption)
        )
    return "\n          ".join(blocks)


def build_flowers_gallery(photos, ids=None, limit=8):
    by_id = {os.path.basename(p["file"]).replace(".jpg", ""): p for p in photos["items"]}
    chosen = [by_id[i] for i in ids if i in by_id] if ids else []
    if not chosen:
        chosen = photos["items"][:limit]
    blocks = []
    for item in chosen:
        caption = esc(item["caption"])
        blocks.append(
            '<li><button class="gallery__item gallery__item--flower" type="button" '
            'data-full="%s" data-caption="%s">'
            '<img src="%s" srcset="%s 560w, %s 1200w" sizes="(max-width: 560px) 31vw, 16vw" '
            'width="560" height="747" alt="%s" loading="lazy" decoding="async">'
            "<figcaption>%s</figcaption></button></li>"
            % (esc(item["file"]), caption, esc(item["thumb"]), esc(item["thumb"]), esc(item["file"]),
               caption, caption)
        )
    return "\n          ".join(blocks)


def build_flowers(items, flowers):
    order = ["Букеты", "Корзины", "Коробки", "Ящики", "Композиции"]
    counts = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1

    chips = ['<button class="chip is-active" type="button" data-kind="all" aria-pressed="true">'
             'Все<span>%d</span></button>' % len(items)]
    for kind in order:
        if counts.get(kind):
            chips.append('<button class="chip" type="button" data-kind="%s" aria-pressed="false">%s<span>%d</span></button>'
                         % (esc(kind), esc(kind), counts[kind]))

    sorted_items = sorted(items, key=lambda i: (order.index(i["kind"]) if i["kind"] in order else 9, i["price"]))
    blocks = []
    for index, item in enumerate(sorted_items):
        title = nice_quotes(item["title"])
        price = money(item["price"])
        text = "Здравствуйте! Хочу заказать: %s, %s." % (title, price)
        link = flowers["whatsapp"] + "?text=" + quote(text)
        hidden = " hidden" if index >= VISIBLE_ITEMS else ""
        blocks.append(
            '<li class="product"%s data-kind="%s">'
            '<div class="product__row"><h3 class="product__title">%s</h3>'
            '<span class="product__price">%s</span></div>'
            '<p class="product__composition">%s</p>'
            '<a class="product__order" href="%s" target="_blank" rel="noopener">Заказать<span aria-hidden="true">→</span></a>'
            "</li>"
            % (hidden, esc(item["kind"]), esc(title), esc(price),
               esc(composition(item.get("composition", ""))), esc(link))
        )
    return "\n            ".join(chips), "\n          ".join(blocks)


def build_reviews(reviews):
    blocks = []
    for review in reviews["items"]:
        stars = "★" * review["rating"] + ('<span class="muted">%s</span>' % ("★" * (5 - review["rating"])))
        blocks.append(
            '<article class="review"><blockquote>«%s»</blockquote>'
            '<footer class="review__meta"><span class="review__author">%s</span>'
            '<span class="review__date">%s</span>'
            '<span class="review__stars" aria-label="Оценка %d из 5">%s</span></footer></article>'
            % (esc(review["text"]), esc(review["author"]), esc(review["date"]), review["rating"], stars)
        )
    return "\n        ".join(blocks)


def build_steps(steps):
    blocks = []
    for index, step in enumerate(steps, 1):
        blocks.append(
            '<li class="step"><span class="step__num" aria-hidden="true">%02d</span>'
            "<h3>%s</h3><p>%s</p></li>" % (index, esc(step["title"]), esc(step["text"]))
        )
    return "\n        ".join(blocks)


def build_jsonld(business, menu):
    coffee = {
        "@type": "CafeOrCoffeeShop",
        "name": business["name"],
        "url": business["maps"],
        "telephone": business["phone"],
        "priceRange": business["prices"]["averageBill"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": business["addressShort"],
            "addressLocality": "Москва",
            "postalCode": business["postalCode"],
            "addressCountry": "RU",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": business["geo"]["lat"], "longitude": business["geo"]["lon"]},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": business["hours"]["open"],
            "closes": business["hours"]["close"],
        }],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": business["rating"]["value"].replace(",", "."),
            "reviewCount": business["rating"]["reviews"],
            "bestRating": 5,
        },
        "hasMenu": {
            "@type": "Menu",
            "hasMenuSection": [{
                "@type": "MenuSection",
                "name": rubric["title"],
                "hasMenuItem": [{
                    "@type": "MenuItem",
                    "name": item["title"],
                    "offers": {"@type": "Offer",
                               "price": item["price"].replace(" ", "").replace("₽", ""),
                               "priceCurrency": "RUB"},
                } for item in rubric["items"]],
            } for rubric in menu["rubrics"]],
        },
    }

    flowers = business["flowers"]
    florist = {
        "@type": "Florist",
        "name": flowers["name"],
        "description": flowers["tagline"],
        "url": flowers["maps"],
        "telephone": flowers["phone"],
        "priceRange": "₽₽",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": business["addressShort"],
            "addressLocality": "Москва",
            "postalCode": business["postalCode"],
            "addressCountry": "RU",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": business["geo"]["lat"], "longitude": business["geo"]["lon"]},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": business["hours"]["open"],
            "closes": business["hours"]["close"],
        }],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": flowers["rating"]["value"].replace(",", "."),
            "reviewCount": flowers["rating"]["reviews"],
            "bestRating": 5,
        },
    }

    return json.dumps({"@context": "https://schema.org", "@graph": [coffee, florist]}, ensure_ascii=False)


def main():
    business = load("business.json")
    menu = load("menu.json")
    reviews = load("reviews.json")
    photos = load("photos.json")
    flowers_data = load("flowers.json")
    flowers_photos = load("flowers-photos.json")

    hero = photo(photos, business["photos"]["hero"], "review")
    intro_main = photo(photos, business["photos"]["introMain"])
    intro_small = photo(photos, business["photos"]["introSmall"])
    menu_photo = photo(photos, business["photos"]["menu"], "review")

    flowers = business["flowers"]
    chips_html, items_html = build_flowers(flowers_data["items"], flowers)

    description = ("%s и цветочная студия %s: %s, ежедневно %s–%s, %s. Кофе, букеты, доставка." % (
        business["name"], flowers["name"], business["addressShort"],
        business["hours"]["open"], business["hours"]["close"], business["phone"]))

    site_url = (business.get("site") or {}).get("url", "").strip()
    og_image = (site_url.rstrip("/") + "/" if site_url else "") + "assets/img/og.jpg"

    values = {
        "TITLE": "%s и %s — кофейня и цветы на Бориса Пастернака" % (business["name"], flowers["name"]),
        "DESCRIPTION": esc(description),
        "NAME": esc(business["name"]),
        "OG_IMAGE": esc(og_image),
        "OG_ALT": esc("Кофеin — кофейня и цветы на Бориса Пастернака, 43"),
        "OG_URL_TAG": ('<meta property="og:url" content="%s">' % esc(site_url)) if site_url else "",
        "CANONICAL": ('<link rel="canonical" href="%s">' % esc(site_url)) if site_url else "",
        "SHORT_NAME": esc(business["shortName"]),
        "BRAND_SUB": "кофейня · Внуково",
        "EYEBROW": esc(business["hero"]["eyebrow"]),
        "SUBTITLE": esc(business["hero"]["subtitle"]),
        "LEAD": esc(business["hero"]["lead"]),
        "PHONE": esc(business["phone"]),
        "PHONE_HREF": esc(business["phoneHref"]),
        "TELEGRAM": esc(business["telegram"]),
        "WHATSAPP": esc(business["whatsapp"]),
        "MAPS_URL": esc(business["maps"]),
        "ROUTE_URL": esc(business["mapsRoute"]),
        "MAP_EMBED": esc(business["mapEmbed"]),
        "ADDRESS": esc(business["address"]),
        "ADDRESS_SHORT": esc(business["addressShort"]),
        "RATING": esc(business["rating"]["value"]),
        "REVIEWS_COUNT": esc(business["rating"]["reviews"]),
        "AVERAGE_BILL": esc(business["prices"]["averageBill"]),
        "MARQUEE": "".join('<span class="marquee__item">%s</span>' % esc(x) for x in business["marquee"]),
        "INTRO_LABEL": esc(business["intro"]["label"]),
        "INTRO_TITLE": esc(business["intro"]["title"]),
        "INTRO_BODY": "".join("<p>%s</p>" % esc(p) for p in business["intro"]["body"]),
        "STATS": "".join('<li><strong>%s</strong><span>%s</span></li>' % (esc(s["value"]), esc(s["label"]))
                         for s in business["intro"]["stats"]),
        "FEATURES_LIST": "".join("<li>%s</li>" % esc(f) for f in business["intro"]["features"]),
        "INTRO_MAIN": esc(intro_main["file"]),
        "INTRO_MAIN_ALT": esc(intro_main["caption"]),
        "INTRO_MAIN_W": intro_main["width"],
        "INTRO_MAIN_H": intro_main["height"],
        "INTRO_SMALL": esc(intro_small["file"]),
        "INTRO_SMALL_ALT": esc(intro_small["caption"]),
        "INTRO_SMALL_W": intro_small["width"],
        "INTRO_SMALL_H": intro_small["height"],
        "INTRO_CAPTION": esc(business["menuSection"]["asideCaption"]),
        "MENU_LABEL": esc(business["menuSection"]["label"]),
        "MENU_TITLE": esc(business["menuSection"]["title"]),
        "MENU_NOTE": esc(business["menuSection"]["note"]),
        "MENU_HTML": build_menu(menu),
        "MENU_PHOTO": esc(menu_photo["file"]),
        "MENU_PHOTO_ALT": esc(menu_photo["caption"]),
        "MENU_PHOTO_W": menu_photo["width"],
        "MENU_PHOTO_H": menu_photo["height"],
        "MENU_CAPTION": esc(business["menuSection"]["asideCaption"]),
        "GALLERY_LABEL": esc(business["gallerySection"]["label"]),
        "GALLERY_TITLE": esc(business["gallerySection"]["title"]),
        "GALLERY_NOTE": esc(business["gallerySection"]["note"]),
        "GALLERY_HTML": build_gallery(photos),
        "PHOTOS_COUNT": len(photos["items"]),
        "FLOWERS_LABEL": esc(flowers["section"]["label"]),
        "FLOWERS_TITLE": esc(flowers["section"]["title"]),
        "FLOWERS_NOTE": esc(flowers["section"]["note"]),
        "FLOWERS_RATING": esc(flowers["rating"]["value"]),
        "FLOWERS_REVIEWS": esc(flowers["rating"]["reviews"]),
        "FLOWERS_NAME": esc(flowers["name"]),
        "FLOWERS_PHONE": esc(flowers["phone"]),
        "FLOWERS_PHONE_HREF": esc(flowers["phoneHref"]),
        "FLOWERS_WA": esc(flowers["whatsapp"]),
        "FLOWERS_TG": esc(flowers["telegram"]),
        "FLOWERS_VK": esc(flowers["vk"]),
        "FLOWERS_DZEN": esc(flowers["dzen"]),
        "FLOWERS_MAPS": esc(flowers["maps"]),
        "FLOWERS_GALLERY": build_flowers_gallery(flowers_photos, flowers.get("gallery")),
        "FLOWERS_CHIPS": chips_html,
        "FLOWERS_ITEMS": items_html,
        "FLOWERS_CATALOG_NOTE": esc(flowers["catalogNote"]),
        "REVIEWS_LABEL": esc(business["reviewsSection"]["label"]),
        "REVIEWS_TITLE": esc(business["reviewsSection"]["title"]),
        "REVIEWS_LINK": esc(business["reviewsSection"]["linkText"]),
        "REVIEWS_HTML": build_reviews(reviews),
        "ORDER_LABEL": esc(business["orderSection"]["label"]),
        "ORDER_TITLE": esc(business["orderSection"]["title"]),
        "ORDER_NOTE": esc(business["orderSection"]["note"]),
        "STEPS": build_steps(business["orderSection"]["steps"]),
        "CONTACTS_LABEL": esc(business["contactsSection"]["label"]),
        "CONTACTS_TITLE": esc(business["contactsSection"]["title"]),
        "CONTACTS_NOTE": esc(business["contactsSection"]["note"]),
        "PHOTOS_CREDIT": esc(business["photosCredit"]),
        "COPYRIGHT": "© %s" % esc(business["name"]),
        "HERO_PHOTO": esc(hero["file"]),
        "HERO_ALT": esc(hero["caption"]),
        "HERO_W": hero["width"],
        "HERO_H": hero["height"],
        "JSONLD": build_jsonld(business, menu).replace("</", "<\\/"),
        "ICON_PHONE": icon("phone"),
        "ICON_ROUTE": icon("route"),
    }

    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()
    for key, value in values.items():
        page = page.replace("{{%s}}" % key, str(value))

    left = sorted({token[2:].split("}}")[0] for token in page.split() if token.startswith("{{")})
    if left:
        raise SystemExit("Не подставлены плейсхолдеры: %s" % left)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("index.html: %d bytes, coffee photos %d, reviews %d, flowers %d, flower photos %d"
          % (len(page), len(photos["items"]), len(reviews["items"]),
             len(flowers_data["items"]), len(flowers_photos["items"])))


if __name__ == "__main__":
    main()
