# Recipe: static icons and grid sheets

**Start from:** [working single-icon ZIP](../../demo/icons.zip) and [blank 24×8 layouts](../../templates/authoring-grids.zip).

1. Specify final display style, logical icon size, safe padding, foreground alpha/tintability and icon names/tags.
2. Design/inspect icons **individually**. Never assume a generated image has mathematically uniform rows or columns. Measure each symbol's actual bounding box.
3. Pack vetted symbols into a clean exact-coordinate atlas. Every icon becomes a `region` with its real `[x,y,w,h]`; a grid is only an optional layout aid.
4. For a large collection, use multiple sheets/manifests and one `collection.json` if useful. Stable asset IDs never depend on physical sheet positions.
5. Run [release checklist](../RELEASE-CHECKLIST.md). Review every cropped symbol; reject unrelated fragments and unverified semantic labels.

Example contract source: [`examples/icons/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/icons/manifest.json).


## Required icon production pipeline

1. Convert creator request to a list of exact visual concepts and intended tags; avoid invented labels.
2. Select style, pixel canvas, baseline, stroke width and transparent padding; preserve a consistent family.
3. Generate source candidates **outside** the final atlas; inspect complete individual glyphs.
4. Measure actual crop boundaries, repack vetted glyphs into declared rectangles and maintain stable IDs.
5. Review every thumbnail/contact-sheet cell at native UI scale and multiple tints/backgrounds.
6. Test each crop for nonempty alpha, safe margins, neighboring-pixel contamination and semantic accuracy.
7. Run validator, pixel QA, acceptance tests and final ZIP reimport; mark uncertain symbols NEEDS REVIEW.
