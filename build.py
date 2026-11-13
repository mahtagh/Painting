#!/usr/bin/env python3
"""Build the painting website.

    python3 build.py

Reads paintings.json and the photos in originals/, and writes the finished
static site into docs/ (ready for GitHub Pages: Settings > Pages > Deploy from
branch > /docs). Needs Pillow:  pip install pillow
"""
import json, shutil, datetime
from html import escape
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
SIZES = {"large": 1600, "thumb": 800}
STATUS_TEXT = {"available": "Available", "reserved": "Reserved", "sold": "Sold"}

data = json.loads((ROOT / "paintings.json").read_text(encoding="utf-8"))
S = data["site"]
P = data["paintings"]
BASE = S["site_url"].rstrip("/")
ARTIST = S["artist"]
CUR = S.get("currency", "CAD")
TODAY = datetime.date.today().isoformat()


def e(x):
    return escape(str(x), quote=True)


def money(n):
    return f"${n:,.0f} {CUR}" if float(n).is_integer() else f"${n:,.2f} {CUR}"


def size_text(p):
    h, w = p["height_in"], p["width_in"]
    return f"{h:g} × {w:g} in ({round(h*2.54)} × {round(w*2.54)} cm)"


def mailto(subject):
    return f"mailto:{S['email']}?subject={quote(subject)}"


# ---------- images: resize, fix phone rotation, strip location metadata ----------
def process_images():
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    for p in P:
        src = ROOT / "originals" / p["image"]
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        p["dims"] = {}
        for key, px in SIZES.items():
            copy = im.copy()
            copy.thumbnail((px, px), Image.LANCZOS)
            name = f"{p['slug']}-{px}.jpg"
            # saving without exif= drops GPS and camera data from phone photos
            copy.save(OUT / "images" / name, "JPEG", quality=84, optimize=True, progressive=True)
            p["dims"][key] = (name, copy.width, copy.height)


def img_tag(p, prefix, size="thumb", eager=False, sizes="(min-width: 900px) 33vw, 100vw"):
    t_name, tw, th = p["dims"]["thumb"]
    l_name, lw, lh = p["dims"]["large"]
    src = t_name if size == "thumb" else l_name
    w, h = (tw, th) if size == "thumb" else (lw, lh)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{prefix}images/{src}" srcset="{prefix}images/{t_name} {tw}w, {prefix}images/{l_name} {lw}w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{e(p["alt"])}" {load} decoding="async">')


# ---------- shared page frame ----------
def page(*, title, description, path, prefix, body, og_image, jsonld, og_type="website"):
    url = f"{BASE}/{path}"
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in jsonld)
    insta = (f'<a href="{e(S["instagram"])}" rel="me">Instagram</a>' if S.get("instagram") else "")
    return f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(ARTIST)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(BASE + '/images/' + og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.region" content="{e(S['country'])}-AB">
<meta name="geo.placename" content="{e(S['city'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&family=Young+Serif&display=swap">
<link rel="stylesheet" href="{prefix}styles.css">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="mark" href="{prefix}index.html">{e(ARTIST)}</a>
  <nav aria-label="Main">
    <a href="{prefix}index.html#paintings">Paintings</a>
    <a href="{prefix}index.html#about">About</a>
    <a href="{prefix}index.html#commissions">Commissions</a>
    <a href="{prefix}index.html#contact">Contact</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <p>Original paintings by {e(ARTIST)}, {e(S['city'])}, {e(S['region'])}.</p>
  <p><a href="{mailto('Hello')}">{e(S['email'])}</a> {insta}</p>
  <p>© {datetime.date.today().year} {e(ARTIST)}. Images may not be reproduced without permission.</p>
</footer>
</body>
</html>
"""


def person_ld():
    d = {"@type": "Person", "@id": f"{BASE}/#artist", "name": ARTIST, "jobTitle": "Painter", "url": f"{BASE}/",
         "address": {"@type": "PostalAddress", "addressLocality": S["city"], "addressRegion": S["region"], "addressCountry": S["country"]}}
    if S.get("instagram"):
        d["sameAs"] = [S["instagram"]]
    return d


def label(p, prefix, heading="h3"):
    """The wall label (tombstone) that sits under each painting."""
    st = p["status"]
    if st == "sold":
        price = '<span class="dot" aria-hidden="true"></span>Sold'
    elif st == "reserved":
        price = '<span class="dot dot--ring" aria-hidden="true"></span>Reserved'
    else:
        price = money(p["price"])
    return (f'<{heading} class="t"><a href="{prefix}paintings/{p["slug"]}.html">{e(p["title"])}</a></{heading}>'
            f'<p class="m">{p["year"]}. {e(p["medium"])}<br>{size_text(p)}</p>'
            f'<p class="price price--{st}">{price}</p>')


# ---------- home page ----------
def build_home():
    feat = next((p for p in P if p.get("featured")), P[0])
    rest = [p for p in P if p is not feat] if any(p.get("featured") for p in P) else P[1:]
    widest = max(p["width_in"] for p in P)
    # hang each painting at a width relative to its real size, so an 8-inch study reads smaller than a 32-inch canvas
    scale = lambda p: round(max(0.45, (p["width_in"] / widest) ** 0.6), 3)
    wall = "\n".join(f'<figure class="work" style="--scale:{scale(p)}">\n<a class="frame" href="paintings/{p["slug"]}.html" tabindex="-1" aria-hidden="true">{img_tag(p, "")}</a>\n'
                     f'<figcaption class="tag">{label(p, "")}</figcaption>\n</figure>' for p in [feat] + rest)
    n_avail = sum(p["status"] == "available" for p in P)
    about = "".join(f"<p>{e(x)}</p>" for x in S["about"])
    insta = f'<li>Instagram: <a href="{e(S["instagram"])}" rel="me">{e(S["instagram"])}</a></li>' if S.get("instagram") else ""
    body = f"""
<section class="hero">
  <div class="hero-text">
    <h1>{e(ARTIST)}</h1>
    <p class="lede">{e(S['intro'])}</p>
    <p class="count"><a href="#paintings">{n_avail} of {len(P)} paintings available</a></p>
  </div>
  <figure class="hero-work">
    <a class="frame" href="paintings/{feat['slug']}.html" tabindex="-1" aria-hidden="true">{img_tag(feat, '', size='large', eager=True, sizes='(min-width: 900px) 60vw, 100vw')}</a>
    <figcaption class="tag tag--card">{label(feat, '', 'h2')}</figcaption>
  </figure>
</section>

<section id="paintings" class="wall" aria-labelledby="paintings-h">
  <h2 id="paintings-h">Paintings</h2>
  <p class="note">Each painting is shown at its size relative to the others. A red dot means it has sold.</p>
  <div class="hang">
{wall}
  </div>
</section>

<section id="about" class="prose" aria-labelledby="about-h">
  <h2 id="about-h">About</h2>
  {about}
</section>

<section id="commissions" class="prose" aria-labelledby="comm-h">
  <h2 id="comm-h">Commissions</h2>
  <p>{e(S['commissions'])}</p>
  <p><a class="btn btn--quiet" href="{mailto('Commission request')}">Ask about a commission</a></p>
</section>

<section id="contact" class="prose" aria-labelledby="contact-h">
  <h2 id="contact-h">Contact</h2>
  <ul class="plain">
    <li>Email: <a href="{mailto('Hello')}">{e(S['email'])}</a></li>
    {insta}
    <li>Based in {e(S['city'])}, {e(S['region'])}.</li>
  </ul>
</section>
"""
    item_list = {"@context": "https://schema.org", "@type": "ItemList", "name": f"Paintings by {ARTIST}",
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/paintings/{p['slug']}.html", "name": p["title"]} for i, p in enumerate(P)]}
    site_ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{BASE}/#site", "url": f"{BASE}/", "name": f"{ARTIST} Paintings", "publisher": {"@id": f"{BASE}/#artist"}},
        person_ld()]}
    html = page(title=f"{ARTIST} | Original paintings for sale, {S['city']} artist",
                description=S.get("home_description") or f"Original paintings by {S['city']} artist {ARTIST}. Buy online, shipped across Canada.",
                path="", prefix="", body=body, og_image=feat["dims"]["large"][0], jsonld=[site_ld, item_list])
    (OUT / "index.html").write_text(html, encoding="utf-8")


# ---------- one page per painting ----------
def cta(p):
    st, t = p["status"], p["title"]
    if st == "available" and p.get("stripe_link"):
        return (f'<a class="btn" href="{e(p["stripe_link"])}">Buy this painting for {money(p["price"])}</a>'
                f'<p class="small">Secure checkout by Stripe. Card, Apple Pay and Google Pay accepted.</p>'
                f'<p><a href="{mailto("Question about " + t)}">Ask a question about this painting</a></p>')
    if st == "available":
        return (f'<a class="btn" href="{mailto("I would like to buy " + t)}">Email to buy this painting</a>'
                f'<p class="small">Send a quick email and I\'ll reply with a payment link and shipping options. Email: {e(S["email"])}</p>')
    if st == "reserved":
        return (f'<p class="status"><span class="dot dot--ring" aria-hidden="true"></span>Reserved for a buyer</p>'
                f'<p><a class="btn btn--quiet" href="{mailto("Waitlist: " + t)}">Tell me if it becomes available</a></p>')
    return (f'<p class="status"><span class="dot" aria-hidden="true"></span>Sold</p>'
            f'<p><a class="btn btn--quiet" href="{mailto("Commission like " + t)}">Ask about a similar commission</a></p>')


def build_paintings():
    (OUT / "paintings").mkdir(parents=True, exist_ok=True)
    avail = {"available": "https://schema.org/InStock", "reserved": "https://schema.org/LimitedAvailability",
             "sold": "https://schema.org/SoldOut"}
    for i, p in enumerate(P):
        prev_p, next_p = P[i - 1], P[(i + 1) % len(P)]
        url = f"{BASE}/paintings/{p['slug']}.html"
        large = p["dims"]["large"][0]
        buying = "".join(f"<li>{e(x)}</li>" for x in S["buying"])
        body = f"""
<nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html#paintings">Paintings</a> / <span aria-current="page">{e(p['title'])}</span></nav>
<article class="piece">
  <figure class="piece-work">
    <div class="frame">{img_tag(p, '../', size='large', eager=True, sizes='(min-width: 900px) 62vw, 100vw')}</div>
  </figure>
  <div class="piece-info">
    <h1>{e(p['title'])}</h1>
    <p class="m">{p['year']}. {e(p['medium'])}<br>{size_text(p)}</p>
    <p class="desc">{e(p['description'])}</p>
    {'<p class="big-price">' + money(p['price']) + '</p>' if p['status'] == 'available' else ''}
    {cta(p)}
    <h2 class="sub">Buying and delivery</h2>
    <ul class="plain small">{buying}</ul>
  </div>
</article>
<nav class="pager" aria-label="More paintings">
  <a href="{prev_p['slug']}.html">Previous: {e(prev_p['title'])}</a>
  <a href="{next_p['slug']}.html">Next: {e(next_p['title'])}</a>
</nav>
"""
        offer = {"@type": "Offer", "url": url, "price": p["price"], "priceCurrency": CUR,
                 "availability": avail[p["status"]], "itemCondition": "https://schema.org/NewCondition",
                 "seller": {"@id": f"{BASE}/#artist"}}
        product = {"@context": "https://schema.org", "@type": ["Product", "VisualArtwork"], "@id": url + "#painting",
                   "name": p["title"], "description": p["description"], "image": [f"{BASE}/images/{large}"],
                   "sku": p["slug"], "brand": {"@type": "Brand", "name": ARTIST},
                   "creator": person_ld(), "dateCreated": str(p["year"]), "artform": "Painting",
                   "artMedium": p["medium"].split(" on ")[0], "artworkSurface": p["medium"].split(" on ")[-1],
                   "height": {"@type": "Distance", "name": f"{p['height_in']} in"},
                   "width": {"@type": "Distance", "name": f"{p['width_in']} in"},
                   "offers": offer}
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Paintings", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": p["title"], "item": url}]}
        state = {"available": f"{money(p['price'])}.", "reserved": "Reserved.", "sold": "Sold."}[p["status"]]
        desc = f"{p['title']} ({p['year']}), original {p['medium'].lower()} painting by {ARTIST}, {size_text(p)}. {state} {p['description']}"
        html = page(title=f"{p['title']} | {p['medium']} painting by {ARTIST}",
                    description=desc[:300], path=f"paintings/{p['slug']}.html", prefix="../",
                    body=body, og_image=large, jsonld=[product, crumbs], og_type="product")
        (OUT / "paintings" / f"{p['slug']}.html").write_text(html, encoding="utf-8")


def build_extras():
    shutil.copy(ROOT / "static" / "styles.css", OUT / "styles.css")
    shutil.copy(ROOT / "static" / "favicon.svg", OUT / "favicon.svg")
    urls = [(f"{BASE}/", P[0])] + [(f"{BASE}/paintings/{p['slug']}.html", p) for p in P]
    items = []
    for u, p in urls:
        imgs = [p] if u != f"{BASE}/" else P
        img_xml = "".join(f"<image:image><image:loc>{e(BASE + '/images/' + q['dims']['large'][0])}</image:loc></image:image>" for q in imgs)
        items.append(f"<url><loc>{e(u)}</loc><lastmod>{TODAY}</lastmod>{img_xml}</url>")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(items) + "\n</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    nf = page(title=f"Page not found | {ARTIST}", description="This page doesn't exist.", path="404.html", prefix=BASE + "/",
              body=f'<section class="prose"><h1>This page doesn\'t exist</h1><p>The painting may have moved. <a href="{BASE}/index.html#paintings">See all paintings</a>.</p></section>',
              og_image=P[0]["dims"]["large"][0], jsonld=[])
    (OUT / "404.html").write_text(nf.replace('<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"'), encoding="utf-8")
    domain = S.get("custom_domain")
    if domain:
        (OUT / "CNAME").write_text(domain + "\n")


if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    process_images()
    build_home()
    build_paintings()
    build_extras()
    samples = [p["title"] for p in P if p.get("sample")]
    print(f"Built {len(P)} paintings into {OUT}/")
    if samples:
        print(f"Note: {len(samples)} sample paintings still in paintings.json: {', '.join(samples)}")
    if "example.com" in S["email"]:
        print("Note: set your real email in paintings.json")
