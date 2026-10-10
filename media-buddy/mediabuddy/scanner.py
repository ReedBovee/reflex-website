"""Drive / folder walker for Media Buddy.

Pure Python, no GUI imports, so it can be tested on its own and run from a
background thread. Results are delivered in per-folder batches through a
callback so the interface can fill in live.
"""

import os
import re
import shutil
import string
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime

from . import formats

# Folders that are operating-system bookkeeping, never customer media.
SYSTEM_DIRS = {
    "$recycle.bin", "system volume information", "$extend", "recycler",
    ".spotlight-v100", ".trashes", ".fseventsd", ".temporaryitems",
    ".documentrevisions-v100", ".pkinstallsandboxmanager", "lost+found",
    ".appledouble", "__macosx",
}

# Film-scan formats are grouped even in short runs; generic image formats only
# when the run looks like a scan (long run, long zero-padded frame number) so a
# folder of camera photos (IMG_1234.jpg) still lists every picture.
SCAN_SEQUENCE_EXTS = {"dpx", "cin", "exr"}
GENERIC_MIN_FRAMES = 24
GENERIC_MIN_DIGITS = 6

_FRAME_RE = re.compile(r"^(?P<prefix>.*?)(?P<num>\d+)(?P<ext>\.[^.]+)$")


@dataclass
class MediaRecord:
    name: str
    category: str
    ext: str
    size: int
    created: datetime | None
    modified: datetime | None
    folder: str
    path: str
    frames: int = 1
    first_frame: int | None = None
    last_frame: int | None = None
    missing_frames: int = 0

    @property
    def frame_range(self):
        if self.frames <= 1 or self.first_frame is None:
            return ""
        return f"{self.first_frame}-{self.last_frame}"


@dataclass
class ScanOptions:
    include_video: bool = True
    include_images: bool = True
    include_audio: bool = False
    group_sequences: bool = True
    include_hidden: bool = False


@dataclass
class ScanStats:
    folders: int = 0
    files_seen: int = 0
    matched_files: int = 0
    errors: list = field(default_factory=list)


def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "bytes":
                return f"{int(size)} bytes"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def _created_time(st):
    """Best available creation time for the platform, or None."""
    birth = getattr(st, "st_birthtime", None)  # macOS, Windows on Python 3.12+
    if birth:
        return datetime.fromtimestamp(birth)
    if sys.platform == "win32":  # older Python on Windows: st_ctime is creation
        return datetime.fromtimestamp(st.st_ctime)
    return None  # Linux does not reliably expose a creation time


def _is_hidden(entry):
    if entry.name.startswith("."):
        return True
    if sys.platform == "win32":
        try:
            attrs = entry.stat(follow_symlinks=False).st_file_attributes
            return bool(attrs & 0x2 or attrs & 0x4)  # HIDDEN or SYSTEM
        except (OSError, AttributeError):
            return False
    return False


def list_drives():
    """Return [(path, label)] for mounted drives/volumes on this computer."""
    drives = []
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        type_names = {2: "Removable", 3: "Local", 4: "Network", 5: "CD/DVD", 6: "RAM"}
        bitmask = kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if not bitmask & (1 << i):
                continue
            root = f"{letter}:\\"
            name_buf = ctypes.create_unicode_buffer(261)
            kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(root), name_buf, 261, None, None, None, None, 0
            )
            kind = type_names.get(kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)), "Drive")
            details = kind
            try:
                details += f", {human_size(shutil.disk_usage(root).total)}"
            except OSError:
                pass
            drives.append((root, f"{letter}:  {name_buf.value or 'No label'}  ({details})"))
        return drives

    bases = ["/Volumes"] if sys.platform == "darwin" else ["/media", "/run/media", "/mnt"]
    for base in bases:
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if os.path.ismount(path) or base == "/Volumes":
                drives.append((path, name))
            elif os.path.isdir(path):  # /media/<user>/<volume>
                for sub in sorted(os.listdir(path)):
                    if os.path.ismount(os.path.join(path, sub)):
                        drives.append((os.path.join(path, sub), sub))
    drives.insert(0, ("/", "/  (whole computer)"))
    return drives


def _count_missing(numbers):
    return (max(numbers) - min(numbers) + 1) - len(set(numbers))


def _group_sequences(records):
    """Collapse frame-per-file runs within one folder into single records."""
    buckets = {}
    singles = []
    for rec in records:
        if rec.ext not in formats.SEQUENCE_CANDIDATES:
            singles.append(rec)
            continue
        m = _FRAME_RE.match(rec.name)
        if not m:
            singles.append(rec)
            continue
        key = (m["prefix"], len(m["num"]), m["ext"].lower())
        buckets.setdefault(key, []).append((int(m["num"]), rec))

    out = list(singles)
    for (prefix, digits, ext), items in buckets.items():
        ext_bare = ext.lstrip(".")
        is_scan_fmt = ext_bare in SCAN_SEQUENCE_EXTS
        qualifies = (len(items) >= 2) if is_scan_fmt else (
            len(items) >= GENERIC_MIN_FRAMES and digits >= GENERIC_MIN_DIGITS
        )
        if not qualifies:
            out.extend(rec for _, rec in items)
            continue
        items.sort(key=lambda pair: pair[0])
        nums = [n for n, _ in items]
        recs = [r for _, r in items]
        first, last = nums[0], nums[-1]
        created = [r.created for r in recs if r.created]
        modified = [r.modified for r in recs if r.modified]
        hashes = "#" * digits
        out.append(MediaRecord(
            name=f"{prefix}[{str(first).zfill(digits)}-{str(last).zfill(digits)}]{ext}",
            category=recs[0].category + " Sequence",
            ext=ext_bare,
            size=sum(r.size for r in recs),
            created=min(created) if created else None,
            modified=max(modified) if modified else None,
            folder=recs[0].folder,
            path=os.path.join(recs[0].folder, f"{prefix}{hashes}{ext}"),
            frames=len(recs),
            first_frame=first,
            last_frame=last,
            missing_frames=_count_missing(nums),
        ))
    return out


def scan(root, options, on_batch, on_folder=None, cancel_event=None):
    """Walk ``root`` and report media files.

    on_batch(list[MediaRecord]) is called once per folder that had matches.
    on_folder(path) is called as each folder is entered (for a status line).
    Returns ScanStats. Stops early if ``cancel_event`` is set.
    """
    cancel_event = cancel_event or threading.Event()
    stats = ScanStats()
    stack = [root]

    while stack:
        if cancel_event.is_set():
            break
        folder = stack.pop()
        stats.folders += 1
        if on_folder:
            on_folder(folder)

        matches = []
        subdirs = []
        try:
            with os.scandir(folder) as it:
                entries = list(it)
        except OSError as exc:
            stats.errors.append(f"{folder}: {exc.strerror or exc}")
            continue

        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    lowered = entry.name.lower()
                    if lowered in SYSTEM_DIRS:
                        continue
                    if not options.include_hidden and _is_hidden(entry):
                        continue
                    subdirs.append(entry.path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError as exc:
                stats.errors.append(f"{entry.path}: {exc.strerror or exc}")
                continue

            stats.files_seen += 1
            name = entry.name
            # macOS resource-fork shadows ("._IMG_0001.JPG") litter drives that
            # have been plugged into a Mac; they are not real media.
            if name.startswith("._"):
                continue
            if not options.include_hidden and _is_hidden(entry):
                continue
            ext = os.path.splitext(name)[1].lower().lstrip(".")
            if not ext:
                continue
            category = formats.classify(
                ext, options.include_video, options.include_images, options.include_audio
            )
            if not category:
                continue
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError as exc:
                stats.errors.append(f"{entry.path}: {exc.strerror or exc}")
                continue
            stats.matched_files += 1
            matches.append(MediaRecord(
                name=name,
                category=category,
                ext=ext,
                size=st.st_size,
                created=_created_time(st),
                modified=datetime.fromtimestamp(st.st_mtime),
                folder=folder,
                path=entry.path,
            ))

        if matches:
            if options.group_sequences:
                matches = _group_sequences(matches)
            matches.sort(key=lambda r: r.name.lower())
            on_batch(matches)

        # Reverse-sorted push so folders are visited in alphabetical order.
        stack.extend(sorted(subdirs, key=str.lower, reverse=True))

    return stats
