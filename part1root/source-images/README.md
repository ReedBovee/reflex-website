# source-images — image archive

Working archive of images uploaded for the Reflex Technologies site, held for
later placement.

## Master originals: 2TB SSD (always connected)

The **2TB SSD** is the master source of all full-resolution originals and is
always plugged into whatever computer is in use. This `source-images/` folder is
the **curated / processed working mirror** — the subset that has been uploaded
into the project, plus any composites and edits made here (stitched panoramas,
retouched versions, etc.). When in doubt, the SSD is the source of truth for
originals.

## Contents

- `manifest.json` — metadata for every archived image (title, caption,
  dimensions, intended page, placement status). The `masterOriginals` field
  records the note above.
- `Film/` — film-related shots (and other named folders as they're added).
- Composites created in-project: `reception-lobby-pano.jpg`,
  `reception-lobby-pano-retouched.jpg`, `reflex-logo-closeup-pano.jpg`
  (their source frames are kept alongside).
- `build-gallery.py` — regenerates `../uploads.html`, a self-contained,
  folder-grouped thumbnail gallery with each image embedded as base64.

## Rebuild the gallery

```bash
python3 source-images/build-gallery.py
```
