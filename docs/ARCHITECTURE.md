# Icon Atlas manifest and search architecture

## Decision and alternatives

**Rejected: one monolithic icon JSON file.** Fast to prototype, but every icon addition rewrites a multi-megabyte file, produces large Git diffs, blurs sheet ownership and encourages redundant coordinates and duplicated filters.

**Rejected: one JSON file per icon.** Naturally modular but creates thousands of small files, expensive I/O, difficult review of a texture as a unit, and an unnecessary burden for GitHub Pages.

**Selected: small root index + one authored manifest per atlas sheet + generated projections.** Texture sheets are already the physical distribution unit, so one manifest owns its specific 0–192 icons. One universal resolver builds all search, site, CLI and application views. The root registry is not itself a second icon list.

## Authoritative layout

```
manifest.json                     # schema smi-icon-atlas/3, style registry, synonyms, sheet refs
manifests/programming-00.json     # schema smi-icon-atlas-sheet/1, sheet and 0..192 curated entries
manifests/files-media-00.json
sheets/programming-00/atlas.png   # white RGBA, 24 × 8 cells of 96 px
sheets/programming-00/black-outline.png
source-images/                    # research provenance, never used as runtime texture
web/                              # presentation only
atlasctl.py                       # resolver, search and image contract
site/                             # derived output; ignored by git
```

`manifest.json` and `manifests/*.json` are authored inputs. The browser's `catalog-data.js`, search index, derived `rect_px` and `uv` are **generated** from them, never edited independently.

Root fields: `schema`, `version`, `pack`, `styles` (style IDs and properties), `search.synonyms` (concept-specific expansion), `sheets` (sheet manifest refs), `review_policy` and provenance note.

Sheet fields: `schema`, `sheet` (ID, category/domain, style, variant, texture path, dimensions, checksums and optional overlay), `icons` (immutable ID, `[x,y]` cell, per-crop hash, source evidence, `review` and license/provenance status).

Example reviewed entry:

```json
{
  "id": "icons.candidate.programming.r04i19",
  "cell": [19, 4],
  "review": {
    "status": "reviewed",
    "name": "Flame",
    "concept_id": "nature.flame",
    "subjects": ["nature.fire"],
    "tags": ["fire", "flame", "burn", "blaze", "burning", "heat", "hot", "combustion"],
    "aliases": ["Fire icon"],
    "art_status": "candidate"
  }
}
```

The full entry also includes the crop checksum, source image bounding box/region and provenance/license review. The row/column is **zero-based**, the origin is **top-left**, and the pixel rectangle is computed as `(x × 96, y × 96, 96, 96)`. UV is derived by dividing the rectangle by the sheet dimensions. Do not author a second rectangle that can drift from the cell.

## Semantics, names, styles and variants

- **Asset ID** addresses an existing crop and never changes because its meaning was recognized later.
- **Concept ID** is an optional semantic grouping assigned through visual review; it is *not* an executable Studio node kind.
- **Name** is human-readable and reviewed; unreviewed names are generated from their actual grid position.
- **Tags** describe what is visibly present. No broad generic keyword stuffing.
- **Aliases** record other human names for the same pictured subject.
- **Synonyms** are curated *concept-level* query relations (e.g. picture/image/photo) and never imply all matching images are equal.
- **Domain** is the collection/sheet's origin, not necessarily a full ontology of the icon's meaning.
- **Subjects** represent cross-domain topics such as `nature.fire` so the flame can live in the programming sheet yet be browsable under Fire.
- **Style** is declared once at the sheet level (`white-geometric-monoline`) and inherited by all entries. New styles can be added as new sheets and referenced by their IDs.
- **Review status** (`reviewed`/`unreviewed`) is separate from artwork quality and licensing clearance.

## Search and filtering

Search uses normalized case-insensitive tokens, AND across query tokens, curated synonyms and weighted fields: exact ID/name > aliases > tags > subject > domain > style. Do **not** use raw substring matching, which produces false positives (e.g. `ram` matching `programming`).

Filters are derived from the catalog data: domain, style, subject and review status. Neither UI nor client projects maintain their own tag registry.

## Renderer contract for any application

1. Read the root manifest and each `sheets[].manifest` once (or consume a *generated* compact index).
2. Resolve a stable icon ID to the owning sheet and cell. Cache the 2304×768 atlas **once per sheet**, not 192 individual files.
3. For ordinary rendering, crop the 96×96 region of `atlas.png` with alpha blending.
4. For recoloring, use `atlas.png` **alpha** as a mask for the user-selected color, and optionally draw `black-outline.png` as a separate outline pass.
5. Unknown IDs display the application's usual fallback. Report nonfatal diagnostics; never infer a programming type or operation from the icon alone.
6. The browser's individual PNG download filename remains `<immutable-icon-id>.png`.

The same pack can serve Studio, websites, native apps, games, and toolkits. No special-case Studio registry is required.

## Versioning and migration

v0.3.2 `manifest.json` was `smi-icon-atlas/2` and contained every icon inline. v0.4.0 `manifest.json` is `smi-icon-atlas/3` and links to per-sheet JSON; code reading the old inline shape must use `atlasctl.load()` or implement the documented resolver. The pixel atlas artwork and IDs remain unchanged. Generated browser data still arrives as `window.ICON_ATLAS_DATA`.

Original raw source images and QA screenshots are retained for provenance. Duplicate `foreground-mask.png` files were removed only after byte-for-byte matching their corresponding atlas PNGs. `inspection-preview.png` is for authors, not production rendering.

## Visual Atlas v0.7 optional animation extension

The existing root registry and per-sheet icon manifests remain authoritative and unchanged. The separate `smi-visual-pack/1` schema accepts optional `duration_ms` and `playback` on compositions. Composition layers accept **tracks**, each containing a named numeric property and strictly increasing `keyframes` with `time_ms`, `value`, and optional `easing` (`linear`, `smooth`, `step`). Valid properties are `x`, `y`, `opacity`, `scale_x`, `scale_y`, `rotation_deg`. Frame count derives from referenced sequences; it is never duplicated as an authored field.

The pure `web/timeline-core.js` handles interpolation and time normalization for both the preview and Node tests. A composition renderer uses the evaluated fields without mutating the authored manifest. Old packs with no tracks remain unchanged. When exported, the builder writes the same optional fields into portable pack manifests. PNG-frame ZIPs contain rendered images plus `frames.json` timing metadata; those are convenience outputs, not an authored source of truth. Game engines may consume the portable pack natively or use flattened frames.

Tracks are deliberately limited: no arbitrary code, event scripts, networking, shader expressions, or transitions requiring physics. Future texture-channel animation should extend the controlled property vocabulary rather than embedding executable expressions.

X/Y keyframe values are **additive displacements** relative to a layer’s `offset_px`. The builder scene uses the same rule so exported and reimported manifests render at the same coordinates.
