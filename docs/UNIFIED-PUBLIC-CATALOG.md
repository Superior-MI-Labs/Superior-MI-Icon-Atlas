# Unified Visual Atlas Public Catalog — Implementation Contract

**Status: APPROVED DIRECTION / NOT YET IMPLEMENTED.** This document describes the coordinated replacement for the public site. Never remove the old gallery before the new catalog is built, tested, and deployable. No changes to the already published Fantasy RPG HUD artwork or IDs.

## Product decision

The public homepage is **one searchable asset library**, not two independent sections called "Explore packs" and "Browse the white geometric icon atlas". Remove both those interfaces and the introductory monoline copy in the coordinated site replacement.

Expose **only published, rights-cleared, approved collections** on the public homepage. The current initial collection is `examples/fantasy-rpg-hud-wave1`. Pending Wave 2, tutorial packs, and 2,073 historical white-monoline icon candidates must not appear as public search results.

Do **not** casually delete historical source art, test fixtures, or APIs from the repository. Existing `smi-icon-atlas/3` sources and tutorial fixtures may be preserved internally while decoupled from the published site build. Old public demo files should stop being included in the **deployed** site after tests are updated to use local fixtures, not deleted blindly before test migration.

## Architecture: one authored source, multiple derived views

Keep existing authoritative `smi-visual-pack/1` and `smi-visual-collection/1` manifests and stable asset IDs. Do not add a second editable searchable list or a duplicated renderer.

Add a **minimal publication allowlist**, separate from asset content: pack path, publication date, approval/rights verification reference, and an optional editorial rank. This is an inclusion policy, not a second metadata registry. Tags, titles, kind, dimensions, semantic aliases, style, presets, relationships, and licensing are derived from each approved pack's real manifests. A missing/invalid license or broken dependency must block public inclusion.

The site build deterministically creates:
- `public-catalog.json`: index of **each addressable published asset**, its parent collection, kind, searchable name/aliases/tags/subjects, style, license, default state/preset, and stable identifier. This contains no duplicate authoring of asset records.
- `public-packs.json`: lightweight collection information, manifest paths, counts, releases, original ZIP download.
- Content-addressable/static image/preview products for thumbnails derived from the same public runtime/renderer, never separately authored metadata.

Do not put complete large atlases into the search index; lazy-load the texture(s) required to render visible results. Source rectangles, pivots, preview defaults and dependency closure come from the actual pack manifests. For "red slider", neither color nor semantic name may be guessed: use reviewed visible subject/color tags, token normalization (plural and compound-word aliases such as "healthbar"/"health bar"), and rank direct names above tags.

## Public browser

One responsive home:
- Compact brand/header, single prominent search field.
- Filters derived from available data: **asset kind** (compositions, regions, sequences, state sets), category/function, visual style, orientation/view (2D, side-scroller, isometric when authored), collection, license and animation.
- No empty hardcoded categories; facets are populated from approved assets.
- Default view sorts **recently published, usable compositions first**, then other useful content; show a diversity of distinct finished assets rather than leading with hundreds of atlas fragments. Sort ties by stable ID for deterministic builds.
- Search returns individual compositions, their accessible states/variants, sprites, standalone icons and reusable regions with proper grouping/badges.
- Related items show pack membership and compatible alternatives. A result can be downloaded independently without forcing the full parent pack.

Each card shows the **actual rendered appearance** (not a generic pack cover image reused for every composition), name, type, style and collection. Animate only when inspected or hovered and when reduced-motion preferences permit. Do not make the page load every texture in the catalog at once. Empty search displays clear guidance.

## Preview and builder sharing

**One renderer for both catalog and builder.** Reuse the existing Canvas 2D drawing path, state sets, sequences, composition layers, `VisualAtlasSlots`, normalized inputs and `VisualAtlasTimeline`. Avoid a second "thumbnail" renderer with subtly different clip/position behavior.

Generate *deterministic* composition thumbnails during CI by rendering the same manifest using the builder's canonical Canvas renderer at a documented default input/state/time and size; cache them in generated site output. Fail the build if a required thumbnail is blank, missing, or throws. Normal region thumbnails can be exact source-region crops.

Clicking a result opens a **single asset detail modal** with the live builder preview component (not the entire site copied into a new implementation), playback/state/preset/value controls generated from the manifest, input/output diagnostics where applicable, exact ID, creator/rights and compatible assets. Provide:
- Download **transparent PNG** for a static region or rendered still;
- Download **this asset** as a ZIP containing **only its transitive dependency closure**, required texture files (possibly atlases until repacking is implemented), manifest definitions, compatible options when required, and license/source notices;
- View/download the complete source pack separately;
- Open the full builder for advanced or private editing.

Reuse the builder's existing dependency resolver/export logic. If an export requires a shared texture atlas, clarify that the ZIP may contain unused pixels on that sheet; future repacking is an optimization, not reason to duplicate runtime logic or omit dependencies. Verify exported ZIPs validate and reimport.

## Builder and private Bag

The builder remains a local-first application. Its private uploads and saved Bag assets never enter the public search index without explicit publishing/rights review. Remove legacy built-in icons from the default builder experience when the new public asset loader replaces them. Private creator imports stay available independent of the public catalog.

If using an embedded builder modal, make the embedded view select the requested **exact asset ID**, not the pack's default last composition. Parent page and iframe must not pass raw executable code through manifest data; use safe URL parameters and validated IDs.

## Migration/release gates

1. Record approved public Wave 1 as the only initial publishable collection. Historical starter/demo packs are internal test fixtures, not published listings.
2. Extract/route the existing renderer and asset dependency export to reusable contracts; no duplicated code paths.
3. Build one **manifest-derived asset-level public index** and test searches for `slider`, `sliders`, `red slider`, `health`, `healthbar`, `heart`, `mana`, and direct IDs against actual approved assets (add truthful synonyms/tags in authored manifests where necessary).
4. Implement responsive browse grid and exact asset selection modal with live preview/interactive controls. Preview every published composition at its authored defaults and representative values.
5. Verify one-item ZIP export, shared texture dependency closure, state/preset playback, and export/reimport pixel equivalence; check license notices and archive integrity.
6. Before deploy, run current repo regression suite, existing 2,073 archival icon checks, pack visual QA, and new public-catalog tests. The archived assets can remain tested without appearing in public web artifacts.
7. Publish the new homepage and remove the old gallery/template/monoline presentation **in one atomic successful deployment**. CI must reject deployments showing a historical starter pack in the public catalog or missing an approved composition.
8. Only after that move the old assets into an explicit compatibility/archive area or delete truly unused generated outputs; never break external stable IDs or lose provenance accidentally.

## Design non-goals

No marketplace database, no publicly writable asset submissions, no browser-side source mutation, no independent catalog/renderer format, no giant handcrafted search category registry, no automatic color labels inferred from IDs, no downloading arbitrary untrusted asset scripts, no pretense that a ZIP-only preview certifies artistic quality.

**Acceptance:** users see professional composed assets first; searching one concept returns its actual independently addressable asset variants; a clicked composition previews and can export **without** requiring the whole pack; the public site contains neither the starter-template section nor the white-geometric legacy gallery. The previous manifest/API/source remain testable.
