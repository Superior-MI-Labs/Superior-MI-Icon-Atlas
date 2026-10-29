# Superior MI Visual Atlas (formerly Icon Atlas)

**Reusable transparent icon atlases, a typed manifest vocabulary, and a searchable static browser.**

[Browse the icon gallery](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/) · [Manifest index](manifest.json) · [Architecture](docs/ARCHITECTURE.md) · [Artwork policy](docs/ARTWORK-POLICY.md)

## v0.7.0 — Keyframe timeline, frame exports and reliable publisher

- **Fixed Linux publisher:** the previous v0.6.0 script attempted the Python test suite before installing `jsonschema`; `RUN-ALL.sh` now installs missing Pillow/jsonschema into an isolated reusable venv and executes the full required tests before any Git operation.
- **Timeline editor:** select a composition layer, scrub time, set/delete keyframes for x, y, opacity, scale X/Y and rotation; choose linear, smooth or step interpolation.
- **Playback:** per-composition `duration_ms`, loop / once / ping-pong. A pure `timeline-core.js` drives browser rendering and Node regressions.
- **Portable animation:** layer tracks are authored into exported `smi-visual-pack/1` manifests and survive reimport. An additional export option writes timed PNG frames and `frames.json` into a ZIP.
- **Private safety:** ZIP imports enforce member and total uncompressed-size limits before CRC inflation; the pack validator rejects invalid frame ordering or impossible values.
- **Compatibility:** the original 2,073 icon IDs and pixels are unchanged. The builder and v0.6.0 pack formats remain compatible; `tracks` and `duration_ms` are optional fields.

### Run and publish

```bash
bash RUN-ALL.sh          # full QA; installs missing deps in a private venv
bash RUN-LOCALLY.sh     # starts local static site (Ctrl+C to stop)
# After the tests pass, use bash publish-to-github.sh to publish this release.
```

The runtime is a local-first Canvas 2D preview, not a server-side upload tool. Browser preview tests performed against injected Chromium resources and a real ZIP import→export→reimport cycle. Browser-navigation restrictions prevent directly testing the GitHub Pages URL here.

## v0.6.0 — Local-first Visual Atlas Builder

This release adds a separate local-first builder for browsing and composing imported icons, sprites, layers, states, animation sequences and GUI components. **Existing v0.5.0 icon artwork and IDs remain unchanged.**

## v0.5.0 — Visual curation and search precision

- **2,073 original candidate icon positions** in **20 real 24×8 sheets**, each 2304×768 with 96×96 cells.
- **White monoline artwork on transparent RGBA**; recolor using the alpha of the atlas itself while keeping black outlines separate.
- **Per-sheet authored manifests**, with one small `manifest.json` index; browser search data is generated, not manually edited.
- **734 visually reviewed symbols**, including `Flame`, `Picture`, `Lambda`, `Terminal`, `Folder`, and common file actions. The other **1,339** remain unreviewed candidates, not falsely described.
- **One stable icon ID per crop**. Concept IDs, display names, aliases and search tags may be curated without moving geometry or changing candidate IDs.
- Search expands curated synonyms (`fire` / `flame`, `picture` / `image` / `photo`), ranks meaningful names before generic categories, and supports automatically populated style, subject, domain, and review filters.

![Sample of visually identified icons](docs/curated-samples.png)

### Quick start

```bash
python3 -m pip install -r requirements-test.txt
python3 atlasctl.py validate --deep
python3 atlasctl.py search flame
python3 atlasctl.py search picture --status reviewed
python3 atlasctl.py info icons.candidate.programming.r04i19
python3 atlasctl.py crop icons.candidate.programming.r04i19 --out flame.png
python3 atlasctl.py tint icons.candidate.programming.r04i19 --color '#4B9CFF' --out flame-blue.png
python3 tools/build_site.py
python3 -m http.server 8000 --directory site
```

Navigate to `http://127.0.0.1:8000/` for local browsing. GitHub Pages builds from the same files on pushes to `main`.

### Where the files live

- `manifest.json` — compact authoritative index and shared style/search vocabulary.
- `manifests/<sheet>.json` — **only authored icon metadata** for that sheet: ID, source, cell, crop checksum, review status, names, aliases, tags and subjects.
- `sheets/<sheet>/atlas.png` — production white transparent atlas; foreground alpha also acts as its tint mask.
- `sheets/<sheet>/black-outline.png` — optional overlay for tinted rendering.
- `sheets/<sheet>/inspection-preview.png` — review-only image; **never render as a production texture**.
- `source-images/` — retained original research images for provenance, **not live atlas assets**.
- `atlasctl.py` — manifest loader, validation, search, crop and tint tooling.
- `tools/review_icon.py` — modifies the one owning sheet manifest (no parallel search registry).
- `tools/audit_repo.py` — on-demand duplicate/reference and backlog report.
- `tools/build_site.py` — generates browser data; `site/` is a build output and is not committed.
- `docs/ARCHITECTURE.md` — downstream usage contract and alternatives considered.

### Name an icon after visual inspection

```bash
python3 tools/review_icon.py icons.candidate.programming.r04i19 \
  --name Flame --tags 'fire,flame,blaze,burn,heat' \
  --subjects nature.fire --concept nature.flame
python3 tools/build_site.py
```

Only confirmed visible properties should be used as search tags. A generic source row, filename, or neighboring image does **not** prove visual meaning.

### Compatibility and licensing

This is **schema v3**, a breaking catalog-layout change from the old 3.3 MB v2 manifest. Existing icon IDs, source atlases, crop rectangles and crop hashes are preserved. Consumers should iterate `manifest.json → sheets[].manifest → icons[]`; see [architecture and migration contract](docs/ARCHITECTURE.md).

The Apache-2.0 root license applies to project code and metadata. Art assets were generated for this project; their **visual quality and provenance remain under review**, so do not treat an unreviewed icon as a guaranteed original, publication-cleared illustration. The historical third-party research pack is not included.

## Visual-review progress (v0.5)

734 of 2,073 icons now have inspected visual names, narrowly scoped subjects and useful search tags. This patch adds 685 visual reviews across programming-adjacent tools, networking, hardware, data/AI, files/media and UI controls. The remaining 1,339 are explicitly unreviewed and have no invented semantic tags. Visual labeling does not confer legal or artwork-clearance status.

Search scores direct token matches above related-word matches to prevent a broad synonym like `heat` from returning unrelated hardware when looking for `fire`. Exact asset IDs and crops are unchanged.
