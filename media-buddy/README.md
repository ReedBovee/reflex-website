# Media Buddy

Standalone Windows program for Reflex Technologies. Plug in a customer's
drive, double-click `MediaBuddy.exe`, and get a scrollable list of every
video and still image on it, then **Export as CSV**.

Part 1 of the shop-tablet workflow (intake → job/work order # → drive
inventory). This piece is the drive inventory.

## Using it

1. Plug in the drive and double-click **MediaBuddy.exe**. Nothing to install,
   and it runs from a USB stick too.
2. Type the **Job / Work Order #** in the top right (optional). It's stamped
   into every row of the CSV and into the file name.
3. Pick a source:
   - **Entire drive**: choose from the list (press *Refresh drives* if you
     plugged it in after opening the program).
   - **One folder**: press *Choose folder…*
4. Tick what to include: Video, Still images + RAW, Audio (off by default).
5. Press **Start Scan**. Results fill in live. **Stop** ends a scan early and
   keeps what was found so far.
6. Use **Search** and **Show** to narrow the list. Click a column heading to
   sort. Double-click a row to open that folder in Explorer.
7. Press **Export as CSV**. It exports what's currently shown, so filters
   apply. The file opens straight into Excel.

### What it lists

File name, type (Video / Image / RAW Image / Audio / … Sequence), extension,
size, date created, date modified, frame count, folder and full path.

### Built-in lab smarts

- **Film-scan frame sequences**: a folder of `reel01_0086400.dpx …
  reel01_0172800.dpx` shows as **one row** with the frame count, frame range,
  total size and **missing frames** (shown in amber). DPX, Cineon and EXR
  always group; TIFF/PNG/JPEG/DNG group only for long runs (24+ frames with
  6+ digit frame numbers), so a folder of camera photos (`IMG_1234.JPG`)
  still lists every picture. Untick *Collapse film-scan frame sequences* to
  list every frame.
- Skips Mac `._` resource-fork files, the Recycle Bin, System Volume
  Information and other OS clutter.
- Recognizes about 400 extensions: consumer video, MPEG-TS/AVCHD/DVD VOB,
  DV/MXF tape captures, cinema camera (R3D, BRAW, ARRI), every camera RAW,
  DPX/Cineon/EXR, HEIC/AVIF/JPEG XL, PSD and more. The full list is in
  `mediabuddy/formats.py`.

## Getting the .exe

**Easiest:** every push that changes this folder builds it on GitHub.
Open the repo → **Actions** → *Build Media Buddy (Windows .exe)* → latest
run → download **MediaBuddy-windows** from the Artifacts section → unzip.

**On any Windows PC:** install Python 3.10+ from python.org, then
double-click `build.bat`. The program lands in `dist\MediaBuddy.exe`.

Windows SmartScreen may warn the first time because the program isn't
code-signed: click *More info → Run anyway*.

## For developers

```
python MediaBuddy.py                      # run from source
python -m unittest discover -s tests -v   # scan engine tests
```

- `mediabuddy/formats.py`: extension catalog
- `mediabuddy/scanner.py`: drive walker, sequence grouping (no GUI code)
- `mediabuddy/export.py`: CSV writer
- `mediabuddy/app.py`: Tkinter interface
