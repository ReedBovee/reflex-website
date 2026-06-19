# Reflex Technologies website — project status & handoff

Everything you need to continue this project on another computer. The code is
fully committed and pushed to GitHub, so this file + a clone of the repo is the
complete picture.

---

## 1. Get set up on a new computer

```bash
git clone https://github.com/ReedBovee/reflex-website.git
cd reflex-website
```

That's it — there is **no build step and no dependencies**. Every page is a
single self-contained `.html` file (inline CSS, fonts from Google Fonts CDN,
images embedded as base64). To preview, just open any `.html` file in a browser,
or run any static server, e.g.:

```bash
# pick whichever you have
python -m http.server 8000      # then open http://localhost:8000
npx serve .
```

Requirements: a browser, `git`, and a text editor. Nothing else.

---

## 2. What this is

Marketing site for **Reflex Technologies**, an archival film/video/image
digitization lab at 4100 West Burbank Blvd, Burbank, CA 91505
(818-859-7770, info@reflextechnologies.com). ~15 years in business; specializes
in scanning deteriorated/shrunken film (up to 23% shrinkage) that other labs
decline.

**Design system:** dark theme, fonts Archivo / Inter / JetBrains Mono, teal
(`#15ebdf`) + amber (`#e6a24a`) accents. The full CSS lives in the `<style>`
block of `reflex-film-page.html` — that file is the **style/template reference**;
new pages copy its CSS, logo, header, and footer.

---

## 3. Page-by-page status

| File | Status |
|------|--------|
| `index.html` | ✅ Done — homepage, nav/CTAs fully wired |
| `reflex-film-page.html` | ✅ Done — Film service page (the template reference) |
| `reflex-stills-page.html` | ✅ Done — Photos, slides & negatives |
| `reflex-video-audio-page.html` | ✅ Done — Video & audio tape transfer |
| `reflex-about-page.html` | 🟡 Scaffold — needs real copy |
| `reflex-our-work-page.html` | ✅ Done — 5 real case studies + client roster |
| `reflex-facility-page.html` | 🟡 Scaffold — needs real copy + photos |
| `reflex-quote-page.html` | 🟡 Functional, needs EmailJS keys (see §5) |

All 8 pages are cross-linked; every internal link resolves.

---

## 4. Outstanding work (what's left to do)

1. **Wire the quote form** — paste 3 EmailJS keys (see §5). Highest priority; it's
   the site's main conversion point.
2. **Fill the remaining scaffold pages** — About and Facility. Each has a visible
   amber **DRAFT** banner, inline amber `[bracketed placeholders]`, and HTML
   comments at every photo slot. Replace all amber text with real content:
   - About: founding story, team members, a real headline stat.
   - Facility: real environmental/equipment specs, hours, and a map embed.
   - Our Work is **done** — 5 case studies (MoMA, Frank Zappa, Paramount, Gene
     Kelly, Jim Henson) built from `Case Studies/Reflex Case Studies.pdf`, plus a
     client roster. Source PDF has 22 total if more are wanted later. Note:
     Paramount card is deliberately attributed to Paramount (PDF wrote it as Warner
     Bros.) and kept general — verify film titles before any detail page.
3. **Swap placeholder images** — every band/thumbnail currently reuses one of the
   three Film-page photos as a stand-in. Search the page for
   `background-image:url('data:image/jpeg;base64,` and the adjacent
   `<!-- Replace with a real photo... -->` comments; drop in page-specific photos.
4. **Real social links** — footer LinkedIn/Facebook are still `href="#"`.
5. **Case-study detail pages** — "Read the case study" links are `href="#"`
   placeholders; no detail pages exist yet.

---

## 5. EmailJS setup (quote form)

The form in `reflex-quote-page.html` sends via **EmailJS** (client-side, no
backend). Until the keys are added it shows a fallback message pointing to
phone/email. The owner has a **paid EmailJS account**.

**Where the keys go** — bottom of `reflex-quote-page.html`, in the `<script>`:
```js
var EMAILJS_PUBLIC_KEY  = "YOUR_PUBLIC_KEY";
var EMAILJS_SERVICE_ID  = "YOUR_SERVICE_ID";
var EMAILJS_TEMPLATE_ID = "YOUR_TEMPLATE_ID";
```

**Steps in the EmailJS dashboard (emailjs.com):**
1. **Email Services → Add New Service** → connect the sending inbox → copy the
   **Service ID** (`service_…`).
2. **Email Templates → Create** → set **To Email** = `info@reflextechnologies.com`,
   **Reply To** = `{{email}}`, **Subject** = `New quote request from {{name}}`.
   Body must reference these variables (they match the form field names exactly):
   `{{name}} {{organization}} {{email}} {{phone}} {{media}} {{formats}}
   {{quantity}} {{condition}} {{message}}`. Copy the **Template ID** (`template_…`).
3. **Account → General** → copy the **Public Key**.
4. **Account → Security** (recommended): turn off non-browser API access and add
   the live site domain to **Allowed Origins** (the Public Key is exposed in
   client code).
5. Paste the three values into the script and open the page to test. Sends are
   logged in EmailJS **Email History**.

The form also has: name/email validation, a `_hp` honeypot spam trap,
disabled-while-sending state, and an accessible success/error status line.

---

## 6. How the pages are built (conventions)

- **Shared CSS/logo/footer** come from `reflex-film-page.html`. When scaffolding a
  new page, copy its `<head>` CSS, the logo `<img>` (a base64 PNG, on the header
  and footer), and the footer block.
- **Section flow** (service pages): hero → intro → "the difference" band →
  specs grid → process band → color/restoration band → case study → FAQ → CTA →
  footer.
- **Placeholder markers** (scaffold pages): a `.draft` banner section, inline
  `.ph` spans wrapping `[bracketed]` instructions, and `<!-- Replace with... -->`
  comments at image slots. Strip all of these before publishing.
- **Images**: real photos are base64 JPEGs inline; new slots reuse them as
  placeholders via `style="background-image:url('data:image/jpeg;base64,…')"`.
- **Cross-links**: nav order is Film, Video & Audio, Stills, Our Work, About,
  Facility; the active page carries `aria-current="page"`. "Request a quote"
  buttons → `reflex-quote-page.html`.
- **Editing tip**: the HTML files are large because of embedded base64 images, so
  editors/tools may be slow — search by the structural text (headings, `class=`)
  rather than scrolling.

---

## 7. Git / GitHub notes

- Remote (canonical): `https://github.com/ReedBovee/reflex-website.git`
  (the lowercase `reedbovee` form redirects to it).
- Default branch: `main`. The owner's workflow is commit straight to `main`.
- On Windows, the first `git push` of a session may pop a **Git Credential
  Manager** sign-in window — complete it once and credentials cache for the rest
  of the session.
- The GitHub CLI (`gh`) is **not** installed on the original machine; plain `git`
  is used for everything. Repo settings (archiving, etc.) are done in GitHub's web
  UI.

---

## 8. Not in the repo (and shouldn't be)

- **EmailJS keys** — live in the EmailJS account; add them locally per §5. (They're
  low-risk public keys, but keep secrets out of git on principle.)
- `.claude/` — local Claude Code config, git-ignored.
