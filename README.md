# Superior MI Icon Atlas

**A reusable, searchable visual vocabulary for software and real-world systems.**

[Browse the icon catalog](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/) · [Installation](#installation) · [Contributing](#contributing) · [Licensing](#licensing)

> **Publication status:** Source import and GitHub Pages deployment are being prepared. The public catalog link becomes available after the site is deployed successfully. This repository must not be mistaken for the older third-party research collection.

## About

Icon Atlas is an open icon system for **Superior MI Labs** and independent developers. A single manifest describes each icon's canonical ID, subject hierarchy, search vocabulary, visual style, licensing provenance, texture-sheet location and precise crop coordinates.

The current original-artwork starter, **v0.2.0**, contains **64 independently constructed concepts** expressed as **192 symbols** (symbol, badge and tile variants). They use a 24 × 8 RGBA sprite atlas with 96 × 96 pixel cells. The production sheet is transparent, with separately tintable grayscale foregrounds and solid-black outlines.

The larger historical experimental library (20,325 assets, including third-party drawings) is **not** part of the clean-original public starter.

## Features

- Search by words, abbreviations, concepts and explicit synonyms.
- Browse by category and visual variant.
- Preview each icon before downloading.
- Download an individual transparent PNG, cropped from the source atlas.
- **Exact manifest naming for downloads**, e.g. `icons.original.programming.bug.symbol.png`.
- Recolor the foreground without recoloring the black outline.
- Reference stable IDs in software without copying a separate registry into every application.
- Rebuild the static browser for GitHub Pages with Python; no server, database or NPM dependency.

## Installation

Linux (user-wide shared assets):

```bash
python3 tools/install.py
# Installs under ~/.local/share/superior-mi/icon-atlas/
```

Windows:

```powershell
py -3 tools/install.py
# Installs under %LOCALAPPDATA%\SuperiorMILabs\icon-atlas\
```

Clone and keep your source wherever you develop; the installer handles the shared runtime location. Run `python3 tools/install.py --show-path` to inspect the destination. Use `--upgrade` for a backup-protected update.

## Development

The **manifest is authoritative**, not an independently maintained UI catalog. The Python build tools generate textures and the searchable website from the same source. To build and test from a complete source checkout:

```bash
python3 -m pip install -r requirements-build.txt
python3 tools/build_original.py
python3 tools/build_site.py
python3 atlasctl.py validate
python3 -m unittest discover -s tests -v
```

A successful GitHub Pages deployment is served at `https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/`. See the site workflow and publishing instructions in the source release.

## Stable asset contract

Each icon's manifest record includes its immutable ID, concept, display name, style, semantic tags, source/provenance, exact pixel rectangle and atlas location. UI code resolves the icon ID to artwork; it **does not** generate a new graph node, type, method or operation. Unknown IDs should use the application's existing fallback icon.

## Licensing

Original code and original starter artwork are intended to be released under **Apache License 2.0**, subject to their documented visual review. Third-party icons and trademarked logos are not silently relicensed as our work. Consult `LICENSE`, `NOTICE.md` and artwork provenance before exporting future icon packs.

## Contributing

New contributions should improve recognition and discoverability, not just increase counts. Use semantic canonical IDs, add everyday synonyms (e.g. *image*, *picture*, *photo*), record provenance, test exact 96 × 96 crops and transparent alpha, and avoid reusing third-party paths without explicit licensing review.

Maintained by [Superior MI Labs](https://github.com/Superior-MI-Labs).