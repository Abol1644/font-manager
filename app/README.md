# Glyph app

This folder contains Glyph's Electron, React, and TypeScript desktop prototype. For project status, roadmap, architecture, contribution guidance, and repository setup, see the [root README](../README.md).

## Run locally

Requirements: Node.js 22+ and npm. From this directory:

```powershell
npm ci
npm start
```

Electron 45 ships its runtime as a separate binary. If Forge cannot fetch it
automatically on first launch, run `npm exec -- install-electron` from this
`app` directory once, then `npm start` again. Do not run this command from the
parent `font-manager` directory: the executable is provided by this app's local
Electron dependency.

Useful checks:

```powershell
npm run typecheck
npm run lint
npm run package
```

`npm run package` creates an unpacked application under `out/` for the current
host platform. This prototype does not configure or verify production release
packaging.

## Current UI

- Live, read-only Windows installed-font discovery from the per-user and
  machine font registry, with real font-file parsing through WPF's
  `GlyphTypeface` API.
- Searchable family list with individual installed face selection and file
  details (path, format, size, modification time, weight, width, style,
  character-map count, and font version where Windows exposes it). Discovery
  results are cached locally; the first scan can take several seconds on a
  large font collection, and the refresh control forces a new Windows scan.
- A selected-family specimen with editable sample text and preview size.
- A face selector populated from the actual registered font files, grouped by
  family.
- Explicit no-results and no-selection states.
- A frameless, resizable desktop window with integrated minimize,
  maximize/restore, and close controls. The centered title label also toggles
  maximize on double-click; the flanking title-bar regions are draggable.
- Local Bodoni Moda and JetBrains Mono variable fonts (regular and italic) are
  bundled from `src/assets/fonts` and used by the interface typography.
  The guideline also specifies Inter for body copy, but no Inter font file was
  present in the supplied assets; body copy therefore uses the system sans-serif
  stack with `Inter` first in the family list.

## Limitations

**Installed-font discovery currently supports Windows only.** The app reads
per-user and machine font registrations and parses supported TTF, OTF, TTC,
and OTC files with Windows Presentation Foundation. macOS and Linux discovery
are not implemented yet. The UI does not install, uninstall, activate, or
deactivate fonts.

The face inventory is based on registered files and WPF's `GlyphTypeface`
metadata. A collection file (TTC/OTC) is currently represented by the face
WPF resolves for that file; multi-face collection indexing is not implemented.
Variable axes, named instances, detailed OpenType tables, and advanced shaping
remain future work. The Persian phrase is sample content, not proof of
Arabic-script shaping or glyph coverage.

Electron is currently scaffolded and built on Windows only. macOS and Linux
runtime behavior and packaging have not been tested. The Python feasibility
spike and its evidence remain in the parent directory and are separate from
this app.

## Security baseline

The renderer has Node integration disabled, context isolation and sandboxing
enabled, and a restrictive content security policy. The preload exposes typed
window controls and a single read-only installed-font query; it does not expose
`ipcRenderer` or broad Electron APIs. Main-process handlers validate the sender
window, require its main frame, and reject unexpected arguments. External
window creation and renderer navigation are denied.

See the root [security policy](../SECURITY.md) for vulnerability reporting and
the [font notices](../docs/FONTS.md) for bundled asset licensing.
