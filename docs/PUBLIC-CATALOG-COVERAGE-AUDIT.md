# Public catalog coverage and metadata audit — 2026-11-07

## Source of truth

Published collections are exclusively listed in `publications.json`. Each collection's `collection.json` and `manifest.json` define the public assets, textures and dependencies. `tools/build_site.py` generates `site/public-catalog.json`. Do **not** manually maintain a second public search index or copy image assets into an unrelated publishing system.

## Current public-source coverage

| Classification | Inventory | Browser treatment |
| --- | ---: | --- |
| Approved assets across 13 collections | 6,056 | Published, searchable and downloadable |
| Historic white-monoline archive | 2,073 | Searchable with explicit archive/review labeling; excluded from unfiltered recommendation view |
| New Wolfcat icon cells | 3,392 | In approved catalog, with broad visually grounded row/category names |
| New Wolfcat full-sheet previews | 53 | In approved catalog as atlas-region assets |
| New StoryForge atlas icons and 24 previews | 1,560 | In approved catalog |
| New StoryForge consumable icons and 5 previews | 325 | In approved catalog |
| New Kissyn loading frames and animation | 17 | In approved catalog |

Published manifests include `region` entries used as layers or frame components: these components are not hidden simply because a composition references them. The public catalog is a complete projection of the approved manifests, not a list of only top-level templates.

## Repository material excluded from the public catalog

These are intentional **source or tutorial** exclusions, not lost icons:

- `examples/icons/`: 1 tutorial asset.
- `examples/animated-icons/`: 4 tutorial assets, including a sequence.
- `examples/character-animations/`: 11 robot animation tutorial assets.
- `examples/interactive-hud/`: 4 tutorial GUI assets.
- Thus **20 intentionally unpublished tutorial entries**; generated demo ZIPs are removed from Pages by `tools/prune_public_site.py`, while the examples remain in the repository.
- `source-images/`: 10 original source atlases used for the 2,073 historic icons. The registered icon regions already reference their extracted published atlas sheets. The original source images are not additional independent public icons.
- `sheets/`: generated icon atlas PNGs and image-processing/review masks. Masks and outlines are implementation material, not distinct icons.
- `production/fantasy-rpg-hud-wave1/source-svg/`: editable vector layers backing the existing approved HUD asset collection, not a second set of finished registered icons.
- `production/royal-forge-controls/` and `production/royal-forge-hud-resources/`: production and QA source bundles, not additional approved collections.
- `production/sky-blue-eyes/`: plan, review and rejected/unapproved character experiments; do **not** publish as finished artwork.

## Naming and search quality findings

The Wolfcat source originally provided sheet/row/column identifiers and generic tags (`uncatalogued`, `grid-cell`, `rpg`), not per-icon subjects. For the November 7 review, the 53 source textures were inspected in visual contact sheets and the **3,392 cell records** were given conservative **sheet/row-level** names, meaningful category tags and subject facets. The 53 sheet-preview records were also named by visual family.

These are **category candidates**, not verified exact item identifications. A visual grouping can support labels such as *Sword*, *Bow*, *Potion* or *Game HUD*, but not invented magic effects, material, rarity, game rules, provenance or unique item identity. The stable IDs and every pixel crop remain unchanged so per-icon annotation can replace broad labels later without breaking links.

StoryForge names were already individual and descriptive. Only safe name-derived search alternatives were added (such as *missing image* for *Broken Image* and *flask* for *Potion*); the atlas family was added to subject facets. Previously published HUD/control/pixel effect items with missing subject facets received their existing collection's appropriate broad domain.

## Discovery behavior and regression tests

- The client searches `name`, `id`, `aliases`, `tags`, `subjects` and the historic thesaurus; don't add a new metadata source or client-side hardcoded exceptions.
- `tests/browser-search.cjs` verifies inventory, preserved legacy search, meaningful Wolfcat discovery queries, subject coverage and alternate StoryForge search terms.
- `tests/test_public_catalog.py` protects public registry and expected counts.
- Use `bash RUN-ALL.sh` for reproducible local tests and the existing Playwright checks before publishing new images.
- Batch related metadata changes into **one commit** to avoid unnecessary GitHub Actions runs.

## Further quality work

Individual Wolfcat icon identity, material, element and rarity remain **unverified** at pixel level. A later per-cell review can provide more precise names and tags. Do not represent broad row labels as fully confirmed individual semantics, and do not publish unapproved source-only examples simply to raise asset counts.
