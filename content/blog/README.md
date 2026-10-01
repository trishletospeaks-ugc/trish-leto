# Blog posts

One file per post: `content/blog/<slug>.md`. `build.py` turns each one into `docs/blog/<slug>/index.html`, adds it to the hub at `/blog/` and to `sitemap.xml`, and checks it. This README is skipped by the build.

## Workflow for one post

```bash
# 1. Photos: search a PHYSICAL real-world scene, then save one (hero is 16:9, inline is 3:2)
python3 tools/blog_images.py <slug> hero "woman filming a smoothie in a home kitchen"
python3 tools/blog_images.py <slug> hero "woman filming a smoothie in a home kitchen" --pick 2
python3 tools/blog_images.py <slug> inline "hands unboxing a skin care jar on a bathroom counter" --pick 1
#    Paste the printed JSON into "hero" / "inline_image" and add your own "alt".
#    Add --pixabay to search Pixabay instead of Pexels.

# 2. Write content/blog/<slug>.md (format below), then check it without touching docs/
python3 build.py --post <slug> --out /tmp/trish-post-check

# 3. Full build (every page, every post, the audit and the internal-link check)
python3 build.py
```

`--post` exits non-zero on any error. Links to posts that are not written yet, and a missing related post, are warnings there; the full build fails on any internal link to a page that does not exist.

## File format

The file starts with a line `---`, then a JSON object, then another line `---`, then the Markdown body.

```
---
{
  "slug": "ugc-brief-template",
  "title": "UGC Brief Template: What to Send a Creator | Trish Leto",
  "h1": "The UGC brief template I wish every brand sent me",
  "description": "140 to 160 characters, with the primary keyword in it.",
  "date": "2026-10-01",
  "updated": "2026-10-01",
  "cluster": "ugc-for-brands",
  "pillar": false,
  "primary_keyword": "ugc brief template",
  "secondary_keywords": ["ugc creative brief", "how to brief a ugc creator"],
  "audience": "brands",
  "excerpt": "One or two sentences for the hub card.",
  "hero": {"file": "ugc-brief-template-hero", "alt": "...", "credit": "...", "credit_url": "https://...", "source_url": "https://..."},
  "inline_image": {"file": "ugc-brief-template-inline", "alt": "...", "credit": "...", "credit_url": "https://...", "source_url": "https://..."},
  "table": {"caption": "...", "columns": ["...", "..."], "rows": [["...", "..."]], "source": "...", "source_url": "https://..."},
  "chart": {"title": "...", "unit": "%", "data": [{"label": "...", "value": 42}], "source": "...", "source_url": "https://..."},
  "tiktok": ["7690644146540776734"],
  "faq": [{"q": "...", "a": "..."}],
  "references": [{"title": "...", "publisher": "...", "url": "https://...", "quote": "exact sentence, under 25 words", "supports": "the claim it backs"}],
  "related": ["slug-one", "slug-two", "slug-three"]
}
---
Body in Markdown...
```

| Key | Rule |
|---|---|
| `slug` | kebab-case, the same as the file name |
| `title` | the SEO `<title>`, 60 characters or fewer, primary keyword near the front |
| `h1` | the one H1 on the page (also the card title and the breadcrumb) |
| `description` | 140 to 160 characters |
| `date`, `updated` | YYYY-MM-DD. A post dated after today renders with noindex and stays out of the hub, the sitemap and related posts. Rebuild and push on or after its date to publish it. |
| `cluster`, `pillar` | cluster id (kebab-case); exactly one pillar (`true`) per cluster |
| `audience` | `brands`, `creators` or `athletes`. Picks the call to action: brands go to /work-with-me/ plus email, creators to her Stan guides, athletes to /nil-consulting/ (the contact page until that page exists) |
| `hero`, `inline_image` | from `tools/blog_images.py`, plus your own descriptive `alt` |
| `table` | every row has one cell per column; the first cell is the row header |
| `chart` | a horizontal bar chart; 2 or more items; values are numbers of 0 or more, taken from the cited source. `unit` is `%`, `$`, `x` or a word (`views`), or empty |
| `tiktok` | optional, 0 to 2 video IDs from `PRODUCT_VIDEOS`, `LIFESTYLE_VIDEOS` or `TOP_VIDEOS` in `build.py` |
| `faq` | optional, 2 to 4 items. Also emitted as FAQPage JSON-LD |
| `references` | 4 or more, https only. `quote` (under 25 words) and `supports` are kept for the audit and never rendered |
| `related` | 3 slugs. Live ones show first; the build fills the rest from the same cluster, then the newest posts |

## Body

- Headings: `##` and `###` only (never a single `#`). The first heading is an `##`; use 2 or more.
- Paragraphs, `-` lists, `1.` lists, `**bold**`, `*italic*`, `[anchor](url)` links and `> ` quotes. No raw HTML.
- Placeholders, each on its own line: `[[IMAGE]]`, `[[TABLE]]`, `[[CHART]]` and `[[CTA]]` exactly once each; `[[TIKTOK]]` once when `tiktok` lists videos (it adds the FTC note that a product shown does not mean that brand hired her).
- Internal links start at the site root: `/blog/<slug>/`, `/work-with-me/`, `/nil-consulting/`, `/portfolio/`, `/about/`, `/speaking/`, `/contact/`. The build rewrites them to relative links. Use 3 or more, including the cluster pillar and at least one service page (`/work-with-me/`, `/nil-consulting/` or `/speaking/`).
- Every external link in the body, and the table and chart `source_url`, must also be in `references`.
- 1,200 to 2,000 words (placeholders, table, chart, FAQ and references do not count).

## House rules the check enforces

- No em dashes, no en dashes, no Unicode ellipsis (type three periods).
- Simply Digital is never mentioned in a post. The ads partner stays unnamed.

## House rules nobody can automate

- Never invent anything: no clients, testimonials, results, prices, credentials, quotes or personal stories. Use only the facts in `RESEARCH-2026-10-01.md` and her `Content Creation Guidelines.rtf` (both in the client folder, outside this repo), and cite every outside stat.
- Write in her voice: playful, direct, GenX humor, faith-friendly. US English.
- Never mention her day job, birthday, age or family. Kids appear on camera hands only, never faces.
- A product in her video is her own content, never a client. Say so.
