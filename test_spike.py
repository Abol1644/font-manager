import json
import unittest
from pathlib import Path

from PIL import Image, ImageChops

from font_spike import DATA, DB_PATH, hb_shape, open_db, render_preview, search_real_families


class FontSpikeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        discovery = DATA / "discovery.json"
        if not discovery.exists():
            raise RuntimeError("Run `python font_spike.py discover` before tests.")
        cls.result = json.loads(discovery.read_text(encoding="utf-8"))
        cls.variable_face = next(
            face for face in cls.result["faces"]
            if face["family"].casefold() == "dibaj vf" and face["is_variable"]
        )

    def test_sqlite_real_catalog_search(self):
        self.assertTrue(DB_PATH.exists())
        with open_db() as db:
            rows = search_real_families(db, "Anjoman", 20)
        self.assertTrue(any(row["name"] == "Anjoman Variable" for row in rows))

    def test_variable_font_named_instances_and_axis(self):
        face = self.variable_face
        self.assertTrue(face["axes"])
        self.assertTrue(face["named_instances"])
        self.assertIn("wght", [axis["tag"] for axis in face["axes"]])

    def test_persian_shapes_without_notdef(self):
        metrics = hb_shape(face_path(self.variable_face), 0, "سلام دنیا — فارسی",
                           {"wght": 200.0})[0]
        self.assertEqual(metrics["direction"], "rtl")
        self.assertEqual(metrics["script"], "Arab")
        self.assertEqual(metrics["notdef_glyphs"], 0)

    def test_liga_feature_changes_shaped_glyph_sequence(self):
        face = self.variable_face
        on = hb_shape(face["path"], face["face_index"], "office affinity ffi",
                      {"wght": 200.0}, {"liga": True})[0]
        off = hb_shape(face["path"], face["face_index"], "office affinity ffi",
                       {"wght": 200.0}, {"liga": False})[0]
        self.assertNotEqual(on["glyph_ids"], off["glyph_ids"])
        self.assertEqual(on["glyph_count"], 13)
        self.assertEqual(off["glyph_count"], 19)

    def test_variable_axis_changes_raster_output(self):
        face = self.variable_face
        axis = face["axes"][0]
        low = DATA / "test-axis-low.png"
        high = DATA / "test-axis-high.png"
        render_preview(face, "office affinity ffi", "liga", False, axis["min"], low)
        render_preview(face, "office affinity ffi", "liga", False, axis["max"], high)
        diff = ImageChops.difference(Image.open(low).convert("RGB"),
                                     Image.open(high).convert("RGB"))
        self.assertIsNotNone(diff.getbbox())


def face_path(face):
    return face["path"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
