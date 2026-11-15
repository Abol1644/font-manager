"""Windows-only feasibility spike for installed-font discovery and preview.

This is deliberately a Python fallback: the inspected machine has Rust but no
MSVC linker/C++ build tools, so a Tauri/Rust executable cannot be built here.
The native discovery call is Windows GDI; font parsing is fontTools; shaping
diagnostics use HarfBuzz; raster preview uses Pillow/FreeType + RAQM.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wintypes
import json
import os
import platform
import random
import sqlite3
import statistics
import sys
import time
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import ttk, messagebox

from fontTools.ttLib import TTCollection, TTFont
import freetype
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageChops
import uharfbuzz as hb


ROOT = Path(__file__).resolve().parent
DATA = ROOT / ".spike-data"
DB_PATH = DATA / "catalog.sqlite3"
PERSIAN_SAMPLE = "سلام دنیا — فارسی"
LATIN_SAMPLE = "Hamburgefontsiv 0123456789"
SUPPORTED_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}
MAX_FONT_FILE_BYTES = 128 * 1024 * 1024


class LOGFONTW(ctypes.Structure):
    _fields_ = [
        ("lfHeight", ctypes.c_long), ("lfWidth", ctypes.c_long),
        ("lfEscapement", ctypes.c_long), ("lfOrientation", ctypes.c_long),
        ("lfWeight", ctypes.c_long), ("lfItalic", ctypes.c_ubyte),
        ("lfUnderline", ctypes.c_ubyte), ("lfStrikeOut", ctypes.c_ubyte),
        ("lfCharSet", ctypes.c_ubyte), ("lfOutPrecision", ctypes.c_ubyte),
        ("lfClipPrecision", ctypes.c_ubyte), ("lfQuality", ctypes.c_ubyte),
        ("lfPitchAndFamily", ctypes.c_ubyte), ("lfFaceName", ctypes.c_wchar * 32),
    ]


class ENUMLOGFONTEXW(ctypes.Structure):
    _fields_ = [
        ("elfLogFont", LOGFONTW), ("elfFullName", ctypes.c_wchar * 64),
        ("elfStyle", ctypes.c_wchar * 32), ("elfScript", ctypes.c_wchar * 32),
    ]


def native_gdi_families() -> list[str]:
    """Enumerate font family names visible to Windows GDI (not file paths)."""
    if os.name != "nt":
        raise RuntimeError("This spike currently implements Windows GDI discovery only.")
    found: set[str] = set()
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(ENUMLOGFONTEXW), ctypes.c_void_p,
        wintypes.DWORD, wintypes.LPARAM,
    )

    def callback(info, _metrics, _font_type, _param):
        try:
            name = info.contents.elfLogFont.lfFaceName.strip()
            if name:
                found.add(name)
        except (ValueError, OSError):
            pass
        return 1

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.EnumFontFamiliesExW.argtypes = [
        wintypes.HDC, ctypes.POINTER(LOGFONTW), callback_type,
        wintypes.LPARAM, wintypes.DWORD,
    ]
    gdi32.EnumFontFamiliesExW.restype = ctypes.c_int
    hdc = user32.GetDC(None)
    if not hdc:
        raise ctypes.WinError(ctypes.get_last_error())
    logfont = LOGFONTW()
    logfont.lfCharSet = 1  # DEFAULT_CHARSET
    callback_ref = callback_type(callback)
    try:
        gdi32.EnumFontFamiliesExW(hdc, ctypes.byref(logfont), callback_ref, 0, 0)
    finally:
        user32.ReleaseDC(None, hdc)
    return sorted(found, key=str.casefold)


def installed_font_paths() -> list[Path]:
    paths: set[Path] = set()
    roots = [Path(os.environ["WINDIR"]) / "Fonts"]
    local_fonts = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"
    if local_fonts.is_dir():
        roots.append(local_fonts)
    for root in roots:
        if root.is_dir():
            for path in root.iterdir():
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    try:
                        paths.add(path.resolve())
                    except OSError:
                        pass
    return sorted(paths, key=lambda p: str(p).casefold())


def name_value(font: TTFont, name_ids: tuple[int, ...]) -> str:
    table = font.get("name")
    if table is None:
        return ""
    for name_id in name_ids:
        # Prefer Windows Unicode English, then any decodable record.
        records = [n for n in table.names if n.nameID == name_id]
        records.sort(key=lambda n: (n.platformID != 3, n.langID not in (0x409, 0)))
        for record in records:
            try:
                value = record.toUnicode().strip()
                if value:
                    return value
            except (UnicodeError, AttributeError):
                continue
    return ""


def parse_face(path: Path, font: TTFont, face_index: int) -> dict:
    family = name_value(font, (16, 1)) or path.stem
    subfamily = name_value(font, (17, 2)) or "Regular"
    cmap = {}
    try:
        cmap = font.getBestCmap() or {}
    except Exception:
        pass
    features: set[str] = set()
    for table_tag in ("GSUB", "GPOS"):
        try:
            feature_list = font[table_tag].table.FeatureList
            if feature_list:
                features.update(record.FeatureTag for record in feature_list.FeatureRecord)
        except (KeyError, AttributeError, TypeError):
            pass
    axes = []
    instances = []
    if "fvar" in font:
        name_table = font.get("name")
        for axis in font["fvar"].axes:
            try:
                axis_name = name_table.getDebugName(axis.axisNameID) if name_table else None
            except Exception:
                axis_name = None
            axes.append({
                "tag": axis.axisTag, "name": axis_name or axis.axisTag,
                "min": round(float(axis.minValue), 4),
                "default": round(float(axis.defaultValue), 4),
                "max": round(float(axis.maxValue), 4),
                "hidden": bool(axis.flags & 1),
            })
        for instance in font["fvar"].instances:
            try:
                instance_name = name_table.getDebugName(instance.subfamilyNameID) if name_table else None
            except Exception:
                instance_name = None
            instances.append({
                "name": instance_name or "Named instance",
                "coordinates": {k: round(float(v), 4) for k, v in instance.coordinates.items()},
            })
    names = []
    try:
        for record in font["name"].names:
            try:
                value = record.toUnicode()
            except Exception:
                continue
            names.append({
                "name_id": record.nameID, "platform_id": record.platformID,
                "encoding_id": record.platEncID, "language_id": record.langID,
                "value": value[:180],
            })
    except (KeyError, AttributeError):
        pass
    arabic_codepoints = [cp for cp in cmap if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F]
    return {
        "family": family, "subfamily": subfamily,
        "full_name": name_value(font, (4,)) or f"{family} {subfamily}",
        "postscript_name": name_value(font, (6,)),
        "path": str(path), "face_index": face_index,
        "weight_class": int(font["OS/2"].usWeightClass) if "OS/2" in font else None,
        "width_class": int(font["OS/2"].usWidthClass) if "OS/2" in font else None,
        "italic": bool(font["post"].italicAngle) if "post" in font else False,
        "is_variable": bool(axes), "axes": axes, "named_instances": instances,
        "features": sorted(features), "glyph_count": len(cmap),
        "arabic_codepoints": len(arabic_codepoints),
        "has_persian_basic": all(cp in cmap for cp in map(ord, "سلامدنیا")),
        "tables": sorted(font.keys()), "raw_names": names,
    }


def discover() -> dict:
    gdi_names = native_gdi_families()
    paths = installed_font_paths()
    faces: list[dict] = []
    errors: list[dict] = []
    for path in paths:
        try:
            if path.stat().st_size > MAX_FONT_FILE_BYTES:
                errors.append({"path": str(path), "error": f"file exceeds {MAX_FONT_FILE_BYTES} byte safety limit"})
                continue
            if path.suffix.lower() in {".ttc", ".otc"}:
                collection = TTCollection(str(path), lazy=True)
                try:
                    for index, font in enumerate(collection.fonts):
                        try:
                            faces.append(parse_face(path, font, index))
                        except Exception as exc:
                            errors.append({"path": str(path), "face_index": index, "error": str(exc)[:240]})
                finally:
                    collection.close()
            else:
                font = TTFont(str(path), lazy=True, recalcBBoxes=False, recalcTimestamp=False)
                try:
                    faces.append(parse_face(path, font, 0))
                finally:
                    font.close()
        except Exception as exc:
            errors.append({"path": str(path), "error": str(exc)[:240]})
    grouped: dict[str, list[dict]] = defaultdict(list)
    for face in faces:
        grouped[face["family"].casefold()].append(face)
    families = [
        {"id": key, "name": sorted(items, key=lambda x: (x["family"].casefold(), x["family"]))[0]["family"],
         "faces": sorted(items, key=lambda x: (x["subfamily"].casefold(), x["full_name"].casefold()))}
        for key, items in grouped.items()
    ]
    families.sort(key=lambda x: x["name"].casefold())
    gdi_folded = {name.casefold() for name in gdi_names}
    parsed_folded = {family["name"].casefold() for family in families}
    return {
        "platform": platform.platform(), "python": sys.version.split()[0],
        "gdi_family_count": len(gdi_names), "gdi_family_samples": gdi_names[:40],
        "file_count": len(paths), "parsed_face_count": len(faces),
        "family_count": len(families), "parse_error_count": len(errors),
        "gdi_families_not_in_file_parser": sorted(gdi_folded - parsed_folded),
        "parsed_families_not_in_gdi": sorted(parsed_folded - gdi_folded),
        "variable_face_count": sum(1 for face in faces if face["is_variable"]),
        "arabic_capable_face_count": sum(1 for face in faces if face["arabic_codepoints"] > 0),
        "families": families, "faces": faces, "errors": errors,
    }


def open_db() -> sqlite3.Connection:
    DATA.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("""CREATE TABLE IF NOT EXISTS real_families (
        family_id TEXT PRIMARY KEY, name TEXT NOT NULL, face_count INTEGER NOT NULL,
        metadata_json TEXT NOT NULL)""")
    db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS real_fts USING fts5(
        family_id UNINDEXED, name, tokenize='unicode61 remove_diacritics 2')""")
    db.execute("""CREATE TABLE IF NOT EXISTS synthetic_families (
        family_id INTEGER PRIMARY KEY, name TEXT NOT NULL)""")
    db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS synthetic_fts USING fts5(
        family_id UNINDEXED, name, tokenize='unicode61')""")
    db.commit()
    return db


def index_real(db: sqlite3.Connection, result: dict) -> None:
    with db:
        db.execute("DELETE FROM real_fts")
        db.execute("DELETE FROM real_families")
        for family in result["families"]:
            payload = json.dumps(family, ensure_ascii=False)
            db.execute("INSERT INTO real_families VALUES (?, ?, ?, ?)",
                       (family["id"], family["name"], len(family["faces"]), payload))
            db.execute("INSERT INTO real_fts VALUES (?, ?)", (family["id"], family["name"]))


def benchmark_search(db: sqlite3.Connection, count: int = 50_000, queries: int = 250) -> dict:
    existing = db.execute("SELECT COUNT(*) FROM synthetic_families").fetchone()[0]
    if existing != count:
        with db:
            db.execute("DELETE FROM synthetic_fts")
            db.execute("DELETE FROM synthetic_families")
            batch = [(i, f"SyntheticFont{i:05d}") for i in range(count)]
            db.executemany("INSERT INTO synthetic_families VALUES (?, ?)", batch)
            db.executemany("INSERT INTO synthetic_fts VALUES (?, ?)", batch)
    rng = random.Random(20261115)
    warmups = [f"syntheticfont{rng.randrange(count):05d}"[:15] + "*" for _ in range(20)]
    for term in warmups:
        db.execute("SELECT family_id, name FROM synthetic_fts WHERE synthetic_fts MATCH ? LIMIT 50",
                   (term,)).fetchall()
    samples = []
    for _ in range(queries):
        n = rng.randrange(count)
        # Prefix queries simulate progressively narrowed family-name search.
        term = f"syntheticfont{n:05d}"[:rng.choice((13, 14, 15, 16, 17))] + "*"
        started = time.perf_counter_ns()
        db.execute("SELECT family_id, name FROM synthetic_fts WHERE synthetic_fts MATCH ? LIMIT 50",
                   (term,)).fetchall()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    memory = MEMORYSTATUSEX()
    memory.dwLength = ctypes.sizeof(memory)
    try:
        ctypes.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx(ctypes.byref(memory))
        total_ram = memory.ullTotalPhys
    except Exception:
        total_ram = None
    return {
        "synthetic_records": count, "queries": queries,
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(p95, 3), "max_ms": round(max(samples), 3),
        "min_ms": round(min(samples), 3),
        "machine": platform.platform(), "cpu": platform.processor(),
        "logical_processors": os.cpu_count(), "ram_bytes": total_ram,
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version, "database_bytes": DB_PATH.stat().st_size,
        "warmup_queries": len(warmups), "cache_mode": "warm-cache timed queries",
        "query_shape": "FTS5 prefix MATCH, LIMIT 50, synthetic table only",
    }


def search_real_families(db: sqlite3.Connection, query: str, limit: int = 10_000) -> list[dict]:
    tokens = [token for token in query.strip().split() if token]
    if tokens:
        expression = " AND ".join('"' + token.replace('"', '""') + '"*' for token in tokens)
        rows = db.execute(
            "SELECT f.metadata_json FROM real_fts x JOIN real_families f "
            "ON f.family_id=x.family_id WHERE real_fts MATCH ? ORDER BY rank LIMIT ?",
            (expression, limit),
        ).fetchall()
    else:
        rows = db.execute("SELECT metadata_json FROM real_families ORDER BY name LIMIT ?", (limit,)).fetchall()
    return [json.loads(row[0]) for row in rows]


def hb_shape(path: str, face_index: int, text: str, variations: dict | None = None,
             feature_overrides: dict | None = None, direction: str | None = None,
             language: str | None = None, script: str | None = None) -> tuple[dict, list, list, int]:
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob, face_index)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    hb.ot_font_set_funcs(font)
    if variations:
        font.set_variations(variations)
    buffer = hb.Buffer()
    buffer.add_str(text)
    if direction:
        buffer.direction = direction
    if language:
        buffer.language = language
    if script:
        buffer.script = script
    buffer.guess_segment_properties()
    hb.shape(font, buffer, feature_overrides or {})
    infos = buffer.glyph_infos
    positions = buffer.glyph_positions
    metrics = {
        "direction": buffer.direction, "script": buffer.script,
        "glyph_count": len(infos), "notdef_glyphs": sum(1 for info in infos if info.codepoint == 0),
        "glyph_ids": [info.codepoint for info in infos[:24]],
        "advance_units": sum(pos.x_advance for pos in positions),
    }
    return metrics, infos, positions, face.upem


def rasterize_shaped_line(image: Image.Image, path: str, face_index: int, text: str,
                          origin: tuple[int, int], size: int, variations: dict | None = None,
                          axis_order: list[str] | None = None, feature_tag: str | None = None,
                          disable_feature: bool = False, rtl: bool = False,
                          color: tuple[int, int, int] = (20, 20, 20)) -> dict:
    overrides = {feature_tag: not disable_feature} if feature_tag else None
    metrics, infos, positions, upem = hb_shape(
        path, face_index, text, variations, overrides,
        direction="rtl" if rtl else None,
        language="fa" if rtl else None,
        script="arab" if rtl else None,
    )
    face = freetype.Face(path, index=face_index)
    face.set_pixel_sizes(0, size)
    if variations and axis_order:
        face.set_var_design_coords([variations[tag] for tag in axis_order])
    scale = size / float(upem)
    pen_x = float(origin[0])
    baseline = float(origin[1])
    for info, position in zip(infos, positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_DEFAULT)
        slot = face.glyph
        slot.render(freetype.FT_RENDER_MODE_NORMAL)
        bitmap = slot.bitmap
        if bitmap.width and bitmap.rows:
            pitch = abs(bitmap.pitch)
            raw = bytes(bitmap.buffer[:pitch * bitmap.rows])
            if bitmap.pixel_mode == freetype.FT_PIXEL_MODE_GRAY:
                mask = Image.frombytes("L", (bitmap.width, bitmap.rows), raw,
                                       "raw", "L", pitch, 1)
            elif bitmap.pixel_mode == freetype.FT_PIXEL_MODE_MONO:
                mask = Image.frombytes("1", (bitmap.width, bitmap.rows), raw,
                                       "raw", "1;R", pitch, 1).convert("L")
            else:
                raise RuntimeError(f"Unsupported FreeType pixel mode: {bitmap.pixel_mode}")
            x = round(pen_x + position.x_offset * scale + slot.bitmap_left)
            y = round(baseline - position.y_offset * scale - slot.bitmap_top)
            image.paste(color, (x, y), mask)
        pen_x += position.x_advance * scale
        baseline -= position.y_advance * scale
    return metrics


def render_preview(face: dict, sample: str, feature_tag: str | None = None,
                   disable_feature: bool = False, axis_value: float | None = None,
                   output: Path | None = None) -> dict:
    path = face["path"]
    index = face["face_index"]
    axes = face["axes"]
    variation_values = {axis["tag"]: axis["default"] for axis in axes}
    if axes and axis_value is not None:
        variation_values[axes[0]["tag"]] = axis_value
    image = Image.new("RGB", (1200, 330), "#f7f7f4")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("segoeui.ttf", 18)
    draw.text((28, 18), f"{face['full_name']}  |  {Path(path).name}  |  face #{index}",
              fill="#333333", font=title_font)
    axis_order = [axis["tag"] for axis in axes]
    latin_metrics = rasterize_shaped_line(
        image, path, index, sample, (28, 118), 44, variation_values, axis_order,
        feature_tag, disable_feature, False, (21, 21, 21),
    )
    persian_source = "selected face"
    persian_path, persian_index, persian_axes, persian_values = path, index, axis_order, variation_values
    if not face["has_persian_basic"]:
        fallback = Path(os.environ["WINDIR"]) / "Fonts" / "tahoma.ttf"
        if fallback.exists():
            persian_path, persian_index, persian_axes, persian_values = str(fallback), 0, [], {}
            persian_source = "Tahoma fallback (selected face lacks basic Persian cmap coverage)"
    persian_metrics = rasterize_shaped_line(
        image, persian_path, persian_index, PERSIAN_SAMPLE, (28, 250), 38,
        persian_values, persian_axes, None, False, True, (22, 75, 117),
    )
    draw.text((28, 285), f"Persian line: {persian_source} | HarfBuzz + FreeType",
              fill="#555555", font=title_font)
    if output:
        output.parent.mkdir(exist_ok=True)
        image.save(output)
    return {
        "output": str(output) if output else None,
        "rasterizer": "HarfBuzz shaping + FreeType glyph rasterization",
        "variation_values": variation_values, "available_features": face["features"],
        "feature_control": {"tag": feature_tag, "disabled": disable_feature},
        "persian_source": persian_source, "harfbuzz_persian_shape": persian_metrics,
        "harfbuzz_latin_shape": latin_metrics,
    }


class SpikeUI:
    def __init__(self, result: dict):
        self.result = result
        self.root = tk.Tk()
        self.root.title("Font Manager — Feasibility Spike (Windows)")
        self.root.geometry("1100x720")
        self.db = open_db()
        self.filtered = search_real_families(self.db, "")
        self.face_lookup = {face["full_name"] + " — " + Path(face["path"]).name: face
                            for face in result["faces"]}
        self.current_face = None
        self.photo = None
        self._build()

    def _build(self):
        outer = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left = ttk.Frame(outer, width=330)
        right = ttk.Frame(outer)
        outer.add(left, weight=1); outer.add(right, weight=3)
        ttk.Label(left, text=f"Installed families: {len(self.result['families']):,}").pack(anchor="w")
        self.query = tk.StringVar()
        entry = ttk.Entry(left, textvariable=self.query)
        entry.pack(fill=tk.X, pady=6); self.query.trace_add("write", self._filter)
        self.family_list = tk.Listbox(left, exportselection=False)
        self.family_list.pack(fill=tk.BOTH, expand=True)
        self.family_list.bind("<<ListboxSelect>>", self._family_selected)
        self._fill_families()

        self.face_var = tk.StringVar()
        self.face_combo = ttk.Combobox(right, textvariable=self.face_var, state="readonly")
        self.face_combo.pack(fill=tk.X, pady=(0, 8))
        self.face_combo.bind("<<ComboboxSelected>>", self._face_selected)
        self.sample = tk.StringVar(value="office affinity ffi")
        ttk.Entry(right, textvariable=self.sample).pack(fill=tk.X, pady=5)
        self.sample.trace_add("write", lambda *_: self._draw())
        self.axis_label = ttk.Label(right, text="No variable axis on selected face")
        self.axis_label.pack(anchor="w")
        self.axis = tk.DoubleVar(value=0)
        self.axis_scale = ttk.Scale(right, variable=self.axis, command=lambda _v: self._draw())
        self.axis_scale.pack(fill=tk.X)
        feature_row = ttk.Frame(right)
        feature_row.pack(fill=tk.X, pady=4)
        self.feature_var = tk.StringVar()
        self.feature_combo = ttk.Combobox(feature_row, textvariable=self.feature_var,
                                          state="readonly", width=12)
        self.feature_combo.pack(side=tk.LEFT)
        self.feature_combo.bind("<<ComboboxSelected>>", lambda _e: self._draw())
        self.feature_off = tk.BooleanVar(value=False)
        ttk.Checkbutton(feature_row, text="Disable selected feature",
                        variable=self.feature_off, command=self._draw).pack(side=tk.LEFT, padx=8)
        self.preview_label = ttk.Label(right)
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=10)
        self.status = tk.StringVar(value="Select a family to inspect its faces and preview.")
        ttk.Label(right, textvariable=self.status, wraplength=720).pack(anchor="w")

    def _fill_families(self):
        self.family_list.delete(0, tk.END)
        for family in self.filtered[:10000]:
            self.family_list.insert(tk.END, family["name"])

    def _filter(self, *_):
        query = self.query.get().casefold().strip()
        try:
            self.filtered = search_real_families(self.db, query)
        except sqlite3.Error as exc:
            self.status.set(f"SQLite search error: {exc}")
            self.filtered = []
        self._fill_families()

    def _family_selected(self, _event=None):
        selection = self.family_list.curselection()
        if not selection:
            return
        family = self.filtered[selection[0]]
        labels = []
        self._family_faces = family["faces"]
        for face in family["faces"]:
            labels.append(face["full_name"] + " — " + Path(face["path"]).name)
        self.face_combo["values"] = labels
        if labels:
            self.face_combo.current(0)
            self._face_selected()

    def _face_selected(self, _event=None):
        index = self.face_combo.current()
        if index < 0:
            return
        self.current_face = self._family_faces[index]
        axes = self.current_face["axes"]
        feature_candidates = [tag for tag in ("liga", "calt", "kern", "dlig", "ss01", "ss02")
                              if tag in self.current_face["features"]]
        self.feature_combo["values"] = feature_candidates
        if feature_candidates:
            self.feature_combo.current(0)
        else:
            self.feature_var.set("")
        if axes:
            axis = axes[0]
            self.axis_label.config(text=f"{axis['tag']} · {axis['name']} ({axis['min']}–{axis['max']})")
            self.axis_scale.configure(from_=axis["min"], to=axis["max"])
            self.axis.set(axis["default"])
            self.axis_scale.state(["!disabled"])
        else:
            self.axis_label.config(text="No variable axis on selected face")
            self.axis_scale.state(["disabled"])
        self._draw()

    def _draw(self):
        if not self.current_face:
            return
        try:
            axes = self.current_face["axes"]
            value = self.axis.get() if axes else None
            output = DATA / "preview.png"
            feature_tag = self.feature_var.get() or None
            details = render_preview(self.current_face, self.sample.get(), feature_tag,
                                     self.feature_off.get(), value, output)
            image = Image.open(output)
            self.photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=self.photo)
            self.status.set(
                f"Axes: {details['variation_values']} | features: {details['features'] or 'none'} | "
                f"Persian: {details['persian_source']} | HarfBuzz glyphs: "
                f"{details['harfbuzz_persian_shape']['glyph_count']} "
                f"(notdef={details['harfbuzz_persian_shape']['notdef_glyphs']}, "
                f"script={details['harfbuzz_persian_shape']['script']}, "
                f"direction={details['harfbuzz_persian_shape']['direction']})"
            )
        except Exception as exc:
            self.status.set(f"Preview failed safely: {type(exc).__name__}: {exc}")

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.db.close()


def run_preview_demo(result: dict) -> dict:
    candidates = [face for face in result["faces"]
                  if face["is_variable"] and face["has_persian_basic"] and "liga" in face["features"]]
    if not candidates:
        raise RuntimeError("No installed variable font with Persian coverage and liga was found.")
    face = next((item for item in candidates if item["family"].casefold() == "dibaj vf"), candidates[0])
    axis = face["axes"][0]
    feature = "liga"
    DATA.mkdir(exist_ok=True)
    variants = {}
    for axis_value, axis_label in ((axis["min"], "low"), (axis["max"], "high")):
        for disabled, feature_label in ((False, "on"), (True, "off")):
            key = f"{axis_label}_{feature_label}"
            output = DATA / f"preview_{key}.png"
            details = render_preview(face, "office affinity ffi", feature, disabled, axis_value, output)
            variants[key] = details
    low_on = Image.open(DATA / "preview_low_on.png").convert("RGB")
    high_on = Image.open(DATA / "preview_high_on.png").convert("RGB")
    low_off = Image.open(DATA / "preview_low_off.png").convert("RGB")
    diff_axis = ImageChops.difference(low_on, high_on)
    diff_feature = ImageChops.difference(low_on, low_off)
    result = {
        "font": face["full_name"], "path": face["path"], "axis": axis,
        "feature": feature, "sample": "office affinity ffi",
        "persian_sample": PERSIAN_SAMPLE,
        "persian_shape": variants["low_on"]["harfbuzz_persian_shape"],
        "latin_feature_on_glyph_count": variants["low_on"]["harfbuzz_latin_shape"]["glyph_count"],
        "latin_feature_off_glyph_count": variants["low_off"]["harfbuzz_latin_shape"]["glyph_count"],
        "axis_pixel_difference_bbox": diff_axis.getbbox(),
        "feature_pixel_difference_bbox": diff_feature.getbbox(),
        "variants": variants,
    }
    (DATA / "preview.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "benchmark", "preview", "gui", "all"), nargs="?", default="all")
    parser.add_argument("--synthetic-count", type=int, default=50_000)
    parser.add_argument("--queries", type=int, default=250)
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)
    result_path = DATA / "discovery.json"
    if args.command in ("discover", "all"):
        started = time.perf_counter()
        result = discover()
        result["discovery_seconds"] = round(time.perf_counter() - started, 3)
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        db = open_db()
        index_real(db, result)
        db.close()
        print(json.dumps({k: v for k, v in result.items() if k not in ("families", "faces", "errors")},
                         ensure_ascii=False, indent=2))
        print(f"Detailed discovery: {result_path}")
    elif args.command in ("preview", "gui"):
        result = json.loads(result_path.read_text(encoding="utf-8"))
    if args.command in ("benchmark", "all"):
        db = open_db()
        metrics = benchmark_search(db, args.synthetic_count, args.queries)
        db.close()
        (DATA / "benchmark.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print("FTS5 benchmark:")
        print(json.dumps(metrics, indent=2))
    if args.command in ("preview", "all"):
        preview_result = run_preview_demo(result)
        print("Preview demo:")
        print(json.dumps({k: v for k, v in preview_result.items() if k != "variants"}, indent=2))
        print(f"Detailed preview evidence: {DATA / 'preview.json'}")
    if args.command in ("gui", "all"):
        SpikeUI(result).run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal spike error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise

