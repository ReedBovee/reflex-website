# Reflex Film Tools — phone app

An installable phone app (PWA) built from the four core calculators on
`reflex-film-tools.html`. Same data, same math, re-paginated for a phone:
four tabs instead of one long scrolling page, nothing hanging off the side.

## What's in it

| Tab | Tool |
|-----|------|
| Footage | Film footage calculator — footage / running time / frames, 8mm to 65mm |
| Storage | Disk storage estimator — total size, data rate, size per hour |
| Timecode | Timecode & feet+frames converter |
| Edge code | Date Kodak film by its edge code, plus the SAFETY factory-dot chart |

Deliberately left out (they don't re-paginate well on a phone): identify your
film gauge, reel capacity & runtime, aspect ratios, film formats.

## Files

```
app/
  index.html            the whole app — inline CSS + JS, no dependencies
  manifest.webmanifest  name, icons, colors, standalone display
  sw.js                 service worker: caches the shell so it runs offline
  icons/                app icons generated from the Reflex logo
```

No build step, same as the rest of the site.

## Deploying

Upload the `app/` folder alongside the other pages, so it lives at
`https://reflextechnologies.com/app/`. It must be served over **HTTPS** —
service workers (and therefore installing and offline use) do not work over
plain HTTP. `file://` won't work either; to preview locally run a static
server from the repo root:

```bash
python -m http.server 8000    # then open http://localhost:8000/app/
```

To point people at it, link `app/` from the Film tools page — something like
"Get the phone app".

## Installing on a phone

- **iPhone / iPad** — open the page in Safari, tap Share, then *Add to Home
  Screen*. The app shows this hint automatically on first visit.
- **Android** — Chrome offers an Install prompt; the app surfaces it with an
  Install button.

Once installed it opens full-screen with its own icon and keeps working with
no signal. It also remembers the tab you were last on and your format /
frame-rate choices.

## Notes

- Fonts come from Google Fonts and are cached after the first online load;
  offline first-runs fall back to the system font stack.
- Each tool has **Share result** (the phone share sheet, or clipboard on
  desktop) and **Download CSV**, matching the website's CSV export.
- If the tool math changes on `reflex-film-tools.html`, update the matching
  block in `app/index.html` — the constants and formulas are copied verbatim
  so the two stay in step.
- Bump `VERSION` in `sw.js` whenever you change the app, or installed copies
  will keep serving the cached old shell.
- This is a web app installed to the home screen, not an App Store / Play
  Store listing. A store build would need a native wrapper (Capacitor or
  similar), an Apple Developer account, and a Play Console account.
