# Visual Atlas Builder R0: local-first contracts

The browser hosted on GitHub Pages is static HTML/CSS/JavaScript. v0.9 supports versioned swappable slots and named presets; see [slot contract](SLOTS-PRESETS.md). It neither asks for an account nor uploads user textures to Superior MI Labs. Imported ZIPs are session-only by default. Users can explicitly enable local IndexedDB persistence for *new imports*; browser storage is not cloud storage, is quota-limited, and can be cleared. **Keep original ZIP backups**. GitHub Pages does not provide a server-side asset storage API.

## Inputs

- A standalone PNG/JPEG/WebP/GIF becomes a full-image `region` with a generated local candidate ID and unspecified license. Animated GIF decoding currently uses only the browser's decoded image, **not** per-frame GIF sequences.
- Upload multiple files together: one or more `smi-visual-pack/1` JSON manifests plus accompanying images whose filenames match their texture paths. Prefer a ZIP for nested directories.
- Import a ZIP containing **one or many** `smi-visual-pack/1` manifests and their nested textures, optionally with `smi-visual-collection/1` `collection.json` defining pack groups and a default entry. A collection is imported as one Bag entry, with cross-pack asset references allowed and validated. No network references allowed.
- Built-in Icon Atlas v0.6.0 records are adapted to `region` assets in memory, preserving their IDs and exact pixel rectangles.

Accepted asset kinds: `region`, `sequence`, `composition`, `state_set`. Supports `region.rect_px`, `region.nine_slice_px`, `sequence.frames/default_fps/duration_ms/playback`, `composition.layers/size_px/inputs`, `state_set.states/default_state`, and layer `offset_px`, `size_px`, `opacity`, `visible_when`, `state_from_input`, `state`, `input_values`, `clip`, and `position_from_input`. The script allows arbitrary region rectangles; grid coordinates are not required.

## Export

The builder resolves transitive asset dependencies and creates a standalone ZIP containing `manifest.json`, the referenced local textures, and `SOURCE-NOTICES.txt`. When an official Apache-2.0 icon texture is included, it also bundles its repository license file. The builder does not automatically submit private packs to GitHub.

## Security and limitations

- No `eval`, arbitrary HTML/JS, shaders, remote texture URLs or upload endpoint.
- Validate relative ZIP paths and reject traversal, excessively many assets, invalid dimensions, missing references, cycles, invalid nine-slice margins, and suspiciously large inputs.
- Import compressed ZIPs up to 120 MB; per-texture entry <=24 MB; image bounds <=8192 px on each side. These are implementation caps, not safe-memory guarantees; very large packs can still exhaust browser memory.
- Not yet implemented: automatic compatible slot/preset replacement, native on-canvas pointer/drag interaction adapters, animated GIF extraction, animated PNG/GIF/video export, rich keyframe tracks, shader composition, automatic pack publication, cloud saves, deep user-editable animation timeline, screen-reader-optimized canvas editing, external engine exporters, rotated source sprites, or automatic art rights verification.
- RGB rendering and texture blending use the Canvas 2D pipeline, which is not a substitute for a full color-managed rendering engine.

## Publish and local use

```
python3 atlasctl.py validate --deep
python3 tools/build_site.py
python3 -m http.server 8000 --directory site
```

Open `http://localhost:8000/builder.html`, or host the generated `site/` files from any static HTTP server. GitHub Actions on main publishes that same generated site to Pages. For fully offline use, the JSZip dependency is bundled in the repository rather than loaded from a CDN.

## Architecture boundaries

The site is a **read-only projection** of the authoritative Icon Atlas manifest, and a **user-owned ephemeral workspace** for newly authored packs. New private assets do **not** automatically edit the original 20 sheets. A published pack must be reviewed and committed through the normal source workflow. The same `smi-visual-pack/1` bundle can be loaded by a native renderer or browser, with host code owning application-specific input events.
