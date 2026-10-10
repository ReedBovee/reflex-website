import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mediabuddy.export import write_csv  # noqa: E402
from mediabuddy.scanner import ScanOptions, scan  # noqa: E402


def touch(path, size=0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(b"\0" * size)


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        # DPX reel with frames 50 and 51 dropped
        for i in range(1, 101):
            if i not in (50, 51):
                touch(os.path.join(d, "Reel 01", f"reel01_{i:07d}.dpx"), 10)
        # Camera photos must stay individual rows
        for i in range(1, 41):
            touch(os.path.join(d, "Photos", f"IMG_{i:04d}.JPG"), 5)
            touch(os.path.join(d, "Photos", f"._IMG_{i:04d}.JPG"))  # Mac junk
        touch(os.path.join(d, "Photos", "portrait.CR2"))
        touch(os.path.join(d, "Video", "Wedding 1994.mp4"), 1000)
        touch(os.path.join(d, "Video", "tape.wav"))
        touch(os.path.join(d, "Video", "notes.txt"))
        touch(os.path.join(d, "$RECYCLE.BIN", "deleted.mp4"))
        touch(os.path.join(d, ".hidden", "secret.mov"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_scan(self, **opts):
        out = []
        stats = scan(self.tmp.name, ScanOptions(**opts), out.extend)
        return out, stats

    def test_default_scan(self):
        recs, stats = self.run_scan()
        by_name = {r.name: r for r in recs}
        seq = by_name["reel01_[0000001-0000100].dpx"]
        self.assertEqual(seq.frames, 98)
        self.assertEqual(seq.missing_frames, 2)
        self.assertEqual(seq.size, 980)
        self.assertEqual(sum(1 for r in recs if r.name.startswith("IMG_")), 40)
        self.assertFalse(any(r.name.startswith("._") for r in recs))
        self.assertEqual(by_name["portrait.CR2"].category, "RAW Image")
        self.assertEqual(by_name["Wedding 1994.mp4"].category, "Video")
        for skipped in ("tape.wav", "notes.txt", "deleted.mp4", "secret.mov"):
            self.assertNotIn(skipped, by_name)
        self.assertEqual(len(recs), 43)
        self.assertEqual(stats.errors, [])

    def test_options(self):
        recs, _ = self.run_scan(include_audio=True, include_hidden=True, group_sequences=False)
        names = {r.name for r in recs}
        self.assertIn("tape.wav", names)
        self.assertIn("secret.mov", names)
        self.assertNotIn("deleted.mp4", names)  # Recycle Bin is never inventoried
        self.assertEqual(sum(1 for r in recs if r.ext == "dpx"), 98)

    def test_csv_export(self):
        recs, _ = self.run_scan()
        path = os.path.join(self.tmp.name, "out.csv")
        self.assertEqual(write_csv(path, recs, "RT-1042"), len(recs))
        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), len(recs))
        self.assertTrue(all(r["Job #"] == "RT-1042" for r in rows))
        seq = next(r for r in rows if r["Extension"] == "DPX")
        self.assertEqual((seq["Frames"], seq["Missing Frames"]), ("98", "2"))


if __name__ == "__main__":
    unittest.main()
