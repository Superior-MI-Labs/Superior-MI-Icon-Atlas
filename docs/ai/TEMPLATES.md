# Authoring templates and grids

Download the [grid starter ZIP](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/templates/authoring-grids.zip) for **blank RGBA canvases** and **guide-only grid overlays**. The overlays are never production textures; their lines will contaminate alpha crops if exported into a release.

| Template | Geometry | Typical use |
| --- | --- | --- |
| icon-24x8 | 24 columns × 8 rows × 96px | Icon and glyph packing |
| sprite-8x4 | 8 columns × 4 rows × 96px | Animation frames |
| ui-regions | 512×256 freeform canvas | Buttons, sliders, fill masks, nine-slice panels |

**Important:** These are *output coordinate systems*, not guaranteed layouts of AI-generated artwork. Extract complete, individually verified symbols first. Then place them on these exact coordinates and generate asset regions from real bounds.

**Working example packs:** [Multi-manifest potion compatibility](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/demo/potions-collection.zip) and [animated glass/components](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/demo/starter-pack.zip). Copy their manifest structure rather than inventing a new schema.

**Manifest recipes:** `region` describes exact crop pixels; `sequence` orders region refs and timing; `composition` assembles layers and typed inputs; `state_set` maps names to variants; `slots` and `presets` select declared compatible replacements. Keep names and tags about observed content rather than guessing. Use the [JSON schemas](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/schemas/smi-visual-pack-v1.schema.json) as the authoritative field list.
