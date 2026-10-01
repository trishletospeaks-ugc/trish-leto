#!/usr/bin/env python3
"""
Trish Leto website generator.

    python3 build.py            build every page, then run the audit
    python3 build.py --audit    audit the existing output only

Writes the published site into docs/: index.html, work-with-me/, portfolio/,
about/, speaking/, contact/, 404.html, robots.txt, sitemap.xml and
site.webmanifest. GitHub Pages serves docs/ only, so this file, the README and
tools/ are never published.

DO NOT HAND-EDIT THE GENERATED HTML. Edit this file and re-run. Every page
shares one header, one footer, one email address and one set of numbers, so a
change here lands everywhere at once.

Two switches matter:

  BASE        the live address, with a trailing slash. Canonical tags, Open
              Graph, JSON-LD and the sitemap all come from it. Moving to her
              own domain is a one-line change here.
  INDEXABLE   False (now): every page says noindex,nofollow and robots.txt
              disallows everything. True: index,follow, robots.txt allows all
              and points at the sitemap. Flip it only when Trish has approved
              the copy and the site is on its final address.

The PENDING block below holds lines that wait on Trish (or Eddie) to confirm.
Each renders only once its switch is True.

House rules this file must keep (the audit enforces the ones it can):
  1. US English. No em dashes or en dashes anywhere.
  2. No invented brand clients, testimonials, results, prices or credentials.
     Products in her TikTok videos are shown as HER content, never as clients.
     Products she sells as an affiliate are labeled as affiliate links.
  3. Her personal life stays off the site, apart from the hands-only rule
     for kids on camera.
  4. Social numbers always carry "as of" (STATS_AS_OF).
  5. No third-party embed loads on page load. TikTok cards are links; the
     official player loads only when someone presses Play.
"""
import datetime
import hashlib
import html
import json
import os
import re
import sys
from urllib.parse import quote

# =============================================================================
# SWITCHES
# =============================================================================

BASE = "https://ogeddiesmith.github.io/trish-leto/"
INDEXABLE = False

# =============================================================================
# PENDING: each line below waits on a confirmation and renders only when True
# =============================================================================

# Trish: link her personal Facebook profile (footer + JSON-LD sameAs)? Off
# until she says yes. If she has a creator page instead, put its address in
# FACEBOOK_URL and switch this on.
LINK_FACEBOOK = False
# Trish: is "GenX content that works" a talk she gives? Off until she confirms.
TALK_GENX_CONFIRMED = False
# Trish: will she post a brand's video on her own TikTok (TikTok Shop or Spark
# Ads, with the paid-partnership label)? Off until she confirms.
POSTS_ON_OWN_TIKTOK_CONFIRMED = False
# Eddie: partner agreement signed, or he names her a partner regardless. The
# "Official Simply Digital Partner" badge renders in the draft because Eddie
# asked for it, but the audit warns until this is True and fails any build
# with INDEXABLE = True. Do not push the site before this is settled.
PARTNER_CONFIRMED = False
# Added to the "Do you post the videos for us?" answer once Trish confirms.
OWN_TIKTOK_LINE = (" Want it on my own TikTok (TikTok Shop or Spark Ads)? Ask. "
                   "It carries a paid-partnership label.")

# =============================================================================
# FACTS (sources: ../RESEARCH-2026-10-01.md and ../Content Creation Guidelines.rtf)
# =============================================================================

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(SRC, "docs")  # the published folder (GitHub Pages: main /docs)
# BUILD_TODAY=YYYY-MM-DD previews the site as it builds on that date (for
# example the day after the summit, to check the past-event copy).
TODAY = (datetime.date.fromisoformat(os.environ["BUILD_TODAY"]) if os.environ.get("BUILD_TODAY")
         else datetime.date.today())
BUILD_DATE = TODAY.isoformat()
YEAR = TODAY.year

NAME = "Trish Leto"
JOB_TITLE = "GenX UGC Creator, Model and Public Speaker"
CITY, REGION = "Tampa", "FL"
EMAIL = "trishletospeaks@gmail.com"

TIKTOK_HANDLE = "@trishizzlefoshizzle"
TIKTOK_URL = "https://www.tiktok.com/@trishizzlefoshizzle"
INSTAGRAM_HANDLE = "@Real_trish_leto"
INSTAGRAM_URL = "https://www.instagram.com/real_trish_leto/"
FACEBOOK_URL = "https://www.facebook.com/trish.leto"
STAN_URL = "https://stan.store/trishleto"
SD_URL = "https://simplydigitalmarketing.co"

# Read from her TikTok profile on 2026-10-01. Update both lines together.
STATS_AS_OF = "October 2026"
STATS = [
    ("30.1K", "TikTok followers"),
    ("178.8K", "TikTok likes"),
    ("1.1M", "views on one video"),
]

# Verified on spartanmedia.com/dominate/ on 2026-10-01. Times are local
# (Eastern Daylight Time in October, so UTC-4). The organizer runs the Power
# Track from 4:20 to 5:20 p.m. as "a series of quick-hitting three minute
# presentations", so the site never calls her slot a full-length talk.
EVENT = {
    "name": "DOMINATE Entrepreneurial Summit",
    "talk": "Control the Scroll: How to Grab Attention with Unlimited Content Ideas",
    "track": "Power Track",
    "start": "2026-10-09T10:30:00-04:00",
    "end": "2026-10-09T17:30:00-04:00",
    "date_label": "Friday, October 9, 2026",
    "time_label": "10:30 a.m. to 5:30 p.m. Eastern",
    "track_time_label": "4:20 to 5:20 p.m. Eastern",
    "short_date": "Oct 9, 2026",
    "where_label": "Clearwater, FL, and online",
    "street": "3118 Gulf To Bay Ste 111",
    "locality": "Clearwater",
    "region": "FL",
    "postal": "33759",
    "url": "https://spartanmedia.com/dominate/",
    "organizer": "Spartan Media",
    "organizer_url": "https://spartanmedia.com/",
}
# After the summit ends, the build writes past-tense copy, drops the Event
# JSON-LD (Google ignores past events) and labels it "Past event" in the HTML.
EVENT_PAST = TODAY > datetime.date.fromisoformat(EVENT["end"][:10])

FORMATS = [
    ("Talking heads", "Straight to camera. Clear, warm and convincing."),
    ("Yap style", "Chatty storytelling that feels like a FaceTime with a friend and keeps people watching."),
    ("Lifestyle", "Your product in real life: the kitchen counter, the morning coffee, the backyard garden."),
    ("Product demos", "Unboxing, how it works, and why it earned a spot in my routine."),
    ("B-roll", "Hands, pours, textures and close-ups your editor will thank you for."),
]

NICHES = [
    "Supplements", "Food and drink", "Pets", "Cars", "Kitchen and appliances",
    "Plants and gardening", "Makeup", "Skin care", "Hair care",
]

# Her two biggest videos. TikTok does not allow these two to be embedded
# (its oEmbed returns nothing), so they are link-only cards.
TOP_VIDEOS = [
    {"id": "7606378740683164958", "views": "1.1M", "title": "My most-viewed TikTok",
     "text": "My most-viewed TikTok to date."},
    {"id": "7486834491520994591", "views": "161.3K", "title": "My GenX intro",
     "text": "My hello to fellow Gen Xers: \u201cGen X, let's connect!\u201d"},
]

# Her own recent product videos. Cover frames come from TikTok's public oEmbed
# (see tools/make_images.py). "note" quotes her on-screen text or caption, or
# plainly describes the cover frame. Never call these brands clients.
PRODUCT_VIDEOS = [
    {"id": "7690644146540776734", "title": "Zinc supplement", "tag": "Supplements",
     "note": "Hook: “POV: is taking zinc really doing anything???”",
     "alt": "Cover frame: Trish holds up a bottle of zinc supplements in her kitchen"},
    {"id": "7689506559583472927", "title": "Hydration drink mix", "tag": "Supplements · TikTok Shop",
     "note": "Product demo with the box, the packet and the finished drink.",
     "alt": "Cover frame: Trish holds a box of hydration drink mix next to a glass of it"},
    {"id": "7691470090906193182", "title": "Energy drink", "tag": "Food and drink · TikTok Shop",
     "note": "Hook: “‘Patiently’ waiting for tomorrow’s energy drink…”",
     "alt": "Cover frame: Trish waits on the couch while an energy drink sits on the kitchen counter"},
    {"id": "7689485389450497311", "title": "Protein powder", "tag": "Supplements · TikTok Shop",
     "note": "Comment reply: “I love replying to comments about my favorite protein powder.”",
     "alt": "Cover frame: Trish holds a jar of protein shake at her kitchen counter"},
    {"id": "7689131684888874271", "title": "Beef tallow skin care", "tag": "Skin care · TikTok Shop",
     "note": "Extreme close-up skin care demo. Built to stop the scroll.",
     "alt": "Cover frame: an extreme close-up of Trish's eye for a beef tallow skin care video"},
    {"id": "7690955913506622750", "title": "Hydration sticks", "tag": "TikTok Shop · Product demo",
     "note": "Unboxing-style demo: the stick pack, the box and the glass.",
     "alt": "Cover frame: Trish holds up a hydration drink stick pack beside its box"},
]
HOME_VIDEO_IDS = ["7690644146540776734", "7689506559583472927", "7691470090906193182", "7689485389450497311"]

# Not a product video: its caption is "#jesuschrist #christiantiktok #coffee"
# (TikTok oEmbed, 2026-10-01). Shown on the portfolio in its own small
# "Lifestyle and faith" slot, never under the product-video headings.
LIFESTYLE_VIDEOS = [
    {"id": "7690267187298290975", "title": "Morning coffee", "tag": "Lifestyle · Faith",
     "note": "On screen: “I hope your coffee tastes great, you feel beautiful today, and you realize how truly blessed you are.”",
     "alt": "Cover frame: coffee brewing, with an on-screen message about feeling blessed"},
]

# Packages sold with Simply Digital (partner deck slide 10). No prices, ever:
# Trish sets her own rates and every package is a custom quote.
PACKAGES = [
    {"name": "UGC + Meta or TikTok ads",
     "trish": "Monthly videos with hooks built from your brand's story.",
     "sd": "Runs them as Meta or TikTok ads, plus retargeting."},
    {"name": "TikTok Shop launch",
     "trish": "TikTok Shop videos and product demos.",
     "sd": "TikTok ads that put them in front of more buyers, with a clear paid-partnership label."},
    {"name": "UGC + Google Ads + landing page",
     "trish": "Videos and b-roll for the page and the ads.",
     "sd": "Builds the landing page, sets up tracking and runs Google Search and Performance Max."},
    {"name": "Website + UGC + ads launch",
     "trish": "Launch videos and b-roll.",
     "sd": "Builds the website, sets up tracking and runs launch campaigns on Google, Meta or TikTok."},
]

# Checked on her Stan store on 2026-10-01. The two guides are hers ("by
# @trishleto"). "The Ultimate UGC Course" on her store is an AFFILIATE link to
# @Megan_UGC's course, so it is labeled as a recommendation with a disclosure,
# never as her own course.
STAN_PRODUCTS = [
    {"label": "On my Stan store", "title": "The GenX Content Survival Guide",
     "text": "5 proven GenX video formulas that actually work.",
     "url": STAN_URL + "/p/genx-content-survival-guide"},
    {"label": "On my Stan store", "title": "The No B.S. ChatGPT Prompt Playbook",
     "text": "Your business in a few prompts. Yes, REALLY!",
     "url": STAN_URL + "/p/the-ultimate-guide-to-using-the-piggly-method"},
    {"label": "A course I recommend", "title": "The Ultimate UGC Course",
     "text": "A UGC course for creators 40+ by @Megan_UGC.",
     "url": "https://stan.store/affiliates/364b4eae-b086-40f4-87f9-9c3fec9693c6",
     "disclosure": "Affiliate link: I may earn a commission."},
]

NAV = [
    ("work-with-me/", "Work with me"),
    ("portfolio/", "Portfolio"),
    ("about/", "About"),
    ("speaking/", "Speaking"),
    ("contact/", "Contact"),
]

OG_IMAGE = "assets/img/og-image.jpg"
OG_IMAGE_ALT = "Trish Leto, GenX UGC creator, model, Navy veteran and speaker"

# Inquiry templates (used by mailto links and the contact page).
UGC_TEMPLATE = """Hi Trish,

Brand:
Website:
Product(s):
Can you ship the product? (yes / no)
Videos needed (how many, which formats):
B-roll needed? (yes / no)
Where they will run (organic, TikTok Shop, paid ads) and for how long:
Timeline:
Budget range:

Thanks!"""

PACKAGE_TEMPLATE = """Hi Trish,

We are interested in a UGC + ads package with Simply Digital.

Brand:
Website:
Product(s):
Package (UGC + Meta or TikTok ads, TikTok Shop launch, UGC + Google Ads + landing page, website + UGC + ads launch, or not sure yet):
Monthly ad budget (if known):
Timeline:

Thanks!"""

SPEAKING_TEMPLATE = """Hi Trish,

Event name:
Date(s):
In person (where) or virtual:
Audience (who and about how many):
Topic you would like:
Format and length:
Speaker budget or honorarium:

Thanks!"""

# =============================================================================
# HELPERS
# =============================================================================


def esc(s):
    return html.escape(s, quote=True)


def mailto(subject, body=None):
    q = "subject=" + quote(subject, safe="")
    if body:
        q += "&body=" + quote(body.replace("\n", "\r\n"), safe="")
    return "mailto:" + EMAIL + "?" + q


NEW_TAB = '<span class="sr-only"> (opens in a new tab)</span>'


def ext(url, text, cls="", label=None):
    c = f' class="{cls}"' if cls else ""
    a = f' aria-label="{esc(label)}"' if label else ""
    return f'<a{c} href="{esc(url)}" target="_blank" rel="noopener"{a}>{text}{"" if label else NEW_TAB}</a>'


def file_hash(rel):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


ICON_STAR = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.2l7.1-.6z"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 16.2l-3.5-3.5L4 14.2l5 5 11-11-1.5-1.5z"/></svg>'
ICON_PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 4.5v15l13-7.5z"/></svg>'


def img(p, name, widths, alt, sizes, ratio, eager=False, cls=""):
    """Responsive WebP <img>. ratio = (w, h) of the largest file."""
    big = max(widths)
    srcset = ", ".join(f"{p}assets/img/{name}-{w}.webp {w}w" for w in sorted(widths))
    w, h = ratio
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="{p}assets/img/{name}-{big}.webp" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(alt)}" {load} decoding="async">')


def partner_badge(where=""):
    label = "Official Simply Digital Partner for UGC and paid ads packages. Opens simplydigitalmarketing.co in a new tab."
    return (f'<a class="partner" href="{SD_URL}" target="_blank" rel="noopener" aria-label="{esc(label)}">'
            f'<span class="seal">{ICON_CHECK}</span>'
            f'<span><span class="p-top">Official Simply Digital Partner</span>'
            f'<span class="p-main">UGC + paid ads packages</span></span>'
            f'<span class="arrow" aria-hidden="true">&rarr;</span></a>')


def tiktok_url(vid):
    return f"{TIKTOK_URL}/video/{vid}"


def vid_card(v, p, h="h3"):
    url = tiktok_url(v["id"])
    title = esc(v["title"])
    return f"""<article class="vid">
  <div class="vid-media">
    <a class="vid-cover" href="{url}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">
      <img src="{p}assets/img/tiktok/{v['id']}.webp" width="360" height="640" alt="" loading="lazy" decoding="async">
    </a>
    <span class="vid-badge">TikTok</span>
    <button class="vid-play" type="button" data-tiktok="{v['id']}" data-title="{title} video on TikTok">{ICON_PLAY}<span>Play here</span><span class="sr-only">: {title} (loads the TikTok player)</span></button>
  </div>
  <div class="vid-body">
    <p class="vid-tag">{esc(v['tag'])}</p>
    <{h}>{title}</{h}>
    <p class="vid-hook">{esc(v['note'])}</p>
    <p class="sr-only">{esc(v['alt'])}</p>
    <a class="vid-link" href="{url}" target="_blank" rel="noopener">Watch on TikTok<span class="sr-only">: {title} (opens in a new tab)</span></a>
  </div>
</article>"""


def disclosure():
    return ("<p class=\"disclosure\">These are my own TikTok posts, shown as samples of my work. "
            "TikTok Shop videos can earn me a commission when viewers buy through them. "
            "A product appearing here does not mean that brand hired me.</p>")


def stats_band(heading_level="h2", heading="The numbers, so far"):
    items = "".join(f'<li class="stat"><b>{n}</b><span>{esc(l)}</span></li>' for n, l in STATS)
    return f"""<section class="band-ink section-tight" aria-labelledby="stats-h">
  <div class="wrap">
    <{heading_level} id="stats-h" class="sr-only">{esc(heading)}</{heading_level}>
    <ul class="stats">{items}</ul>
    <p class="stats-note">TikTok numbers as of {STATS_AS_OF}, from {ext(TIKTOK_URL, esc(TIKTOK_HANDLE))}.</p>
  </div>
</section>"""


def event_status():
    if EVENT_PAST:
        return '<span class="event-status is-past">Past event</span>'
    # site.js still relabels it in the browser if the page outlives the date.
    return (f'<span class="event-status" data-event-end="{EVENT["end"]}" '
            f'data-past-label="Past event">Upcoming</span>')


def home_event_line():
    if EVENT_PAST:
        return (f"<p><strong>{EVENT['short_date']}:</strong> I spoke in the {EVENT['track']} at the "
                f"{EVENT['name']} in {EVENT['locality']}, {EVENT['region']}: &ldquo;{EVENT['talk']}.&rdquo;</p>")
    return (f"<p><strong>{EVENT['date_label']}:</strong> {EVENT['name']}, {EVENT['where_label']}. "
            f"My {EVENT['track']} ({EVENT['track_time_label']}): &ldquo;{EVENT['talk']}.&rdquo;</p>")


def cta_band(p):
    return f"""<section class="band-coral section" aria-labelledby="cta-h">
  <div class="wrap center">
    <p class="kicker">PAID collabs ONLY</p>
    <h2 id="cta-h">Let's make something people can't scroll past!</h2>
    <p class="lede" style="margin-inline:auto">Tell me about your product, and I'll tell you how I'd film it.</p>
    <div class="btn-row" style="justify-content:center">
      <a class="btn btn-sun" href="{esc(mailto('UGC collab: [your brand]', UGC_TEMPLATE))}">Email Trish</a>
      <a class="btn btn-ghost" href="{p}contact/">All the ways to reach me</a>
    </div>
  </div>
</section>"""


# =============================================================================
# SHARED HEADER AND FOOTER
# =============================================================================


def header(p, current):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        cls = ' class="nav-cta"' if href == "contact/" else ""
        items.append(f'<li{cls}><a href="{p}{href}"{cur}>{label}</a></li>')
    home_cur = ' aria-current="page"' if current == "" else ""
    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-row">
    <a class="brand" href="{p or './'}"{home_cur}>
      <span class="brand-name">Trish Leto<span class="dot">.</span></span>
      <span class="brand-tag">Gen<span class="x">X</span> UGC Creator</span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav"><span class="bars" aria-hidden="true"></span>Menu</button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul>{"".join(items)}</ul>
    </nav>
  </div>
</header>"""


def footer(p):
    links = "".join(f'<li><a href="{p}{h}">{l}</a></li>' for h, l in NAV[:-1])
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <span class="brand-name">Trish Leto<span class="dot" style="color:var(--coral-soft)">.</span></span>
        <p>GenX UGC creator and model, U.S. Navy veteran and public speaker in Tampa, FL. Short-form videos for brands that sell to real grown-ups.</p>
        {partner_badge()}
      </div>
      <nav aria-label="Footer">
        <p class="footer-h">Pages</p>
        <ul class="footer-list"><li><a href="{p or './'}">Home</a></li>{links}<li><a href="{p}contact/">Contact</a></li></ul>
      </nav>
      <div>
        <p class="footer-h">Say hi</p>
        <ul class="footer-list">
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li>{ext(TIKTOK_URL, 'TikTok <span class="handle">' + esc(TIKTOK_HANDLE) + '</span>')}</li>
          <li>{ext(INSTAGRAM_URL, 'Instagram <span class="handle">' + esc(INSTAGRAM_HANDLE) + '</span>')}</li>
          {f"<li>{ext(FACEBOOK_URL, 'Facebook')}</li>" if LINK_FACEBOOK else ""}
          <li>{ext(STAN_URL, 'My guides <span class="handle">on Stan</span>')}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; {YEAR} Trish Leto. PAID collabs ONLY.</span>
      <span>Social numbers as of {STATS_AS_OF}.</span>
    </div>
  </div>
</footer>"""


# =============================================================================
# STRUCTURED DATA
# =============================================================================

PERSON_ID = BASE + "#trish"
SERVICE_ID = BASE + "#ugc"
SITE_ID = BASE + "#website"


def person():
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": NAME,
        "jobTitle": JOB_TITLE,
        "description": "GenX UGC creator and model, U.S. Navy veteran and public speaker. "
                       "Makes short-form product videos and b-roll for brands.",
        "url": BASE,
        "image": BASE + "assets/img/trish-coffee-640.webp",
        "email": "mailto:" + EMAIL,
        "address": {"@type": "PostalAddress", "addressLocality": CITY, "addressRegion": REGION, "addressCountry": "US"},
        "knowsAbout": ["User-generated content (UGC)", "Short-form video", "TikTok Shop",
                       "Content strategy", "Hooks and content ideas"],
        "sameAs": [TIKTOK_URL, INSTAGRAM_URL] + ([FACEBOOK_URL] if LINK_FACEBOOK else []) + [STAN_URL],
    }


def service():
    offers = [
        ("Monthly UGC retainer", "A batch of short-form videos plus b-roll every month, delivered to Google Drive."),
        ("Per-project UGC", "Videos and b-roll for one product or launch, delivered to Google Drive."),
    ] + [(pk["name"] + " (with Simply Digital)", pk["trish"] + " Simply Digital: " + pk["sd"]) for pk in PACKAGES]
    # serviceType belongs to Service, not ProfessionalService, so it sits on
    # each offered Service below.
    return {
        "@type": "ProfessionalService",
        "@id": SERVICE_ID,
        "name": "Trish Leto UGC",
        "description": "User-generated content (UGC) videos for brands: talking heads, yap style, lifestyle, "
                       "product demos and b-roll, delivered to Google Drive on a monthly retainer or per project.",
        "url": BASE + "work-with-me/",
        "image": BASE + OG_IMAGE,
        "email": "mailto:" + EMAIL,
        "address": {"@type": "PostalAddress", "addressLocality": CITY, "addressRegion": REGION, "addressCountry": "US"},
        "founder": {"@id": PERSON_ID},
        "areaServed": {"@type": "Country", "name": "United States"},
        "knowsLanguage": "en",
        "sameAs": [TIKTOK_URL, INSTAGRAM_URL],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "UGC services",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d,
                                                   "serviceType": "User-generated content (UGC) video creation"}}
                for n, d in offers
            ],
        },
    }


def event():
    return {
        "@type": "Event",
        "name": EVENT["name"],
        "description": f"Trish Leto speaks in the {EVENT['track']}: {EVENT['talk']}.",
        "startDate": EVENT["start"],
        "endDate": EVENT["end"],
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/MixedEventAttendanceMode",
        "location": [
            {"@type": "Place", "name": f"{EVENT['name']}, {EVENT['locality']}",
             "address": {"@type": "PostalAddress", "streetAddress": EVENT["street"],
                         "addressLocality": EVENT["locality"], "addressRegion": EVENT["region"],
                         "postalCode": EVENT["postal"], "addressCountry": "US"}},
            {"@type": "VirtualLocation", "url": EVENT["url"]},
        ],
        "image": [BASE + "assets/img/dominate-summit-2026-860.webp"],
        "url": EVENT["url"],
        "organizer": {"@type": "Organization", "name": EVENT["organizer"], "url": EVENT["organizer_url"]},
        "performer": {"@id": PERSON_ID},
    }


def graph(page):
    url = BASE + page["slug"]
    page_type = page.get("page_type", "WebPage")
    webpage = {
        "@type": page_type,
        "@id": url + "#webpage",
        "url": url,
        "name": page["title"],
        "description": page["description"],
        "isPartOf": {"@id": SITE_ID},
        "about": {"@id": PERSON_ID},
        "inLanguage": "en-US",
        "primaryImageOfPage": {"@type": "ImageObject", "url": BASE + OG_IMAGE},
    }
    if page_type == "ProfilePage":
        webpage["mainEntity"] = {"@id": PERSON_ID}
    nodes = [
        {"@type": "WebSite", "@id": SITE_ID, "url": BASE, "name": NAME, "inLanguage": "en-US",
         "publisher": {"@id": PERSON_ID}},
        person(),
        webpage,
    ]
    if page["slug"]:
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        nodes.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": page["crumb"], "item": url},
        ]})
    for extra in page.get("schema", []):
        nodes.append(extra())
    data = {"@context": "https://schema.org", "@graph": nodes}
    return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


# =============================================================================
# PAGE SHELL
# =============================================================================


def head(page, p, absolute=False):
    url = BASE + page["slug"]
    robots = "index,follow,max-image-preview:large" if (INDEXABLE and not page.get("noindex")) else "noindex,nofollow"
    asset = (lambda r: BASE + r) if absolute else (lambda r: p + r)
    css_v, js_v = file_hash("assets/css/style.css"), file_hash("assets/js/site.js")
    og_type = page.get("og_type", "website")
    canonical = "" if page.get("noindex") else f'<link rel="canonical" href="{url}">\n'
    ld = "" if page.get("noindex") else f'<script type="application/ld+json">\n{graph(page)}\n</script>\n'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page['title'])}</title>
<meta name="description" content="{esc(page['description'])}">
<meta name="robots" content="{robots}">
{canonical}<meta name="author" content="{NAME}">
<meta name="theme-color" content="#17193b">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(page['title'])}">
<meta property="og:description" content="{esc(page['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE + OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(OG_IMAGE_ALT)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page['title'])}">
<meta name="twitter:description" content="{esc(page['description'])}">
<meta name="twitter:image" content="{BASE + OG_IMAGE}">
<meta name="twitter:image:alt" content="{esc(OG_IMAGE_ALT)}">
<link rel="icon" href="{asset('favicon.ico')}" sizes="32x32">
<link rel="icon" href="{asset('favicon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{asset('apple-touch-icon.png')}">
<link rel="manifest" href="{asset('site.webmanifest')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&amp;display=swap">
<link rel="stylesheet" href="{asset('assets/css/style.css')}?v={css_v}">
<script>document.documentElement.classList.add("js")</script>
<script src="{asset('assets/js/site.js')}?v={js_v}" defer></script>
{ld}</head>"""


def render(page):
    depth = page["slug"].count("/")
    p = "../" * depth
    absolute = page.get("absolute", False)
    if absolute:
        p = BASE
    body = page["body"](p)
    return f"""{head(page, p, absolute)}
<body>
{header(p, page['slug'] if not page.get('noindex') else None)}
<main id="main">
{body}
</main>
{footer(p)}
</body>
</html>
"""


# =============================================================================
# PAGES
# =============================================================================


def home(p):
    formats = "".join(f'<div class="card format"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for t, d in FORMATS)
    niches = "".join(f"<li>{esc(n)}</li>" for n in NICHES)
    vids = "".join(vid_card(next(v for v in PRODUCT_VIDEOS if v["id"] == i), p) for i in HOME_VIDEO_IDS)
    pkgs = "".join(f"<li>{esc(pk['name'])}</li>" for pk in PACKAGES)
    # Mobile order: words, then her photo (so her face is in the first
    # screen), then the buttons. On wide screens the photo sits to the right.
    # The partner badge lives in the packages band and the footer, not here.
    return f"""<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="kicker">GenX UGC creator &middot; Model &middot; Speaker</p>
      <h1>UGC for brands that sell to <span class="hl">real grown-ups</span>.</h1>
      <p class="lede">I'm Trish Leto. I make short-form videos about products I ACTUALLY use: honest, funny, zero fluff, and built to stop the scroll.</p>
    </div>
    <div class="hero-photo">
      <div class="frame">{img(p, "trish-coffee", [400, 640], "Trish Leto smiling over a pink coffee mug in her kitchen", "(min-width: 900px) 420px, min(76vw, 340px)", (640, 800), eager=True)}</div>
      <span class="sticker sticker-genx" aria-hidden="true"><span><b>Gen X</b>creator</span></span>
      <span class="sticker sticker-navy">{ICON_STAR}Navy veteran</span>
    </div>
    <div class="hero-actions">
      <p class="lede hero-more">You get batches of videos and b-roll in your Google Drive, ready to run.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="{p}work-with-me/">Work with me</a>
        <a class="btn btn-ghost" href="{p}portfolio/">Watch my videos</a>
      </div>
      <p class="hero-note">PAID collabs ONLY &middot; U.S. Navy veteran &middot; Based in Tampa, FL<br>
      <a href="{p}work-with-me/#packages">Official Simply Digital Partner for UGC + ads packages</a></p>
    </div>
  </div>
</section>

{stats_band()}

<section class="section" aria-labelledby="make-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">What I make</p>
      <h2 id="make-h">Videos that sound like a real person. Because I am one!</h2>
      <p class="lede">Vertical, hook-first and made for TikTok, TikTok Shop, Instagram Reels and your ads.</p>
    </div>
    <div class="grid formats">{formats}</div>
    <h3 style="margin-top:2.6rem">Categories I love</h3>
    <ul class="chips" aria-label="Categories">{niches}</ul>
  </div>
</section>

<section class="band-alt section" aria-label="What UGC means">
  <div class="wrap">
    <blockquote class="bigquote"><span class="q">&ldquo;</span>UGC is fancy lingo for creating short-form videos for brands about products you're ALREADY using &hellip; and getting paid!<span class="q">&rdquo;</span></blockquote>
    <p class="quote-by">Trish, explaining UGC better than any marketing textbook</p>
  </div>
</section>

<section class="section" aria-labelledby="how-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">How it works</p>
      <h2 id="how-h">Film it in batches. Drop it in your Drive. BOOM!</h2>
    </div>
    <ol class="steps steps-3">
      <li><h3>Send the brief</h3><p>Your product, your audience, and where the videos will run.</p></li>
      <li><h3>I film in batches</h3><p>Hooks, talking points and b-roll, all shot around your product in my real life.</p></li>
      <li><h3>Delivered to Google Drive</h3><p>Ready for your team or your ad account. Monthly retainer or one-time project.</p></li>
    </ol>
    <p style="margin-top:1.8rem"><a class="text-link" href="{p}work-with-me/">Retainers, packages and what I won't do &rarr;</a></p>
  </div>
</section>

<section class="band-alt section" aria-labelledby="recent-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Recent work</p>
      <h2 id="recent-h">Fresh off my TikTok</h2>
      <p class="lede">A few recent product videos. Tap Play to watch here, or open them on TikTok.</p>
    </div>
    <div class="vids">{vids}</div>
    {disclosure()}
    <div class="btn-row"><a class="btn btn-primary" href="{p}portfolio/">See the full portfolio</a></div>
  </div>
</section>

<section class="band-ink section" aria-labelledby="pkg-h">
  <div class="wrap split">
    <div>
      <p class="kicker">UGC + paid ads</p>
      <h2 id="pkg-h">Need the videos and the ads? Get both.</h2>
      <p class="lede">I'm an Official Simply Digital Partner. When you need content and the ads to run it, we quote them together: I make the videos, Simply Digital runs the ads, pages and tracking.</p>
      <div class="btn-row"><a class="btn btn-sun" href="{p}work-with-me/#packages">See the packages</a></div>
    </div>
    <div>
      <ul class="ticks" style="font-size:1.08rem">{pkgs}</ul>
      <p class="small" style="margin-top:1.2rem">Every package is a custom quote.</p>
      <div style="margin-top:1.4rem">{partner_badge()}</div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="speak-h">
  <div class="wrap split split-rev">
    <div>
      <p class="kicker">Speaking</p>
      <h2 id="speak-h">I make the videos. Then I teach the craft on stage.</h2>
      <p>{event_status()}</p>
      {home_event_line()}
      <div class="btn-row"><a class="btn btn-ghost" href="{p}speaking/">Speaking and booking</a></div>
    </div>
    <div class="photo">{img(p, "trish-military-creator-con", [400, 600], "Trish Leto speaking into a microphone in front of the Military Creator Con backdrop", "(min-width: 880px) 540px, 92vw", (600, 408))}</div>
  </div>
</section>

{cta_band(p)}"""


def work_with_me(p):
    pk_cards = "".join(f"""<div class="card pkg">
  <h3>{esc(pk['name'])}</h3>
  <dl>
    <div><dt>Trish</dt><dd>{esc(pk['trish'])}</dd></div>
    <div><dt>Simply Digital</dt><dd>{esc(pk['sd'])}</dd></div>
  </dl>
  <span class="quote-chip">Custom quote</span>
</div>""" for pk in PACKAGES)
    niches = ", ".join(n.lower() for n in NICHES[:-1]) + " and " + NICHES[-1].lower()
    return f"""<section class="page-hero">
  <div class="wrap">
    <p class="kicker">Work with me</p>
    <h1>UGC videos and b-roll, delivered every month and ready to run.</h1>
    <p class="lede">UGC is fancy lingo for short-form videos about products I'm ALREADY using, made for your brand to post and run as ads. Here is exactly how working together works.</p>
  </div>
</section>

<section class="section-tight" aria-labelledby="ways-h" style="padding-top:0">
  <div class="wrap">
    <h2 id="ways-h" class="sr-only">Two ways to work together</h2>
    <div class="grid grid-2">
      <div class="card card-feature">
        <span class="card-label">My favorite</span>
        <h3 style="font-size:1.7rem">Monthly retainer</h3>
        <p>A batch of videos plus b-roll every month, uploaded to your Google Drive. Fresh creative on a schedule, so your ads never go stale.</p>
        <p class="card-voice">Send me the product and I will crank those videos out, no problem!</p>
        <ul class="ticks">
          <li>A set number of videos each month</li>
          <li>B-roll with every batch</li>
          <li>Delivered to a shared Google Drive folder</li>
        </ul>
        <span class="quote-chip">Custom quote</span>
      </div>
      <div class="card">
        <span class="card-label">One and done</span>
        <h3 style="font-size:1.7rem">Per project</h3>
        <p>One product, one launch, one batch. A great way to test UGC or kick off a TikTok Shop launch.</p>
        <ul class="ticks">
          <li>Videos and b-roll for one product or launch</li>
          <li>Your pick of formats</li>
          <li>Delivered to Google Drive</li>
        </ul>
        <span class="quote-chip">Custom quote</span>
      </div>
    </div>
  </div>
</section>

<section class="band-alt section" aria-labelledby="get-h">
  <div class="wrap split">
    <div>
      <p class="kicker">What you get</p>
      <h2 id="get-h">Content that feels real, because it is.</h2>
      <p class="lede">I use the product before I film it. Then I build every video around a hook that earns the next three seconds.</p>
    </div>
    <ul class="ticks" style="font-size:1.06rem">
      <li>Vertical short-form videos for TikTok, TikTok Shop, Reels and ads</li>
      <li>Talking heads, yap style, lifestyle or product demos: your pick</li>
      <li>B-roll: hands, pours, textures and your product in real life</li>
      <li>Files delivered to Google Drive, batch by batch</li>
      <li>Categories: {esc(niches)}</li>
    </ul>
  </div>
</section>

<section class="section" aria-labelledby="process-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">The process</p>
      <h2 id="process-h">Five steps. That's REALLY it!</h2>
    </div>
    <ol class="steps steps-5">
      <li><h3>Email the brief</h3><p>Product, audience, where the videos will run, and your timeline. The <a href="{p}contact/">contact page</a> has a checklist.</p></li>
      <li><h3>Get a custom quote</h3><p>Based on how many videos, how much b-roll, and how you plan to use them.</p></li>
      <li><h3>Ship the product</h3><p>I use it for real before I film. No fake reviews, ever.</p></li>
      <li><h3>I film in batches</h3><p>Hooks, angles and b-roll, all in one go.</p></li>
      <li><h3>Drive delivery</h3><p>Your files land in Google Drive, ready for your team or your ads.</p></li>
    </ol>
  </div>
</section>

<section id="packages" class="band-ink section anchor-target" aria-labelledby="packages-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Packages with Simply Digital</p>
      <h2 id="packages-h">UGC + paid ads packages</h2>
      <p class="lede">I'm an Official Simply Digital Partner. When you need the videos and the ads, we quote them together. I make the content. Simply Digital runs the ads, landing pages and tracking.</p>
      <div style="margin-top:1.4rem">{partner_badge()}</div>
    </div>
    <div class="grid grid-2">{pk_cards}</div>
    <div class="btn-row">
      <a class="btn btn-sun" href="{esc(mailto('Package inquiry: UGC + ads', PACKAGE_TEMPLATE))}">Ask about a package</a>
      {ext(SD_URL, 'Visit Simply Digital', 'btn btn-ghost')}
    </div>
  </div>
</section>

<section class="section" aria-labelledby="nope-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Ground rules</p>
      <h2 id="nope-h">What I don't do</h2>
      <p class="lede">A few hard NOs. Saves us both an email!</p>
    </div>
    <ul class="nope">
      <li><strong>Alcohol, tobacco or gambling</strong><span>Not for any budget.</span></li>
      <li><strong>Managing your brand accounts</strong><span>I don't run or post to your brand accounts, and I don't start new accounts for you (&ldquo;canvas UGC&rdquo;). I make the content. You post it.</span></li>
      <li><strong>Fake reviews</strong><span>I only talk about products I have actually used.</span></li>
      <li><strong>Kids' faces</strong><span>Kids on camera are hands only, never faces.</span></li>
      <li><strong>Unpaid collabs</strong><span>PAID collabs ONLY. Gifted product alone is not a deal.</span></li>
    </ul>
  </div>
</section>

<section class="band-alt section" aria-labelledby="faq-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Questions</p>
      <h2 id="faq-h">Good questions. STRAIGHT answers.</h2>
    </div>
    <div class="faq">
      <details><summary>What does it cost?</summary><div class="answer"><p>Every job is a custom quote. It depends on how many videos you need, how much b-roll, and where and for how long you will run them. Email me the details and I will send a quote.</p></div></details>
      <details><summary>Do you post the videos for us?</summary><div class="answer"><p>Not on your brand accounts, and I don't start new accounts for you. You get the files and post or run them wherever you like.{OWN_TIKTOK_LINE if POSTS_ON_OWN_TIKTOK_CONFIRMED else ""}</p></div></details>
      <details><summary>Can we run your videos as ads?</summary><div class="answer"><p>Yes. Tell me where and for how long when you ask for a quote, and it goes into the quote. If you want the ads run for you too, ask about a <a href="#packages">package with Simply Digital</a>.</p></div></details>
      <details><summary>Which categories are a fit?</summary><div class="answer"><p>Supplements, food and drink, pets, cars, kitchen and appliances, plants and gardening, makeup, skin care and hair care. Not a fit: alcohol, tobacco and gambling.</p></div></details>
      <details><summary>How do the videos get to us?</summary><div class="answer"><p>Through a shared Google Drive folder, batch by batch.</p></div></details>
    </div>
  </div>
</section>

{cta_band(p)}"""


def portfolio(p):
    tops = "".join(f"""<div class="top-vid">
  <div class="num">{v['views']}<small>views</small></div>
  <h3 style="margin:0">{esc(v['title'])}</h3>
  <p>{esc(v['text'])}</p>
  {ext(tiktok_url(v['id']), 'Watch on TikTok<span class="sr-only">: ' + esc(v['title']) + '</span>', 'btn btn-sun')}
</div>""" for v in TOP_VIDEOS)
    vids = "".join(vid_card(v, p) for v in PRODUCT_VIDEOS)
    life = "".join(vid_card(v, p) for v in LIFESTYLE_VIDEOS)
    return f"""<section class="page-hero">
  <div class="wrap">
    <p class="kicker">Portfolio</p>
    <h1>My UGC portfolio: real products, real reactions.</h1>
    <p class="lede">Samples from my own TikTok, including recent TikTok Shop product videos. Tap Play to watch a video right here, or open it on TikTok.</p>
  </div>
</section>

{stats_band()}

<section class="section" aria-labelledby="top-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Top performers</p>
      <h2 id="top-h">The ones that took off</h2>
    </div>
    <div class="grid grid-2">{tops}</div>
    <p class="small" style="margin-top:1rem">View counts as of {STATS_AS_OF}.</p>
  </div>
</section>

<section class="band-alt section" aria-labelledby="products-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Product videos</p>
      <h2 id="products-h">Recent TikTok Shop and product videos</h2>
      <p class="lede">Supplements, drinks and skin care. Each one opens with a hook built to stop the scroll.</p>
    </div>
    <div class="vids">{vids}</div>
    {disclosure()}
  </div>
</section>

<section class="section-tight" aria-labelledby="life-h">
  <div class="wrap life">
    <div>
      <p class="kicker">Lifestyle and faith</p>
      <h2 id="life-h">Not every post sells something.</h2>
      <p class="lede">Some are just me, my coffee and my faith. Same voice, same real life your customers see in my product videos.</p>
    </div>
    <div class="vids vids-solo">{life}</div>
  </div>
</section>

<section class="band-alt section" aria-labelledby="pf-next-h">
  <div class="wrap split">
    <div>
      <p class="kicker">Your product next?</p>
      <h2 id="pf-next-h">Want videos like these for your brand?</h2>
      <p class="lede">Monthly retainer or one project. Videos and b-roll in your Google Drive.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="{p}work-with-me/">How it works</a>
        <a class="btn btn-ghost" href="{p}contact/">Get a quote</a>
      </div>
    </div>
    <div class="card">
      <h3>Formats I shoot</h3>
      <ul class="ticks">{"".join(f"<li><strong>{esc(t)}:</strong> {esc(d)}</li>" for t, d in FORMATS)}</ul>
    </div>
  </div>
</section>

{cta_band(p)}"""


# DRAFT, Trish to rewrite or approve before launch: her story in her words.
# Kept to facts from her bios until she does (no invented backstory).
ABOUT_STORY = """<p>I make short-form videos for brands about products I ACTUALLY use. Supplements, kitchen gadgets, skin care, my morning coffee: if I use it, I can show it on camera exactly the way it fits my life.</p>
      <p>I'm Gen X, and maybe your customers are too. That's my lane: real talk for real grown-ups.</p>
      <p>I'm also a proud U.S. Navy veteran.</p>"""


def stan_card(sp):
    note = f'<p class="small" style="margin-top:0.8rem">{esc(sp["disclosure"])}</p>' if sp.get("disclosure") else ""
    link = "See the course" if sp.get("disclosure") else "Check it out"
    return f"""<div class="card">
  <span class="card-label">{esc(sp['label'])}</span>
  <h3>{esc(sp['title'])}</h3>
  <p>{esc(sp['text'])}</p>{note}
  <p style="margin-top:1rem">{ext(sp['url'], link + '<span class="sr-only">: ' + esc(sp['title']) + '</span>', 'text-link')}</p>
</div>"""


def about(p):
    stan = "".join(stan_card(sp) for sp in STAN_PRODUCTS)
    return f"""<section class="page-hero">
  <div class="wrap split">
    <div>
      <p class="kicker">About</p>
      <h1>Hi, I'm Trish Leto.</h1>
      <p class="lede">GenX UGC creator and model, U.S. Navy veteran and public speaker, based in Tampa, Florida.</p>
      {ABOUT_STORY}
      <div class="btn-row">
        <a class="btn btn-primary" href="{p}work-with-me/">Work with me</a>
        <a class="btn btn-ghost" href="{p}portfolio/">See my videos</a>
      </div>
    </div>
    <div class="hero-photo">
      <div class="frame">{img(p, "trish-coffee", [400, 640], "Trish Leto smiling over a pink coffee mug in her kitchen", "(min-width: 880px) 420px, 86vw", (640, 800), eager=True)}</div>
      <span class="sticker sticker-navy">{ICON_STAR}U.S. Navy veteran</span>
    </div>
  </div>
</section>

<section class="band-alt section" aria-labelledby="facts-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Quick facts</p>
      <h2 id="facts-h">The short version</h2>
    </div>
    <div class="grid grid-auto">
      <div class="card"><span class="card-label">Based in</span><h3>Tampa, FL</h3><p>Filming in real kitchens, real backyards and real life.</p></div>
      <div class="card"><span class="card-label">I make</span><h3>UGC videos + b-roll</h3><p>Talking heads, yap style, lifestyle and product demos.</p></div>
      <div class="card"><span class="card-label">How I work</span><h3>Retainer or project</h3><p>Batches delivered to your Google Drive.</p></div>
      <div class="card"><span class="card-label">Vibe</span><h3>Faith-friendly, coffee-powered</h3><p>Plus popup TikTok LIVEs when the mood strikes.</p></div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="partner-h">
  <div class="wrap split">
    <div class="photo">{img(p, "trish-military-creator-con", [400, 600], "Trish Leto speaking into a microphone in front of the Military Creator Con backdrop", "(min-width: 880px) 540px, 92vw", (600, 408))}<p class="photo-cap" style="padding:0 1rem 1rem">Teaching creators at Military Creator Con.</p></div>
    <div>
      <p class="kicker">Partner</p>
      <h2 id="partner-h">Content from me. Ads from Simply Digital.</h2>
      <p class="lede">I'm an Official Simply Digital Partner for UGC + paid ads packages. Brands that want the videos and the ads can get both, quoted together.</p>
      <div style="margin-top:1.4rem">{partner_badge()}</div>
      <p style="margin-top:1.4rem"><a class="text-link" href="{p}work-with-me/#packages">See the packages &rarr;</a></p>
    </div>
  </div>
</section>

<section class="band-alt section" aria-labelledby="learn-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">For creators</p>
      <h2 id="learn-h">Want to make UGC yourself?</h2>
      <p class="lede">Turn your doom scrolling into money rolling! My guides live on my Stan store, plus a UGC course I recommend.</p>
    </div>
    <div class="grid grid-3">{stan}</div>
    <div class="btn-row">{ext(STAN_URL, 'Visit my Stan store', 'btn btn-primary')}</div>
  </div>
</section>

{cta_band(p)}"""


TALKS = [
    # Her DOMINATE Power Track slot is a quick three-minute talk, so it is
    # labeled "As seen at", never "Signature talk", unless Trish confirms she
    # gives a full-length version.
    ("As seen at DOMINATE 2026", "Control the Scroll",
     "How to grab attention with unlimited content ideas: hooks, formats, and a way to never run out of things to post.", True),
    ("For new creators", "Getting set up for brand deals",
     "What you need before the first pitch: payment gateways, contracts, pitch emails and DMs, bio setup, and where to find paid work.", True),
    ("For brands and creators", "GenX content that works",
     "Video formulas for reaching Gen X, from the creator of The GenX Content Survival Guide.", TALK_GENX_CONFIRMED),
]


def speaking_event_facts():
    if EVENT_PAST:
        return f"""<dl class="facts">
          <div><dt>When</dt><dd>{EVENT['date_label']}</dd></div>
          <div><dt>Where</dt><dd>{EVENT['where_label']}</dd></div>
          <div><dt>Host</dt><dd>{EVENT['organizer']}</dd></div>
        </dl>"""
    return f"""<dl class="facts">
          <div><dt>When</dt><dd>{EVENT['date_label']}<br>Summit: {EVENT['time_label']}<br><strong>My {EVENT['track']}: {EVENT['track_time_label']}</strong></dd></div>
          <div><dt>Where</dt><dd>{EVENT['where_label']}</dd></div>
          <div><dt>Host</dt><dd>{EVENT['organizer']}</dd></div>
        </dl>
        <p class="small">The {EVENT['track']} is a series of quick three-minute talks. Virtual attendance is free for everyone, per the organizer.</p>
        <div class="btn-row">{ext(EVENT['url'], 'Event details and registration', 'btn btn-primary')}</div>"""


def speaking(p):
    talks = [t for t in TALKS if t[3]]
    cards = "".join(f'<div class="card"><span class="card-label">{esc(lab)}</span><h3>{esc(h)}</h3><p>{esc(d)}</p></div>'
                    for lab, h, d, _ in talks)
    cols = "grid-3" if len(talks) == 3 else "grid-2"
    topics = "Content ideas that never run dry, and how to get set up for brand deals that PAY"
    if TALK_GENX_CONFIRMED:
        topics += ", plus GenX content that actually works"
    return f"""<section class="page-hero">
  <div class="wrap">
    <p class="kicker">Speaking</p>
    <h1>I teach people how to control the scroll.</h1>
    <p class="lede">{topics}. Practical, funny and straight to the point.</p>
    <div class="btn-row">
      <a class="btn btn-primary" href="{esc(mailto('Speaking inquiry: [event name]', SPEAKING_TEMPLATE))}">Book me to speak</a>
      <a class="btn btn-ghost" href="#topics">See my topics</a>
    </div>
  </div>
</section>

<section class="section-tight" aria-labelledby="event-h" style="padding-top:0">
  <div class="wrap">
    <article class="event">
      <div class="event-media">{img(p, "dominate-summit-2026", [480, 860], "DOMINATE Entrepreneurial Summit speaker graphic featuring Trish Leto: October 9, 10:30 to 5:30, Clearwater, FL and virtual", "(min-width: 880px) 560px, 100vw", (860, 665))}</div>
      <div class="event-body">
        {event_status()}
        <h2 id="event-h" style="font-size:clamp(1.6rem,1.2rem + 1.6vw,2.3rem)">{EVENT['name']}</h2>
        <p class="talk">{EVENT['track']}: {esc(EVENT['talk'])}</p>
        {speaking_event_facts()}
      </div>
    </article>
  </div>
</section>

<section class="band-alt section" aria-labelledby="mcc-h">
  <div class="wrap split">
    <div class="photo">{img(p, "trish-military-creator-con", [400, 600], "Trish Leto presenting at Military Creator Con, microphone in hand, in front of the event backdrop", "(min-width: 880px) 540px, 92vw", (600, 408))}</div>
    <div>
      <p class="kicker">Recent stage</p>
      <h2 id="mcc-h">Military Creator Con</h2>
      <p class="lede">I walked creators through getting set up for brand deals: payment gateways, contracts, pitch emails and DMs, bio setup, and the best platforms to find paid work.</p>
    </div>
  </div>
</section>

<section id="topics" class="section anchor-target" aria-labelledby="topics-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Talk topics</p>
      <h2 id="topics-h">What I can bring to your stage</h2>
    </div>
    <div class="grid {cols}">{cards}</div>
    <p style="margin-top:1.6rem">A great fit for entrepreneur events, creator conferences, veteran and military-connected communities, and virtual summits. In person or online.</p>
  </div>
</section>

<section class="band-coral section" aria-labelledby="book-h">
  <div class="wrap split">
    <div>
      <p class="kicker">Book me</p>
      <h2 id="book-h">Bring the energy to your event!</h2>
      <p class="lede">Email me with the details below and I will get back to you.</p>
      <div class="btn-row"><a class="btn btn-sun" href="{esc(mailto('Speaking inquiry: [event name]', SPEAKING_TEMPLATE))}">Email a speaking inquiry</a></div>
    </div>
    <ul class="ticks">
      <li>Event name and date</li>
      <li>In person (where) or virtual</li>
      <li>Who is in the audience, and about how many</li>
      <li>The topic you would like</li>
      <li>Format and length</li>
      <li>Speaker budget or honorarium</li>
    </ul>
  </div>
</section>"""


def contact(p):
    return f"""<section class="page-hero">
  <div class="wrap">
    <p class="kicker">Contact</p>
    <h1>Let's work together.</h1>
    <p class="lede">Email is the fastest way to reach me. PAID collabs ONLY, please!</p>
  </div>
</section>

<section class="section-tight" aria-labelledby="email-h" style="padding-top:0">
  <div class="wrap">
    <div class="email-box">
      <h2 id="email-h" class="label" style="font-family:var(--font-body);margin:0">Collab email</h2>
      <a class="email-big" href="mailto:{EMAIL}">{EMAIL.replace("@", "<wbr>@")}</a>
      <div class="btn-row" style="margin-top:0">
        <a class="btn btn-sun" href="{esc(mailto('UGC collab: [your brand]', UGC_TEMPLATE))}">Start an email</a>
        <button class="btn btn-ghost copy-btn" type="button" hidden data-copy="{EMAIL}" data-status="copy-email-status" data-done="Email address copied.">Copy email address</button>
      </div>
      <p id="copy-email-status" class="copy-status" role="status" aria-live="polite"></p>
    </div>
  </div>
</section>

<section class="section-tight" aria-labelledby="paths-h">
  <div class="wrap">
    <div class="section-head">
      <p class="kicker">Pick your reason</p>
      <h2 id="paths-h">What can I help with?</h2>
      <p class="lede">Each button opens an email with the right subject line and a short checklist already filled in.</p>
    </div>
    <div class="grid grid-3">
      <div class="card"><span class="card-label">Brands</span><h3>UGC videos</h3><p>Videos and b-roll for your product, on a monthly retainer or per project.</p><p style="margin-top:1.1rem"><a class="btn btn-primary" href="{esc(mailto('UGC collab: [your brand]', UGC_TEMPLATE))}">Email about UGC</a></p></div>
      <div class="card"><span class="card-label">Brands</span><h3>UGC + ads package</h3><p>My videos plus paid ads, landing pages and tracking from Simply Digital.</p><p style="margin-top:1.1rem"><a class="btn btn-primary" href="{esc(mailto('Package inquiry: UGC + ads', PACKAGE_TEMPLATE))}">Email about a package</a></p></div>
      <div class="card"><span class="card-label">Events</span><h3>Speaking</h3><p>Your stage, breakout or virtual summit.</p><p style="margin-top:1.1rem"><a class="btn btn-primary" href="{esc(mailto('Speaking inquiry: [event name]', SPEAKING_TEMPLATE))}">Email about speaking</a></p></div>
    </div>
  </div>
</section>

<section class="band-alt section" aria-labelledby="include-h">
  <div class="wrap split">
    <div>
      <p class="kicker">Save a round trip</p>
      <h2 id="include-h">What to include in your email</h2>
      <ul class="ticks">
        <li>Your brand and website</li>
        <li>The product, and whether you can ship it</li>
        <li>How many videos, which formats, and whether you want b-roll</li>
        <li>Where the videos will run (organic, TikTok Shop or paid ads) and for how long</li>
        <li>Your timeline</li>
        <li>Your budget range</li>
      </ul>
      <p style="margin-top:1.4rem">Not a fit: alcohol, tobacco and gambling. <a href="{p}work-with-me/">See what I make and what I don't.</a></p>
    </div>
    <div>
      <h3>Or copy this template</h3>
      <pre class="template" id="ugc-template">{esc(UGC_TEMPLATE)}</pre>
      <div class="btn-row" style="margin-top:0.9rem">
        <button class="btn btn-ghost copy-btn" type="button" hidden data-copy="" data-copy-from="ugc-template" data-status="copy-template-status" data-done="Template copied. Paste it into an email to {EMAIL}.">Copy the template</button>
      </div>
      <p id="copy-template-status" class="copy-status" role="status" aria-live="polite" style="color:var(--coral)"></p>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="dm-h">
  <div class="wrap measure">
    <p class="kicker">Social</p>
    <h2 id="dm-h">Prefer to say hi on social?</h2>
    <p class="lede">Find me on {ext(TIKTOK_URL, 'TikTok ' + esc(TIKTOK_HANDLE))} and {ext(INSTAGRAM_URL, 'Instagram ' + esc(INSTAGRAM_HANDLE))}. For paid collabs, please use email so nothing gets lost in the DMs.</p>
  </div>
</section>"""


def not_found(p):
    return f"""<section class="section">
  <div class="wrap measure">
    <p class="kicker">404</p>
    <h1>Well, that scrolled right off the page.</h1>
    <p class="lede">The page you were looking for is not here. Try one of these instead.</p>
    <div class="btn-row">
      <a class="btn btn-primary" href="{p}">Home</a>
      <a class="btn btn-ghost" href="{p}work-with-me/">Work with me</a>
      <a class="btn btn-ghost" href="{p}contact/">Contact</a>
    </div>
  </div>
</section>"""


PAGES = [
    {"slug": "", "file": "index.html", "crumb": "Home", "body": home,
     "title": "Trish Leto | GenX UGC Creator, Navy Veteran and Speaker",
     "description": "Trish Leto is a GenX UGC creator and model in Tampa, FL. Scroll-stopping product videos "
                    "and b-roll for brands that sell to real grown-ups. Paid collabs only.",
     "schema": [service]},
    {"slug": "work-with-me/", "file": "work-with-me/index.html", "crumb": "Work with me", "body": work_with_me,
     "title": "Work With Me: UGC Retainers and Packages | Trish Leto",
     "description": "Hire Trish Leto for UGC: batches of short-form videos and b-roll delivered to Google Drive "
                    "on a monthly retainer or per project, plus UGC + paid ads packages.",
     "schema": [service]},
    {"slug": "portfolio/", "file": "portfolio/index.html", "crumb": "Portfolio", "body": portfolio,
     "title": "UGC Portfolio: TikTok Product Videos | Trish Leto",
     "description": "Watch Trish Leto's UGC: TikTok Shop and product videos for supplements, drinks and skin care, "
                    "plus a 1.1M-view TikTok. 30.1K followers as of October 2026.",
     "page_type": "CollectionPage"},
    {"slug": "about/", "file": "about/index.html", "crumb": "About", "body": about,
     "title": "About Trish Leto: GenX UGC Creator and Navy Veteran",
     "description": "Meet Trish Leto: GenX UGC creator and model, U.S. Navy veteran and public speaker in Tampa, FL, "
                    "making honest product videos for brands.",
     "page_type": "ProfilePage", "og_type": "profile"},
    {"slug": "speaking/", "file": "speaking/index.html", "crumb": "Speaking", "body": speaking,
     "title": "Speaking: Control the Scroll | Trish Leto, Speaker",
     "description": ("Book Trish Leto to speak on content ideas and getting set up for UGC brand deals. "
                     + ("She spoke in the Power Track at the DOMINATE Summit, Oct 9, 2026." if EVENT_PAST else
                        "Catch her Power Track at the DOMINATE Summit, October 9, 2026.")),
     "schema": [] if EVENT_PAST else [event]},
    {"slug": "contact/", "file": "contact/index.html", "crumb": "Contact", "body": contact,
     "title": "Contact Trish Leto: Paid UGC Collabs and Speaking",
     "description": "Email Trish Leto at trishletospeaks@gmail.com for paid UGC collabs, UGC + ads packages "
                    "and speaking. What to include so you get a quote fast.",
     "page_type": "ContactPage"},
    {"slug": "404.html", "file": "404.html", "crumb": "Not found", "body": not_found,
     "title": "Page not found | Trish Leto",
     "description": "This page does not exist. Head back to Trish Leto's home page to see her UGC work and contact details.",
     "noindex": True, "absolute": True},
]


# =============================================================================
# ROBOTS, SITEMAP, MANIFEST
# =============================================================================


def robots_txt():
    if INDEXABLE:
        return f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n"
    return "# Not indexed yet. Flip INDEXABLE in build.py when the site is approved.\nUser-agent: *\nDisallow: /\n"


def sitemap_xml():
    rows = "".join(
        f"  <url><loc>{BASE}{pg['slug']}</loc><lastmod>{BUILD_DATE}</lastmod></url>\n"
        for pg in PAGES if not pg.get("noindex"))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")


def manifest():
    return json.dumps({
        "name": NAME, "short_name": NAME,
        "icons": [{"src": "android-chrome-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "android-chrome-512.png", "sizes": "512x512", "type": "image/png"}],
        "theme_color": "#17193b", "background_color": "#fbf7f1", "display": "browser",
    }, indent=2) + "\n"


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build():
    for pg in PAGES:
        write(pg["file"], render(pg))
    write("robots.txt", robots_txt())
    write("sitemap.xml", sitemap_xml())
    write("site.webmanifest", manifest())
    print(f"Built {len(PAGES)} pages into docs/. BASE={BASE} INDEXABLE={INDEXABLE} TODAY={TODAY} EVENT_PAST={EVENT_PAST}")


# =============================================================================
# AUDIT
# =============================================================================

DASHES = {chr(0x2014): "em dash", chr(0x2013): "en dash"}
TEXT_EXT = (".html", ".css", ".js", ".xml", ".txt", ".webmanifest", ".md", ".py", ".svg")


def audit():
    errors, warnings = [], []
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for fn in filenames:
            if fn.endswith(TEXT_EXT):
                path = os.path.join(dirpath, fn)
                text = open(path, encoding="utf-8").read()
                for ch, label in DASHES.items():
                    if ch in text:
                        errors.append(f"{os.path.relpath(path, SRC)}: contains an {label}")

    if not PARTNER_CONFIRMED:
        msg = ("partner badge is in the HTML but PARTNER_CONFIRMED is False: do not push until Eddie "
               "confirms the partner agreement is signed (or names her a partner regardless)")
        (errors if INDEXABLE else warnings).append(msg)

    want_robots = "index,follow" if INDEXABLE else "noindex,nofollow"
    for pg in PAGES:
        path = os.path.join(ROOT, pg["file"])
        s = open(path, encoding="utf-8").read()
        name = pg["file"]
        if len(re.findall(r"<h1[\s>]", s)) != 1:
            errors.append(f"{name}: needs exactly one <h1>")
        title = re.search(r"<title>(.*?)</title>", s).group(1)
        if len(html.unescape(title)) > 65:
            warnings.append(f"{name}: title is {len(html.unescape(title))} chars (aim for 65 or fewer)")
        desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', s).group(1))
        if not 70 <= len(desc) <= 160:
            warnings.append(f"{name}: description is {len(desc)} chars (aim for 70 to 160)")
        robots = re.search(r'<meta name="robots" content="(.*?)">', s).group(1)
        if pg.get("noindex"):
            if robots != "noindex,nofollow":
                errors.append(f"{name}: 404 must stay noindex")
        elif not robots.startswith(want_robots):
            errors.append(f"{name}: robots meta is {robots}, expected {want_robots}")
        if not pg.get("noindex"):
            if f'<link rel="canonical" href="{BASE}{pg["slug"]}">' not in s:
                errors.append(f"{name}: canonical missing or wrong")
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
                try:
                    json.loads(block)
                except ValueError as e:
                    errors.append(f"{name}: JSON-LD does not parse ({e})")
        for tag in re.findall(r"<img\b[^>]*>", s):
            if " alt=" not in tag:
                errors.append(f"{name}: <img> without alt: {tag[:80]}")
            if " width=" not in tag or " height=" not in tag:
                errors.append(f"{name}: <img> without width/height: {tag[:80]}")
        for m in re.finditer(r'href="https://stan\.store/affiliates/', s):
            if "Affiliate link" not in s[max(0, m.start() - 600):m.start() + 600]:
                errors.append(f"{name}: affiliate link without an affiliate disclosure next to it")
        if EVENT_PAST and ("EventScheduled" in s or ">Upcoming<" in s):
            errors.append(f"{name}: the event is over but the page still calls it upcoming")
        if pg.get("absolute"):
            continue
        base_dir = os.path.dirname(path)
        refs = re.findall(r'\s(?:href|src)="([^"]+)"', s)
        for srcset in re.findall(r'srcset="([^"]+)"', s):
            refs += [part.strip().split(" ")[0] for part in srcset.split(",")]
        for ref in refs:
            for one in [ref]:
                one = one.strip().split(" ")[0]
                if not one or one.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                target = os.path.normpath(os.path.join(base_dir, one.split("#")[0].split("?")[0]))
                if one.split("#")[0].split("?")[0].endswith("/") or os.path.isdir(target):
                    target = os.path.join(target, "index.html")
                if not os.path.exists(target):
                    errors.append(f"{name}: broken link {one}")

    robots_txt_now = open(os.path.join(ROOT, "robots.txt")).read()
    if INDEXABLE != ("Sitemap:" in robots_txt_now):
        errors.append("robots.txt does not match INDEXABLE")
    for rel in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "android-chrome-192.png",
                "android-chrome-512.png", OG_IMAGE):
        if not os.path.exists(os.path.join(ROOT, rel)):
            errors.append(f"missing {rel} (run tools/make_icons.py)")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"Audit: {len(errors)} errors, {len(warnings)} warnings")
    return not errors


if __name__ == "__main__":
    if "--audit" not in sys.argv:
        build()
    sys.exit(0 if audit() else 1)
