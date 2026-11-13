# Painting website

A fast static website for selling original paintings. You edit one file
(`paintings.json`), drop photos into `originals/`, run one command, and
publish the `docs/` folder free on GitHub Pages.

## Folder layout

```
paintings.json   your paintings, prices and site text (the only file you edit)
originals/       full-size photos of your paintings (any size, .jpg or .png)
static/          stylesheet and favicon
build.py         builds the site into docs/
docs/            the finished site (don't edit by hand, it's rebuilt each time)
```

## 1. Replace the sample paintings

To add a new painting:

1. Photograph it straight-on in daylight, no glare, cropped to the edges of the canvas.
2. Save it in `originals/` with a descriptive name, e.g. `bow-river-winter.jpg`.
   Descriptive file names help Google Images.
3. Add an entry to `paintings.json`:

| Field | What to put |
|---|---|
| `slug` | URL name, lowercase with hyphens: `bow-river-winter` |
| `title`, `year`, `medium` | e.g. `"Oil on canvas"` (keep the "X on Y" form) |
| `height_in`, `width_in` | Real size in inches, height first. The site converts to cm and uses it to show paintings at relative sizes. |
| `price` | Number in CAD, no `$` |
| `status` | `available`, `reserved` or `sold` (sold shows a red dot) |
| `stripe_link` | Stripe Payment Link for this painting (see step 3). Leave `""` and the button becomes "Email to buy". |
| `alt` | One sentence describing what's in the painting: colours, subject, place. Used by screen readers and Google. |
| `description` | 1–3 sentences about the painting, in your voice. |
| `featured` | `true` on the one painting you want large at the top |

Set your real email, Instagram and about text in the `site` section.

## 2. Build

```
pip install pillow
python3 build.py
```

Open `docs/index.html` in your browser to check it. The build also strips
GPS location data from phone photos, so your home address isn't in the images.

## 3. Take payments with Stripe Payment Links (no code)

1. Create a Stripe account (stripe.com, works in Canada).
2. Payment Links > New. Add the painting as a product with its price in CAD.
3. Turn on **Limit the number of payments** and set it to 1, so a painting can't be sold twice.
4. Turn on **Collect customers' addresses > Billing and shipping**, allow Canada (and any other countries you ship to),
   and add shipping rates, plus a "Local pickup in Calgary" rate at $0.
5. Copy the link into that painting's `stripe_link`, rebuild, publish.

When a painting sells: set `status` to `sold`, rebuild and publish.

## 4. Publish on GitHub Pages

1. Create a new public repo named `paintings` on your GitHub account.
2. Push this whole folder to it.
3. Repo Settings > Pages > Deploy from a branch > `main`, folder `/docs`.
4. Under Custom domain, enter `www.mahtaium.com` and save. The site lives at `https://www.mahtaium.com`
   (this is `site_url` in `paintings.json`).

### Custom domain (recommended for SEO and trust)

Buy a domain like `yourname.art` or `yournamepaintings.ca`, add
`"custom_domain": "www.yourdomain.ca"` to the `site` section, set
`site_url` to `https://www.yourdomain.ca`, rebuild, and follow GitHub's
custom-domain DNS steps (Settings > Pages > Custom domain, tick Enforce HTTPS).

## 5. Getting found on Google

Already built in: a unique title and description on every page, one page per
painting with Product + VisualArtwork structured data (price, availability,
size, medium, artist), breadcrumbs, an image sitemap, `robots.txt`, canonical
URLs, social-share previews, alt text, and small, fast pages with no tracking scripts.

What you need to do:

- **Google Search Console** (search.google.com/search-console): add the site,
  verify it, and submit `sitemap.xml`. Re-submit after adding paintings.
- **Write real alt text and descriptions.** Mention places people search for:
  "textured ocean painting", "beach wall art", "floral painting", "Calgary artist".
- **Get links to the site:** your Instagram bio, your portfolio site, Pinterest
  pins of each painting (link to the painting's page), local art markets or
  shows you take part in.
- **Add new work regularly.** Fresh pages are what bring people back and keep
  the site visible.
