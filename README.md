# Trish Leto website

Static site for Trish Leto, GenX UGC creator and model, U.S. Navy veteran and speaker. It is her own brand, and it names her as an Official Simply Digital Partner for UGC + paid ads packages. Built by Simply Digital.

Not indexed yet (`INDEXABLE = False`).

## Layout

| Path | What it is |
|---|---|
| `build.py` | Generates every page. Edit this, never the HTML. |
| `docs/` | **The published site.** GitHub Pages serves this folder only (Settings > Pages > Deploy from a branch > `main` / `/docs`). |
| `docs/assets/css/style.css`, `docs/assets/js/site.js` | Hand-edited source files; the build stamps a cache-busting `?v=` hash onto them. |
| `tools/` | Image, icon and layout tools. Not published. |

## Pages

| Path | What it does |
|---|---|
| `/` | Who she is, proof numbers, formats and categories, how it works, recent product videos, packages, speaking, CTA |
| `/work-with-me/` | Retainer vs per project, what you get, 5-step process, the four Simply Digital packages, what she won't do, FAQ |
| `/portfolio/` | Stats, top performers, recent product videos with the FTC disclosure, a lifestyle and faith slot |
| `/about/` | Her story, quick facts, partner note, her Stan store guides and a recommended course (affiliate link, disclosed) |
| `/speaking/` | DOMINATE Summit (Oct 9, 2026), Military Creator Con, talk topics, booking checklist |
| `/contact/` | Collab email, copy button, three pre-filled mailto paths, inquiry template. No third-party form. |
| `/404.html` | Not-found page (always noindex, uses absolute BASE links so it works at any depth) |

## How to change things

```bash
python3 build.py            # writes docs/ (every page, robots.txt, sitemap.xml, site.webmanifest), then audits
python3 build.py --audit    # audit only
BUILD_TODAY=2026-10-10 python3 build.py   # preview the site as it builds on another date
```

The header, footer, email, handles, stats, event, video list and Stan products are each defined once near the top of `build.py`.

The audit fails the build on: any em dash or en dash in any text file in the repo, more or fewer than one `<h1>` per page, a robots meta that does not match `INDEXABLE`, a wrong canonical, JSON-LD that does not parse, an `<img>` without alt or size, a broken internal link, an affiliate link without a disclosure next to it, "upcoming" event copy after the event date, or a missing icon or OG image. It warns while `PARTNER_CONFIRMED` is False (and fails if `INDEXABLE` is True).

### The two switches

- **`BASE`** (now `https://ogeddiesmith.github.io/trish-leto/`): canonical tags, Open Graph, JSON-LD and the sitemap all come from it. To move to her own domain, change this one line, add a `docs/CNAME` file with the domain, and rebuild.
- **`INDEXABLE`** (now `False`): every page emits `noindex,nofollow` and `robots.txt` disallows everything. Set it to `True` to emit `index,follow` and a `robots.txt` that allows all and lists the sitemap.

Crawlers only read `robots.txt` at the root of a host. While the site lives at the `/trish-leto/` project path, the per-page noindex meta tag is what keeps it out of search. On her own domain both apply.

### Pending lines

The `PENDING` block at the top of `build.py` holds lines that wait on a confirmation (her Facebook link, a third talk topic, posting on her own TikTok, the partner badge). Each renders only when its switch is `True`.

### Events

The build is date-aware. After `EVENT["end"]`, it writes past-tense copy, labels the event "Past event" in the HTML, rewrites the speaking description and drops the Event JSON-LD. Rebuild and push after the date so the published HTML catches up.

### Images

```bash
python3 tools/make_images.py   # crops + WebP into docs/assets/img/
python3 tools/make_icons.py    # favicons (Pillow) + docs/assets/img/og-image.jpg (headless Chrome from tools/og.html)
```

Source photos stay outside this repo, in the client folder. File names stay the same when the sources change, so no HTML changes are needed.

### Layout check

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs   # from this folder
node tools/check_layout.mjs ../site-screenshots                  # 360, 390, 768, 1280 px
```

It uses real mobile emulation over the Chrome DevTools Protocol, compares `scrollWidth` to the device width, counts `<h1>` tags, reports console errors and failed requests, and saves full-page screenshots. Below 900 px it also opens the mobile menu and checks the open panel (no overflow, links inside the side gutter). On pages with a hero photo it prints where the photo starts. Requests to the live `BASE` (the 404 page's assets) are answered from the local server.

## House rules for this site

1. US English. No em dashes or en dashes.
2. Never invent brand clients, testimonials, results, prices or credentials. Products in her TikTok videos are her own content, never presented as clients. Affiliate products are labeled and disclosed. Packages are always "custom quote."
3. Her personal life stays off the site, apart from the "hands only, never faces" rule for kids on camera.
4. Social numbers always say "as of" (`STATS_AS_OF`).
5. No third-party embed on page load. TikTok cards are plain links; TikTok's official player loads only when someone presses Play.
