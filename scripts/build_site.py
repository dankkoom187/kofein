"""Сборка index.html из шаблона и данных.

    python scripts/build_site.py

Источники:
    templates/index.html   - разметка с плейсхолдерами {{...}}
    data/business.json     - карточка, тексты секций, ссылки
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

ICONS = {
    "phone": '<path d="M6 3h3l2 5-2.5 1.5a12 12 0 0 0 6 6L16 13l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2Z"/>',
    "route": '<circle cx="6" cy="17" r="2.5"/><circle cx="18" cy="8" r="2.5"/>'
             '<path d="M8.5 17h6a4 4 0 0 0 0-8H10a3 3 0 0 1 0-6h5.5"/>',
    "arrow": '<path d="M4 12h15M13 6l6 6-6 6"/>',
}


def icon(name, size=16):
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (size, size, ICONS[name]))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def esc(text):
    return html.escape(str(text), quote=True)


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
    # сначала фото места, затем снимки гостей — от новых к старым
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
    data = {
        "@context": "https://schema.org",
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
                    "offers": {
                        "@type": "Offer",
                        "price": item["price"].replace(" ", "").replace("₽", ""),
                        "priceCurrency": "RUB",
                    },
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

    hero = photo(photos, business["photos"]["hero"], "review")
    intro_main = photo(photos, business["photos"]["introMain"])
    intro_small = photo(photos, business["photos"]["introSmall"])
    menu_photo = photo(photos, business["photos"]["menu"], "review")

    description = ("%s: %s. %s, ежедневно %s–%s, %s. Средний чек %s." % (
        business["name"], business["hero"]["subtitle"], business["addressShort"],
        business["hours"]["open"], business["hours"]["close"], business["phone"],
        business["prices"]["averageBill"]))

    values = {
        "TITLE": "%s — %s" % (business["name"], business["hero"]["subtitle"]),
        "DESCRIPTION": esc(description),
        "OG_IMAGE": esc(hero["file"]),
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
    print("index.html: %d bytes, photos %d, reviews %d" % (len(page), len(photos["items"]), len(reviews["items"])))


if __name__ == "__main__":
    main()
