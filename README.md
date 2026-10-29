# Superior MI Icon Atlas

**v0.3.2 · Source-alignment repair · 2,073 candidate icons · 20 real 24×8 texture atlases**

[Browse the Icon Atlas](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/) | [Manifest](manifest.json) | [QA report](SOURCE-ALIGNMENT-AUDIT.json)

This release **replaces the broken v0.3.1 crops**. The ten AI-generated source images had different symbol counts (about 24 to 30 symbols per row) and sometimes different row offsets. Previous code assumed each source was already a perfectly aligned 24×8 grid. Consequently it sliced through icons, placing glyph fragments from adjacent symbols into the same tile.

## Correct pipeline

1. Detect actual source row separators using foreground-alpha valleys.
2. Identify complete individual symbols within each row; use the verified 24-column segmentation for the first seven programming rows.
3. Crop each source icon at its own detected bounding box; leave 6px safe padding.
4. Scale each symbol independently into a true 96×96 output cell.
5. Pack into new 24×8 textures; do not equate source grid coordinates with destination grid coordinates.
6. Record **source_file, source_region_px, source_bbox_px** and exact output sheet/cell/rect in the manifest.
7. Validate real pixels (transparent 5px borders, alpha coverage, pure-white foreground, individual crop SHA), not only whole-image checksums.

All final `atlas.png` files use transparent RGBA, white tintable strokes, and no embedded grid. `inspection-preview.png` is the only dark checkerboard.

## Search and download

The static GitHub Pages browser derives its index from `manifest.json`; it downloads cropped 96×96 transparent PNG assets named exactly `{icon-id}.png`. Color tint is applied through the separate `foreground-mask.png` and `black-outline.png` layers. Every asset may be downloaded individually.

**Important:** Names describe source positions, not verified semantic meanings. These are artwork *candidates* and may include visually similar or malformed drawings. We intentionally avoid inventing labels and tags. The source register and provenance let us replace any candidate later.

## Build and test

```bash
python3 -m pip install -r requirements-test.txt
python3 atlasctl.py validate --deep
python3 -m unittest discover -s tests -p 'test_site.py' -v
python3 tools/build_site.py
```

## Install paths

Linux (per-user): `~/.local/share/superior-mi/icon-atlas/`.
Windows (per-user): `%LOCALAPPDATA%\SuperiorMILabs\IconAtlas\`.

This is a static asset library, not a new source of truth for Studio's node semantics. The authoritative contract is the manifest and its immutable asset IDs. An intentionally changed crop may require versioning; an old location-based candidate ID must not be silently assigned a newly guessed meaning.

## Ownership and licensing

The source images for this experimental rebuild were generated for Superior MI Labs, not copied from Font Awesome or Material Design vector paths. The root Apache-2.0 license governs the project code, metadata, and project-generated assets. The artworks still require visual and provenance review before a definitive original-artwork release. No legacy mixed-license packs are bundled.
