#!/usr/bin/env python3
"""Build uploads.html — a self-contained thumbnail gallery of all uploaded
images, read from source-images/manifest.json + the image files beside it.

Each image is embedded as a lossless base64 data URI, so uploads.html doubles
as the durable archive (the raw .jpg files don't survive this cloud container,
but the committed HTML does). Re-run after adding entries to the manifest.

    python3 source-images/build-gallery.py
"""
import json, base64, mimetypes, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "manifest.json")
OUT = os.path.join(ROOT, "uploads.html")


def data_uri(path):
    mt = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mt};base64," + base64.b64encode(f.read()).decode()


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def main():
    with open(MANIFEST) as f:
        data = json.load(f)
    imgs = data.get("images", [])

    groups = {}
    count = 0
    for im in imgs:
        src = os.path.join(HERE, im["file"])
        if not os.path.exists(src):
            print(f"  ! missing image file, skipping: {im['file']}", file=sys.stderr)
            continue
        folder = os.path.dirname(im["file"]) or "Unsorted"
        uri = data_uri(src)
        placed = im.get("placed")
        badge = ('<span class="badge placed">Placed</span>' if placed
                 else '<span class="badge pending">Not placed</span>')
        dims = f'{im.get("width","?")}×{im.get("height","?")}'
        count += 1
        groups.setdefault(folder, []).append(f"""      <figure class="card">
        <a class="thumbwrap" target="_blank" rel="noopener" title="Open full size">
          <img loading="lazy" src="{uri}" alt="{esc(im.get('title',''))}">
        </a>
        <figcaption>
          <h2>{esc(im.get('title', im['file']))}</h2>
          <p class="cap">{esc(im.get('caption',''))}</p>
          <dl class="meta">
            <div><dt>File</dt><dd><code>{esc(im['file'])}</code></dd></div>
            <div><dt>Size</dt><dd>{dims}</dd></div>
            <div><dt>For</dt><dd>{esc(im.get('intendedPage','—'))}</dd></div>
            <div><dt>Uploaded</dt><dd>{esc(im.get('uploaded','—'))}</dd></div>
          </dl>
          {badge}
        </figcaption>
      </figure>""")

    # render groups: "Unsorted" first, then folders alphabetically
    order = (["Unsorted"] if "Unsorted" in groups else []) + sorted(
        f for f in groups if f != "Unsorted")
    sections = []
    for folder in order:
        cards = groups[folder]
        label = "Unsorted" if folder == "Unsorted" else folder
        sections.append(
            f'    <h2 class="folder">{esc(label)} '
            f'<span class="fcount">{len(cards)}</span></h2>\n'
            f'    <div class="grid">\n' + "\n".join(cards) + "\n    </div>")
    grid = "\n".join(sections) if sections else '<p class="empty">No images uploaded yet.</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Uploaded images — Reflex Technologies (internal)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0c0e10; --panel:#15191c; --line:#262c31; --ink:#e8edf0;
    --muted:#9aa6ad; --teal:#15ebdf; --amber:#e6a24a;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:Inter,system-ui,sans-serif;line-height:1.55}}
  header.top{{padding:48px 24px 24px;border-bottom:1px solid var(--line);
    max-width:1200px;margin:0 auto}}
  .kicker{{font-family:"JetBrains Mono",monospace;font-size:12px;
    letter-spacing:.18em;text-transform:uppercase;color:var(--teal)}}
  h1{{font-family:Archivo,sans-serif;font-weight:800;font-size:clamp(28px,5vw,44px);
    margin:.3em 0 .2em;letter-spacing:-.01em}}
  header.top p{{color:var(--muted);max-width:60ch;margin:.4em 0 0}}
  .count{{color:var(--amber);font-family:"JetBrains Mono",monospace}}
  main{{max-width:1200px;margin:0 auto;padding:32px 24px 80px}}
  h2.folder{{font-family:Archivo,sans-serif;font-weight:700;font-size:20px;
    margin:34px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--line);
    display:flex;align-items:center;gap:10px}}
  h2.folder:first-child{{margin-top:0}}
  .fcount{{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--amber);
    border:1px solid var(--amber);border-radius:999px;padding:1px 9px}}
  .grid{{display:grid;gap:24px;
    grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}}
  .card{{margin:0;background:var(--panel);border:1px solid var(--line);
    border-radius:14px;overflow:hidden;display:flex;flex-direction:column}}
  .thumbwrap{{display:block;aspect-ratio:4/3;background:#000;overflow:hidden}}
  .thumbwrap img{{width:100%;height:100%;object-fit:cover;display:block;
    transition:transform .35s ease}}
  .thumbwrap:hover img{{transform:scale(1.04)}}
  figcaption{{padding:16px 18px 18px}}
  figcaption h2{{font-family:Archivo,sans-serif;font-size:17px;font-weight:700;
    margin:0 0 6px}}
  .cap{{color:var(--muted);font-size:13.5px;margin:0 0 14px}}
  dl.meta{{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;margin:0 0 14px}}
  dl.meta div{{min-width:0}}
  dl.meta dt{{font-family:"JetBrains Mono",monospace;font-size:10.5px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
  dl.meta dd{{margin:2px 0 0;font-size:13.5px}}
  dl.meta code{{font-family:"JetBrains Mono",monospace;font-size:12.5px;
    color:var(--teal);word-break:break-all}}
  .badge{{display:inline-block;font-family:"JetBrains Mono",monospace;
    font-size:11px;letter-spacing:.08em;text-transform:uppercase;
    padding:4px 10px;border-radius:999px;border:1px solid}}
  .badge.pending{{color:var(--amber);border-color:var(--amber)}}
  .badge.placed{{color:var(--teal);border-color:var(--teal)}}
  .empty{{color:var(--muted)}}
  footer{{max-width:1200px;margin:0 auto;padding:0 24px 60px;color:var(--muted);
    font-size:13px}}
  footer code{{font-family:"JetBrains Mono",monospace;color:var(--amber)}}
</style>
</head>
<body>
  <header class="top">
    <div class="kicker">Reflex Technologies · internal</div>
    <h1>Uploaded images</h1>
    <p>Photos uploaded and held for later placement across the site.
       <span class="count">{count} image{'' if count==1 else 's'}</span> archived.
       Click any thumbnail to open it full size.</p>
  </header>
  <main>
{grid}
  </main>
  <script>
    // Each image is embedded once (in the <img>); point its "open full size"
    // link at the same data so the base64 isn't duplicated in the file.
    document.querySelectorAll('.thumbwrap').forEach(function(a){{
      var img = a.querySelector('img');
      if (img) a.href = img.currentSrc || img.src;
    }});
  </script>
  <footer>
    Generated from <code>source-images/manifest.json</code> by
    <code>source-images/build-gallery.py</code>. Not linked from the public
    site (<code>noindex</code>).
  </footer>
</body>
</html>
"""
    with open(OUT, "w") as f:
        f.write(html)
    print(f"Wrote {OUT} with {count} image(s).")


if __name__ == "__main__":
    main()
