# Game item icons — HD pixel-art production contract

**Status:** new artwork standard for future game-icon packs. This supplements the existing [icon recipe](README.md), [GUI recipe](../gui/README.md), and [release checklist](../RELEASE-CHECKLIST.md). It does **not** replace the manifest, renderer, builder, or publication pipelines.

## Non-negotiable visual direction

- **Create genuinely painted raster pixel art**, not outline glyphs, monochrome vector approximations, or procedural SVG item icons. SVG may be useful for technical UI geometry in unrelated packs; it is not a required or preferred source format for these game items.
- Work from the selected **HD fantasy pixel art** look: readable silhouettes, convincing volume and material (glass, metal, wood, fabric, leather, crystal), crisp deliberate pixel clusters, upper-left primary light, restrained highlights and coherent saturation.
- Draw the actual **item**, not an inventory frame permanently burned into its texture. Inventory slot chrome, rarity frames and interaction treatments are separate assets/layers.
- Each subject must be unmistakable at **64 px and 128 px** on dark and light backgrounds. Review real raster crops at 1×; do not infer quality from a large marketing composite.
- Keep equipment proportions, viewing angles, palette and light direction consistent. Flat vector shapes, generic emoji-looking glyphs, repeated silhouettes with simple hue swaps, and AI-generated fake spritesheet posters are rejection criteria.
- Distinguish meaningful variations (bottle geometry, material, blade silhouette, heraldry), not merely recolored duplicates.

## Logical canvas and texture atlas

- New normal item icon **logical canvas: 128 × 128** with transparent RGBA. Place art inside a measured safe area; no fixed 4px margin if the subject needs different silhouette spacing. The template is a *packing destination*, never evidence that generated imagery has accurate cell boundaries.
- Preferred *full* sheet: **16 columns × 8 rows, 128px cells = 2048 × 1024 PNG, 128 item regions**. Use smaller partial sheets (for example, **4 × 4 = 512 × 512**) to avoid a large mostly empty GPU texture during pilots.
- Each authored `region` references the exact texture and `rect_px`. Preserve stable IDs when repacking. Packed freeform rectangles are permitted for non-square/UI effects and animations.
- Keep PNG alpha true and optimize **losslessly**. Compare pixel hashes before/after. Never convert color modes or quantize as a supposed lossless optimization. Treat compressed disk size and uncompressed GPU usage as different metrics.
- One original source icon per subject. Generate concept candidates individually or in small inspectable batches, **then deterministically** pack approved crops. If source is a *poster with frames/backgrounds*, extraction is a **review candidate only** until every halo, border remnant, or cut edge has been inspected and corrected.
- Keep the original raster source or reproducible authored source separately from runtime textures; do not invent source provenance.

## Reuse existing contracts, don't fork the engine

- Continue with `smi-visual-pack/1` and `smi-visual-collection/1`. **No new mandatory manifest format.**
- Base items are `region` assets. Optional animated items use `sequence`. Interaction appearance variants use `state_set` and `composition`; compatible artwork is provided with validated `slots` and `interfaces`.
- The shared slot composition should accept any compatible 128px item and layer optional shared effects over it. Do **not** duplicate hover/pressed/selected/cooldown art for every item, and do not write a separate icon renderer.
- Base interaction state (`default`, `hover`, `pressed`, `disabled`) is separate from orthogonal statuses (`selected`, `new`, `equipped`, `cooldown`, etc.). Host game code owns pointer, keyboard, equip/cast rules and valid action state. Visual metadata never decides whether gameplay actions are legal.
- Use existing supported effects honestly. A Y-axis clip creates a **linear** cooldown veil; it does **not** implement a radial sweep. A radial effect requires explicit qualified renderer support, not cosmetic metadata claiming otherwise.
- Respect existing `behavior` contracts and never add executable JavaScript to user-supplied manifests. Do not rely on schema fields such as `tint` without verifying renderer support first.
- Icon labels, style, tags, subjects, license, IDs and source rectangles live in authored pack manifests. Search index and previews are generated. `publications.json` is only the publication allowlist, never an editable second asset catalog.

## Release recipe for AI creators

1. Read the current request and approved art direction. Enumerate the exact subject inventory, objective visual differences, state controls and acceptance tests.
2. Choose a source batch sized for **actual visual inspection** (16-item pilot before 128-item sheets is sensible). Generate *original* raster icon artwork or carefully verified isolated source sprites, without template frames painted into item pixels.
3. Inspect every individual crop for subject fidelity, material, alpha, missing pieces, light, neighboring contamination and consistent optical size. Reject frame bleed/ghost fragments; do not report such a candidate ready.
4. Pack the reviewed art into measured RGBA texture(s); derive exact rectangles and SHA-256 texture hashes. Produce region IDs independent of grid index.
5. Define one reusable typed item-slot composition with compatible slot options, optional state overlay, selected/new flags, and any actually supported value controls. Use no new behavior engine.
6. Generate a **contact sheet**, default/hover/pressed/selected/disabled/cooldown composite samples, and inspect them on dark/light backgrounds at 64/128. For every named state verify a visibly distinct, correctly composited render using the **shared** renderer, not a standalone mockup.
7. Run `tools/validate_visual_pack.py`, `tools/qualify_asset_zip.py`, the relevant `tests/browser_visual_matrix.py` scenario, a creator-specific `tools/ai_acceptance.py` test, the ZIP import→export→reimport test and project `RUN-ALL.sh`. Report **PASS / WARN / NOT RUN** accurately for each; unknown is never PASS.
8. Submit as **unpublished candidate** until visual QA, license/source review, and creator approval. Only then add the finished pack to `publications.json` and generate public catalog entries.

## First production pilot

Suggested subject set: health/mana/poison/arcane potions; knight helmet and chestplate; leather boots and lion shield; ruby ring and sapphire pendant; sealed scroll and spellbook; sword, axe, bow and fireball. That is **16 distinct designs** in a compact 4×4 512px atlas. These are a *pilot inventory*, not a declaration that all art is finished or rights-cleared.

Expand by category after a successful 16-item pilot: consumables, weapons, armor, jewelry, abilities, materials, tools and skills. Avoid filling a sheet with low-quality placeholders just to reach a count.

## Anti-regression checklist

- No switch from raster pixel art to vector glyphs without explicit creator approval.
- No monolithic 4,864-item manifest or per-icon JSON files when a category/sheet manifest suffices.
- No duplicate effect texture per item.
- No pretending a generated marketing sheet is an accurate alpha spritesheet.
- No publishing draft crops, unverified names, source rights, or broken assets.
- No significant renderer additions for visual effects until existing layers, states, tint capability, and tested fallback options are exhausted.
