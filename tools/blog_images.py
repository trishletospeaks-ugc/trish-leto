#!/usr/bin/env python3
"""Find and save a stock photo for a blog post.

    python3 tools/blog_images.py <slug> hero|inline "<physical scene>"            list the top results
    python3 tools/blog_images.py <slug> hero|inline "<physical scene>" --pick N   save result N
    add --pixabay to search Pixabay instead of Pexels

Search for a PHYSICAL real-world scene (people, places, things: "woman filming
a smoothie in a home kitchen"), never screens or "digital marketing", which all
return the same generic stock photo.

Pexels (landscape) first; Pixabay when Pexels fails or finds nothing. --pick
saves WebP at 1200 and 720 px wide into docs/assets/img/blog/ as
<slug>-<kind>-<width>.webp (hero cropped to 16:9, inline to 3:2), plus a
1200 px JPEG of the hero for social previews. The build never deletes that
folder. The last line printed is the JSON for the post's front matter
("hero" or "inline_image"); add your own descriptive "alt".

Keys come from the environment (PEXELS_API_KEY, PIXABAY_API_KEY) or, failing
that, from the Simply Digital .env three folders up. They are never printed,
logged or written anywhere.
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageOps

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SITE, "docs", "assets", "img", "blog")
ENV_FILE = os.path.normpath(os.path.join(SITE, "..", "..", "..", ".env"))
RATIO = {"hero": (16, 9), "inline": (3, 2)}
WIDTHS = (1200, 720)
RESULTS = 10
# Pexels answers urllib's default User-Agent with a 403, so send a browser one.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def api_key(name):
    val = os.environ.get(name, "").strip()
    if val:
        return val
    try:
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def fetch(url, headers=None, as_json=True):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r) if as_json else r.read()


def search_pexels(query):
    key = api_key("PEXELS_API_KEY")
    if not key:
        raise RuntimeError("PEXELS_API_KEY not found")
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "orientation": "landscape", "per_page": RESULTS})
    data = fetch(url, {"Authorization": key, "Accept": "application/json"})
    return [{"site": "Pexels", "w": ph["width"], "h": ph["height"], "about": ph.get("alt") or "",
             "credit": ph["photographer"], "credit_url": ph["photographer_url"], "source_url": ph["url"],
             "download": ph["src"]["original"] + "?auto=compress&cs=tinysrgb&w=2000"}
            for ph in data.get("photos", [])]


def search_pixabay(query):
    key = api_key("PIXABAY_API_KEY")
    if not key:
        raise RuntimeError("PIXABAY_API_KEY not found")
    url = "https://pixabay.com/api/?" + urllib.parse.urlencode(
        {"key": key, "q": query[:100], "image_type": "photo", "orientation": "horizontal",
         "safesearch": "true", "min_width": 1200, "per_page": RESULTS})
    data = fetch(url, {"Accept": "application/json"})
    return [{"site": "Pixabay", "w": h["imageWidth"], "h": h["imageHeight"], "about": h.get("tags", ""),
             "credit": h["user"], "credit_url": f"https://pixabay.com/users/{h['user']}-{h['user_id']}/",
             "source_url": h["pageURL"], "download": h["largeImageURL"]}
            for h in data.get("hits", [])]


def search(query, pixabay_only):
    """Never print the request or the exception text: the Pixabay key rides in the query string."""
    order = [("Pixabay", search_pixabay)] if pixabay_only else [("Pexels", search_pexels), ("Pixabay", search_pixabay)]
    for name, fn in order:
        try:
            hits = fn(query)
        except urllib.error.HTTPError as e:
            print(f"{name} search failed (HTTP {e.code}).", file=sys.stderr)
            continue
        except urllib.error.URLError as e:
            print(f"{name} search failed (network: {e.reason}).", file=sys.stderr)
            continue
        except RuntimeError as e:
            print(f"{name}: {e}.", file=sys.stderr)
            continue
        except (ValueError, KeyError):
            print(f"{name} sent an unexpected response.", file=sys.stderr)
            continue
        if hits:
            return hits
        print(f"{name} found nothing for that query.", file=sys.stderr)
    return []


def crop_to(im, ratio):
    rw, rh = ratio
    w, h = im.size
    if w * rh > h * rw:
        nw = round(h * rw / rh)
        left = (w - nw) // 2
        return im.crop((left, 0, left + nw, h))
    nh = round(w * rh / rw)
    top = (h - nh) // 2
    return im.crop((0, top, w, top + nh))


def save(hit, slug, kind):
    raw = fetch(hit["download"], as_json=False)
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    im = crop_to(im, RATIO[kind])
    if im.width < max(WIDTHS):
        print(f"Note: after cropping the photo is only {im.width}px wide, so it is upscaled. Pick a bigger one if you can.",
              file=sys.stderr)
    clean = Image.new("RGB", im.size)  # a fresh image carries no EXIF or other metadata
    clean.paste(im)
    os.makedirs(OUT, exist_ok=True)
    name = f"{slug}-{kind}"
    rw, rh = RATIO[kind]
    written = []
    for w in WIDTHS:
        out = clean.resize((w, round(w * rh / rw)), Image.LANCZOS)
        path = os.path.join(OUT, f"{name}-{w}.webp")
        out.save(path, "WEBP", quality=80, method=6)
        written.append(path)
    if kind == "hero":
        path = os.path.join(OUT, f"{name}-1200.jpg")
        clean.resize((1200, 675), Image.LANCZOS).save(path, "JPEG", quality=82, optimize=True, progressive=True)
        written.append(path)
    return name, written


def main(argv):
    args, pick, i = [], None, 0
    while i < len(argv):
        if argv[i] == "--pick":
            try:
                pick = int(argv[i + 1])
            except (IndexError, ValueError):
                sys.exit("--pick needs a result number, for example --pick 2")
            i += 2
            continue
        if not argv[i].startswith("--"):
            args.append(argv[i])
        i += 1
    if len(args) != 3 or args[1] not in RATIO:
        sys.exit(__doc__)
    slug, kind, query = args
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        sys.exit("slug must be kebab-case, the same as the post's file name")
    hits = search(query, "--pixabay" in argv)
    if not hits:
        sys.exit("No photos found. Try a different physical scene.")
    if pick is None:
        print(f'{hits[0]["site"]} results for "{query}" ({kind}, cropped to {RATIO[kind][0]}:{RATIO[kind][1]}):')
        for i, h in enumerate(hits, 1):
            print(f"{i:2}. {h['w']}x{h['h']}  {h['credit']}  {h['about'][:90]!r}\n    {h['source_url']}")
        print(f"\nSave one: python3 tools/blog_images.py {slug} {kind} \"{query}\" --pick N")
        return
    if not 1 <= pick <= len(hits):
        sys.exit(f"--pick must be 1 to {len(hits)}")
    hit = hits[pick - 1]
    name, written = save(hit, slug, kind)
    for path in written:
        print("Saved", os.path.relpath(path, SITE))
    if hit["about"]:
        print(f"{hit['site']} describes it as: {hit['about']} (write your own alt text)")
    print(json.dumps({"file": name, "credit": hit["credit"], "credit_url": hit["credit_url"],
                      "source_url": hit["source_url"]}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
