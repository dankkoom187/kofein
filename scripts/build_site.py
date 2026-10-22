"""Сборка index.html из шаблона и данных.

    python scripts/build_site.py

Источники:
    templates/index.html   - разметка с плейсхолдерами {{...}}
    data/business.json     - карточка: адрес, часы, телефоны, преимущества
    data/menu.json         - меню по разделам
    data/reviews.json      - отзывы гостей
    data/photos.json       - манифест фотографий (создаётся build_photos.py)
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TEMPLATE = os.path.join(ROOT, "templates", "index.html")
OUT = os.path.join(ROOT, "index.html")

# Фото для первого экрана (стакан с логотипом в руке, на фоне интерьера)
HERO_PHOTO_ID = "2a0000019ea1e83fbd3fe032e4c158cc81ca"

ICONS = {
    "cup": '<path d="M4 8h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8Z"/><path d="M17 9h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M7 3v2.5M11 3v2.5M15 3v2.5"/>',
    "leaf": '<path d="M20 4c-9 0-15 4-15 11 0 3 2 5 5 5 7 0 10-7 10-16Z"/><path d="M5 20c3-5 7-8 12-10"/>',
    "flower": '<path d="M12 8a3 3 0 1 1 0 6 3 3 0 0 1 0-6Z"/><path d="M12 3c1.6 2 1.6 3.5 0 5M12 21c-1.6-2-1.6-3.5 0-5M3 12c2-1.6 3.5-1.6 5 0M21 12c-2 1.6-3.5 1.6-5 0"/>',
    "breakfast": '<path d="M6 3v7a2 2 0 0 0 4 0V3M8 10v11"/><path d="M16 3c2 0 3 2 3 5s-1 4-3 4v9"/>',
    "child": '<circle cx="12" cy="12" r="9"/><path d="M9 10h.01M15 10h.01M8.5 14.5a4.5 4.5 0 0 0 7 0"/>',
    "gift": '<path d="M3 11h18v9H3zM12 11v9"/><path d="M8 7a2 2 0 0 1 4 0 2 2 0 0 1 4 0c0 2-4 4-4 4S8 9 8 7Z"/>',
    "wifi": '<path d="M2 8.5a16 16 0 0 1 20 0M5 12.5a11 11 0 0 1 14 0M8.5 16a6 6 0 0 1 7 0"/><path d="M12 19.5h.01"/>',
    "card": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M2 10.5h20"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.5l3.5 2"/>',
    "phone": '<path d="M6 3h3l2 5-2.5 1.5a12 12 0 0 0 6 6L16 13l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2Z"/>',
    "location": '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
    "telegram": '<path d="M21 4 3 11l5 2 2 6 3-4 5 4 1-13Z"/><path d="M8 13l10-6-8 7"/>',
    "whatsapp": '<path d="M3 21l1.8-5.2A8 8 0 1 1 8 19.2L3 21Z"/><path d="M9 8.5c0 3.5 2.5 6 6 6 .8 0 1.5-.7 1.5-1.4 0-.4-.2-.7-.5-1l-1-.6c-.3-.2-.7-.2-.9.1l-.5.6c-1.3-.6-2.2-1.5-2.8-2.8l.6-.5c.3-.2.3-.6.1-.9l-.6-1c-.3-.4-.6-.5-1-.5H9c-.6 0-1 .4-1 1"/>',
    "route": '<circle cx="6" cy="17" r="2.5"/><circle cx="18" cy="8" r="2.5"/><path d="M8.5 17h6a4 4 0 0 0 0-8H10a3 3 0 0 1 0-6h5.5"/>',
    "award": '<circle cx="12" cy="9" r="5"/><path d="M8.5 13 7 21l5-3 5 3-1.5-8"/>',
    "message": '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-6.4A8 8 0 1 1 21 12Z"/>',
}


def icon(name, size=20):
    path = ICONS.get(name, ICONS["cup"])
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (size, size, path))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def esc(text):
    return html.escape(str(text), quote=True)


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
        note = ('<p class="menu-card__note">%s</p>' % esc(rubric["note"])) if rubric.get("note") else ""
        blocks.append(
            '<article class="menu-card"><div class="menu-card__title"><h3>%s</h3></div>%s'
            '<ul class="menu-list">%s</ul></article>' % (esc(rubric["title"]), note, "".join(items))
        )
    return "\n        ".join(blocks)


def build_features(business):
    blocks = []
    for feature in business["features"]:
        blocks.append(
            '<li class="feature"><span class="feature__icon" aria-hidden="true">%s</span>'
            "<h3>%s</h3><p>%s</p></li>"
            % (icon(feature.get("icon", "cup"), 22), esc(feature["title"]), esc(feature["text"]))
        )
    return "\n        ".join(blocks)


def build_gallery(photos):
    order = {"review": 0, "candidate": 1, "gallery": 2}
    items = sorted(photos["items"], key=lambda p: (order.get(p["group"], 3), p["date"] or "", p["id"]))
    blocks = []
    for photo in items:
        caption = esc(photo["caption"])
        blocks.append(
            '<li><button class="gallery__item" type="button" data-full="%s" data-caption="%s">'
            '<img src="%s" srcset="%s 640w, %s 1400w" sizes="(max-width: 760px) 45vw, 260px" '
            'width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
            "<figcaption>%s</figcaption></button></li>"
            % (esc(photo["file"]), caption, esc(photo["thumb"]), esc(photo["thumb"]), esc(photo["file"]),
               photo["thumbWidth"], photo["thumbHeight"], caption, caption)
        )
    return "\n        ".join(blocks)


def build_reviews(reviews):
    blocks = []
    for review in reviews["items"]:
        stars = "★" * review["rating"] + '<span class="muted">%s</span>' % ("★" * (5 - review["rating"]))
        initial = esc(review["author"][:1].upper())
        blocks.append(
            '<li class="review"><blockquote>«%s»</blockquote>'
            '<div class="review__meta"><span class="review__avatar" aria-hidden="true">%s</span>'
            '<span><span class="review__who">%s</span><br><span class="review__date">%s</span></span>'
            '<span class="review__stars" aria-label="Оценка %d из 5">%s</span></div></li>'
            % (esc(review["text"]), initial, esc(review["author"]), esc(review["date"]), review["rating"], stars)
        )
    return "\n        ".join(blocks)


def build_jsonld(business, menu):
    data = {
        "@context": "https://schema.org",
        "@type": "CafeOrCoffeeShop",
        "name": business["name"],
        "description": business["tagline"],
        "url": business["maps"],
        "image": ["assets/img/photos/%s.jpg" % HERO_PHOTO_ID],
        "telephone": business["phone"],
        "priceRange": business["prices"]["averageBill"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": business["addressShort"],
            "addressLocality": "Москва",
            "postalCode": business["postalCode"],
            "addressCountry": "RU",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": business["geo"]["lat"],
            "longitude": business["geo"]["lon"],
        },
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": business["hours"]["open"],
            "closes": business["hours"]["close"],
        }],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": business["rating"]["value"],
            "reviewCount": business["rating"]["reviews"],
            "bestRating": 5,
        },
        "hasMenu": {
            "@type": "Menu",
            "name": "Меню",
            "hasMenuSection": [{
                "@type": "MenuSection",
                "name": rubric["title"],
                "hasMenuItem": [{
                    "@type": "MenuItem",
                    "name": item["title"],
                    "offers": {"@type": "Offer", "price": item["price"].replace(" ", "").replace("₽", ""),
                               "priceCurrency": "RUB"},
                } for item in rubric["items"]],
            } for rubric in menu["rubrics"]],
        },
    }
    return json.dumps(data, ensure_ascii=False)


def main():
    business = load("business.json")
    menu = load("menu.json")
    reviews = load("reviews.json")
    photos = load("photos.json")

    hero = next((p for p in photos["items"] if p["id"] == HERO_PHOTO_ID), photos["items"][0])

    values = {
        "TITLE": "%s — %s" % (business["name"], business["tagline"]),
        "DESCRIPTION": "%s: %s. %s, ежедневно %s–%s, %s. Средний чек %s." % (
            business["name"], business["tagline"], business["addressShort"],
            business["hours"]["open"], business["hours"]["close"], business["phone"],
            business["prices"]["averageBill"]),
        "NAME": esc(business["name"]),
        "SHORT_TITLE": esc(business["shortName"]),
        "CATEGORIES": esc(", ".join(business["categories"])),
        "EYEBROW": "Кофейня · район Внуково, Москва",
        "BRAND_SUB": "кофейня · район Внуково",
        "TAGLINE": esc(business["tagline"]),
        "PHONE": esc(business["phone"]),
        "PHONE_HREF": esc(business["phoneHref"]),
        "TELEGRAM": esc(business["telegram"]),
        "WHATSAPP": esc(business["whatsapp"]),
        "MAPS_URL": esc(business["maps"]),
        "ROUTE_URL": esc(business["mapsRoute"]),
        "MAP_EMBED": esc(business["mapEmbed"]),
        "ADDRESS": esc(business["address"]),
        "ADDRESS_SHORT": esc(business["addressShort"]),
        "HOURS_OPEN": esc(business["hours"]["open"]),
        "HOURS_CLOSE": esc(business["hours"]["close"]),
        "RATING_VALUE": esc(business["rating"]["value"]),
        "REVIEWS_COUNT": esc(business["rating"]["reviews"]),
        "AVERAGE_BILL": esc(business["prices"]["averageBill"]),
        "BUSINESS_LUNCH": esc(business["prices"]["businessLunch"]),
        "AWARD": esc(business["award"]),
        "PHOTOS_COUNT": esc(len(photos["items"])),
        "PHOTOS_CREDIT": esc(business["photosCredit"]),
        "COPYRIGHT": "© %s" % business["name"],
        "HERO_PHOTO": esc(hero["file"]),
        "HERO_ALT": esc(hero["caption"]),
        "HERO_W": esc(hero["width"]),
        "HERO_H": esc(hero["height"]),
        "MENU": build_menu(menu),
        "FEATURES": build_features(business),
        "GALLERY": build_gallery(photos),
        "REVIEWS": build_reviews(reviews),
        "JSONLD": build_jsonld(business, menu).replace("</", "<\\/"),
        "PHONE_ICON": icon("phone", 18),
        "CLOCK_ICON": icon("clock", 18),
        "LOCATION_ICON": icon("location", 18),
        "MESSAGE_ICON": icon("message", 18),
        "ROUTE_ICON": icon("route", 18),
        "TELEGRAM_ICON": icon("telegram", 18),
        "WHATSAPP_ICON": icon("whatsapp", 18),
        "AWARD_ICON": icon("award", 22),
    }

    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()
    for key, value in values.items():
        page = page.replace("{{%s}}" % key, value)

    left = [token for token in page.split() if token.startswith("{{")]
    if left:
        raise SystemExit("Не подставлены плейсхолдеры: %s" % sorted(set(left)))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("index.html готов: %d байт, фото %d, отзывов %d" % (len(page), len(photos["items"]), len(reviews["items"])))


if __name__ == "__main__":
    main()
