"""CSV export for Media Buddy."""

import csv

from .scanner import human_size

COLUMNS = [
    "Job #", "File Name", "Type", "Extension", "Size", "Size (GB)",
    "Size (bytes)", "Date Created", "Date Modified", "Frames", "Frame Range",
    "Missing Frames", "Folder", "Full Path",
]


def _fmt_dt(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def write_csv(path, records, job_number=""):
    """Write records to ``path``. UTF-8 with BOM so Excel shows accents correctly."""
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for r in records:
            writer.writerow([
                job_number,
                r.name,
                r.category,
                r.ext.upper(),
                human_size(r.size),
                f"{r.size / 1024 ** 3:.3f}",
                r.size,
                _fmt_dt(r.created),
                _fmt_dt(r.modified),
                r.frames,
                r.frame_range,
                r.missing_frames if r.frames > 1 else "",
                r.folder,
                r.path,
            ])
    return len(records)
