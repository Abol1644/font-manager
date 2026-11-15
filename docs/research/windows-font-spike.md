# Windows Font Discovery and Rendering Feasibility Study

This document preserves a historical, separate Python feasibility spike. Its
source remains at the repository root (`font_spike.py`); run the commands below
from the repository root. This research code is not the current Glyph Electron
app's backend.

The study was a deliberately small **Windows-only** experiment. At the time,
Rust/Tauri was being considered, but the inspected machine had Rust installed
without an MSVC linker or Visual C++ build tools, so neither a Rust executable
nor a Tauri prototype could be built. The Python spike collected feasibility
evidence for font discovery, OpenType parsing, shaping/raster preview, and
SQLite search.

## Environment and prerequisites

- Verified runtime: Windows 10 Pro x64, build 19045.
- Python 3.15, with dependencies pinned in `requirements.txt`.
- Native discovery: Windows GDI `EnumFontFamiliesExW`.
- File metadata: `fontTools` (TTF/OTF/TTC/OTC).
- Shaping diagnostics: HarfBuzz (`uharfbuzz`).
- Raster preview: explicit HarfBuzz shaping + FreeType glyph rasterization
  (`freetype-py`), composited with Pillow. This avoids relying on Pillow's
  optional RAQM build feature.
- Catalog: Python SQLite with FTS5.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe font_spike.py all
.\.venv\Scripts\python.exe -m unittest discover -v
```

The `all` command enumerates installed fonts, parses metadata, stores the real
catalog, benchmarks 50,000 separate synthetic family names, generates a
variable-font/feature preview comparison, then opens a small Tk UI. Use
`discover`, `benchmark`, `preview`, or `gui` to run individual stages. The UI
allows SQLite-backed family search, face selection, sample text editing, a
first-variable-axis slider, and a feature-tag toggle when the selected font
exposes one.

Run `discover` once before `preview`, `gui`, or the test suite. `benchmark` can
run independently and does not need a discovery result.

## What it tests

- Windows GDI family enumeration compared with parsing installed font files.
- Family/face names, file/collection index, localized raw name records, table
  inventory, `fvar` axes and named instances, and GSUB/GPOS feature tags.
- HarfBuzz shaping for Latin and Persian samples, including `.notdef` glyphs,
  direction, script, glyph IDs, and advances.
- FreeType raster preview with variable-axis application and OpenType feature
  overrides. The demo compares `Dibaj VF`'s `wght` axis at its minimum/maximum
  and `liga` enabled/disabled; the Persian sample is shaped in the selected
  face when its cmap covers the sample, otherwise Tahoma is used as fallback.
- SQLite FTS5 prefix search on 50,000 synthetic records, kept in a distinct
  table from real installed fonts.

## Generated evidence

Runtime output is written under `.spike-data/` (ignored by Git):

- `discovery.json`: raw and normalized Windows discovery/parser results.
- `catalog.sqlite3`: separate real and synthetic catalog tables.
- `benchmark.json`: search timings and machine/runtime context.
- `preview.json`: preview metrics and image-difference evidence.
- `preview_*.png`: low/high axis and feature on/off preview variants.
- `preview.png`: most recent preview rendered by the UI.

## Verified run (2026-11-15)

Environment: Windows 10 Pro x64 (10.0.19045), AMD64 Family 25 Model 80,
16 logical processors, approximately 14.9 GB RAM, Python 3.15.2, SQLite 3.53.4.

Discovery run:

- 549 distinct names returned by GDI enumeration.
- 618 font files scanned; 655 faces parsed and grouped into 205 typographic
  family records.
- 15 variable faces; all 15 exposed named instances (the number of named
  instances varies by font); 212 distinct GSUB/GPOS feature tags found.
- 293 faces had Arabic-range cmap entries; 24,322 raw name records retained.
- 0 per-face parse exceptions; discovery completed in 5.200 seconds. One
  non-fatal `post` table warning was emitted by fontTools while reading the
  installed corpus.
- GDI and file-parser names do not match one-to-one: GDI includes face/style
  aliases while the parser groups typographic family names. This needs a
  DirectWrite-based follow-up before claiming exact Windows catalog parity.

SQLite benchmark (50,000 synthetic records, 20 warm-up + 250 timed FTS5 prefix
queries, `LIMIT 50`, warm cache; final rerun): median 0.115 ms, p95 2.462 ms,
max 2.869 ms; database file 7,761,920 bytes. Synthetic rows live only in
`synthetic_families` / `synthetic_fts`; installed fonts live in separate
`real_families` / `real_fts` tables.

Preview run (`Dibaj VF`, installed per-user font): variable `wght` axis 200 to
950 produced a non-empty pixel-difference region. Disabling `liga` changed the
Latin sample from 13 to 19 HarfBuzz glyphs and produced a non-empty pixel-
difference region. The Persian sample shaped RTL / Arabic with 16 glyphs and
zero `.notdef` glyphs. Four preview variants were generated.

Validation: `python -m py_compile font_spike.py test_spike.py` passed;
`python -m unittest discover -v` passed all 5 tests (SQLite real-catalog
search, variable axes/named instances, Persian shaping, `liga` toggle, and
axis raster difference). The Tk UI process was launched and remained alive
after startup.

Tauri was not built: a minimal Rust compile probe failed with `link.exe` not found;
`vswhere -all -products '*'` returned no Visual Studio installations, and the
MSVC C++ workload is absent. No macOS or Linux build/runtime was available.

The script skips files larger than 128 MiB and catches per-file/per-face parse
failures so discovery can continue. Font files are read-only inputs; this spike
does not install, activate, or modify fonts. This is not a security sandbox:
production parsing and rasterization should run in a constrained worker process
with time/memory limits because native font libraries can still fail on hostile
binary inputs.

## Known limitations / unverified

- macOS Core Text and Linux Fontconfig discovery were **not run**; no macOS or
  Linux runtime is available in this environment.
- No Rust/Tauri prototype was built as part of this historical study. Rust
  compilation failed because `link.exe` was missing; Visual C++ build tools
  were not installed. That proposed UI integration was never verified.
- GDI is a legacy Windows enumeration API and is not a substitute for a final
  DirectWrite adapter. GDI family names and font-file parsing can differ.
- File discovery currently scans Windows and per-user font directories. Fonts
  exposed through unusual registered paths or app-private collections may be
  missed. The GDI list is retained as a comparison signal.
- Parser table/tag discovery does not prove every feature is correctly
  rendered. `liga` is a narrow demonstration, not full OpenType feature UI.
- HarfBuzz + FreeType are wired together for the preview prototype, but this is
  not a production-quality text renderer: color fonts, bitmap strikes, hinting,
  subpixel output, fallback chains, and every OpenType table are not covered.
- The preview uses a fallback font for Persian if the selected face lacks
  coverage; it does not implement general per-glyph fallback selection.
- Synthetic FTS5 timings are local microbenchmarks, not a substitute for a
  real 50k-family dataset or end-to-end UI latency measurements.

## Decisions this spike can inform

- Whether SQLite FTS5 is a viable catalog/search baseline at 50k rows.
- Whether `fontTools` exposes the metadata needed for a Rust parser test corpus.
- Whether a native API + file parser comparison is necessary for correctness.
- Whether separate shaping and raster components can produce a useful
  variable-font and complex-script preview.

Do not promote these Python results to proof that the proposed Rust crates or
Tauri architecture work. The next engineering spike should reproduce the
verified behaviors with Rust (`fontdb`/native provider, `skrifa`/`read-fonts`,
and a `cosmic-text`/Swash renderer) after installing the MSVC C++ toolchain,
then run native CI jobs on macOS and Linux.
