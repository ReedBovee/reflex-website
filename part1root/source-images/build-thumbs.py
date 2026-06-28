#!/usr/bin/env python3
"""Build uploads-thumbs.html — a LIGHTWEIGHT browsing gallery.

Same content as uploads.html (read from manifest.json), but each image is a
downscaled, more-compressed JPEG thumbnail (~560px wide) so the whole page is
a couple MB instead of tens of MB. uploads.html remains the full-resolution
archive; this is just for fast browsing/curation.

    python3 source-images/build-thumbs.py
"""
import json, base64, os, sys, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "manifest.json")
OUT = os.path.join(ROOT, "uploads-thumbs.html")
MAXW = 560


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def thumb_uri(path):
    im = cv2.imread(path)
    if im is None:
        return ""
    h, w = im.shape[:2]
    if w > MAXW:
        im = cv2.resize(im, (MAXW, int(h * MAXW / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 68])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def main():
    man = json.load(open(MANIFEST))
    groups, count = {}, 0
    for im in man.get("images", []):
        src = os.path.join(HERE, im["file"])
        if not os.path.exists(src):
            print(f"  ! missing, skipping: {im['file']}", file=sys.stderr)
            continue
        folder = os.path.dirname(im["file"]) or "Unsorted"
        count += 1
        pick = im.get("pick", "keep")
        pl = {"hero": "★ Hero", "keep": "Keep", "cut": "Cut"}[pick]
        badge = f'<span class="b {pick}">{pl}</span>'
        card = (f'<figure class="card pk-{pick}" data-rank="{ {"hero":0,"keep":1,"cut":2}[pick] }"><img loading="lazy" src="{thumb_uri(src)}" '
                f'alt="{esc(im.get("title",""))}"><figcaption>'
                f'<h2>{esc(im.get("title", im["file"]))}</h2>'
                f'<p class="cap">{esc(im.get("caption",""))}</p>'
                f'<dl><div><dt>File</dt><dd><code>{esc(im["file"])}</code></dd></div>'
                f'<div><dt>Size</dt><dd>{im.get("width","?")}×{im.get("height","?")}</dd></div>'
                f'<div><dt>For</dt><dd>{esc(im.get("intendedPage","—"))}</dd></div></dl>'
                f'{badge}</figcaption></figure>')
        rank = {"hero": 0, "keep": 1, "cut": 2}[pick]
        groups.setdefault(folder, []).append((rank, card))

    order = (["Unsorted"] if "Unsorted" in groups else []) + sorted(
        f for f in groups if f != "Unsorted")
    secs = []
    for f in order:
        cards = [c for _, c in sorted(groups[f], key=lambda t: t[0])]
        nh = sum(1 for r, _ in groups[f] if r == 0)
        secs.append(f'<h2 class="folder">{esc(f)} <span class="fc">{len(cards)}</span>'
                    f'<span class="fh">{nh} hero</span></h2>'
                    f'<div class="grid">' + "".join(cards) + "</div>")
    body = "\n".join(secs)
    nhero = sum(1 for im in man.get("images", []) if im.get("pick") == "hero")
    nkeep = sum(1 for im in man.get("images", []) if im.get("pick") == "keep")
    ncut = sum(1 for im in man.get("images", []) if im.get("pick") == "cut")

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Uploaded images (thumbnails) — Reflex Technologies</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0c0e10;--panel:#15191c;--line:#262c31;--ink:#e8edf0;--muted:#9aa6ad;--teal:#15ebdf;--amber:#e6a24a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,sans-serif;line-height:1.5}}
header.top{{max-width:1200px;margin:0 auto;padding:44px 24px 20px}}
.kick{{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--teal)}}
h1{{font-family:Archivo,sans-serif;font-weight:800;font-size:clamp(26px,5vw,40px);margin:.3em 0 .2em}}
header.top p{{color:var(--muted);max-width:60ch}}.cnt{{color:var(--amber);font-family:"JetBrains Mono",monospace}}
main{{max-width:1200px;margin:0 auto;padding:24px}}
h2.folder{{font-family:Archivo,sans-serif;font-size:20px;margin:30px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:center}}
h2.folder:first-child{{margin-top:0}}.fc{{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--amber);border:1px solid var(--amber);border-radius:999px;padding:1px 9px}}
.grid{{display:grid;gap:20px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}}
.card{{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}}
.card img{{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#000}}
figcaption{{padding:14px 16px}}figcaption h2{{font-family:Archivo,sans-serif;font-size:16px;margin:0 0 5px}}
.cap{{color:var(--muted);font-size:13px;margin:0 0 12px}}
dl{{display:grid;grid-template-columns:1fr 1fr;gap:7px 14px;margin:0 0 12px}}dl div{{min-width:0}}
dt{{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
dd{{margin:2px 0 0;font-size:13px}}code{{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--teal);word-break:break-all}}
.b{{display:inline-block;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding:3px 9px;border-radius:999px;border:1px solid}}
.b.hero{{color:#06121a;background:var(--teal);border-color:var(--teal);font-weight:600}}
.b.keep{{color:var(--ink);border-color:var(--muted)}}
.b.cut{{color:#ff7a7a;border-color:#ff7a7a}}
.pk-hero{{outline:2px solid var(--teal);outline-offset:-2px}}
.pk-cut{{opacity:.4;filter:grayscale(.5)}}.pk-cut:hover{{opacity:1;filter:none}}
.fh{{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--teal);border:1px solid var(--teal);border-radius:999px;padding:1px 9px;margin-left:2px}}
</style></head><body>
<header class="top"><div class="kick">Reflex Technologies · internal</div><h1>Uploaded images — thumbnails</h1>
<p>Lightweight browsing copy. <span class="cnt">{count} images</span> across {len(order)} folders.
Curation: <b style="color:var(--teal)">{nhero} hero</b> · {nkeep} keep · <span style="color:#ff7a7a">{ncut} cut</span>.
Heroes are outlined; cuts are dimmed (hover to view). Full-res originals live in <code>uploads.html</code> / <code>source-images/</code>.</p></header>
<main>{body}</main></body></html>"""
    open(OUT, "w").write(html)
    print(f"Wrote {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB, {count} images)")


if __name__ == "__main__":
    main()
