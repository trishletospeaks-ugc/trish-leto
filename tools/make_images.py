#!/usr/bin/env python3
"""
Crop and optimize the site photos into docs/assets/img/.

    python3 tools/make_images.py

Sources live OUTSIDE this repo, in the client folder one level up, so the
big originals never get committed here:

    ../photos/facebook-captures/   placeholder photos until Trish sends originals
    ../photos/tiktok-thumbs/       cover frames of her own TikTok videos
                                   (from TikTok's public oEmbed endpoint)

These are PLACEHOLDERS. When Trish sends original photos, drop them in
../photos/originals/, point the SOURCES below at them, and re-run. The output
file names stay the same, so no HTML changes are needed.

Crop rules:
  * speaking photo: audience heads and the mouse cursor are cropped out
  * summit graphic: the bottom title line is cropped off (the page prints the
    talk title as text instead)
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
CLIENT = os.path.dirname(SITE)
CAP = os.path.join(CLIENT, "photos", "facebook-captures")
THUMBS = os.path.join(CLIENT, "photos", "tiktok-thumbs")
OUT = os.path.join(SITE, "docs", "assets", "img")

# name: (source file, crop box (left, top, right, bottom) or None, output widths)
SOURCES = {
    # Her current profile photo, cropped to 4:5 around her face.
    "trish-coffee": (os.path.join(CAP, "headshot-coffee.png"), (120, 0, 818, 873), [640, 400]),
    # Presenting at Military Creator Con. Heads start at y~455 and the cursor
    # sits at x~760, so keep x 0..600 and y 40..448 (Trish plus the logo).
    "trish-military-creator-con": (os.path.join(CAP, "speaking-military-creator-con.png"), (0, 40, 600, 448), [600, 400]),
    # DOMINATE speaker graphic, title line cropped off.
    "dominate-summit-2026": (os.path.join(CAP, "speaker-dominate-summit-oct9.png"), (40, 0, 909, 672), [860, 480]),
}

# TikTok cover frames, all cropped to 9:16 and saved at 360 px wide.
TIKTOK_IDS = [
    "7691470090906193182",
    "7690644146540776734",
    "7689506559583472927",
    "7689485389450497311",
    "7689131684888874271",
    "7690267187298290975",
    "7690955913506622750",
]


def save_webp(im, path, q=80):
    im.save(path, "WEBP", quality=q, method=6)
    return os.path.getsize(path)


def nine_sixteen(im):
    w, h = im.size
    target = 9 / 16
    if abs(w / h - target) < 0.01:
        return im
    if w / h > target:  # too wide: trim the sides
        nw = round(h * target)
        x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w / target)  # too tall: keep the top
    return im.crop((0, 0, w, nh))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (src, box, widths) in SOURCES.items():
        im = Image.open(src).convert("RGB")
        if box:
            im = im.crop(box)
        for w in widths:
            h = round(im.height * w / im.width)
            out = os.path.join(OUT, f"{name}-{w}.webp")
            size = save_webp(im.resize((w, h), Image.LANCZOS), out)
            print(f"{out}  {w}x{h}  {size // 1024} KB")

    os.makedirs(os.path.join(OUT, "tiktok"), exist_ok=True)
    for vid in TIKTOK_IDS:
        im = Image.open(os.path.join(THUMBS, f"{vid}.jpg")).convert("RGB")
        if vid == "7689506559583472927":
            im = im.crop((0, 0, im.width, 1450))  # trim the black strip at the bottom
        im = nine_sixteen(im).resize((360, 640), Image.LANCZOS)
        out = os.path.join(OUT, "tiktok", f"{vid}.webp")
        size = save_webp(im, out, q=72)
        print(f"{out}  360x640  {size // 1024} KB")


if __name__ == "__main__":
    main()
