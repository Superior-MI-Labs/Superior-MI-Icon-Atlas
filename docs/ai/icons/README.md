# Recipe: static icons and grid sheets

**Start from:** [working single-icon ZIP](../../demo/icons.zip) and [blank 24×8 layouts](../../templates/authoring-grids.zip).

1. Specify final display style, logical icon size, safe padding, foreground alpha/tintability and icon names/tags.
2. Design/inspect icons **individually**. Never assume a generated image has mathematically uniform rows or columns. Measure each symbol's actual bounding box.
3. Pack vetted symbols into a clean exact-coordinate atlas. Every icon becomes a `region` with its real `[x,y,w,h]`; a grid is only an optional layout aid.
4. For a large collection, use multiple sheets/manifests and one `collection.json` if useful. Stable asset IDs never depend on physical sheet positions.
5. Run [release checklist](../RELEASE-CHECKLIST.md). Review every cropped symbol; reject unrelated fragments and unverified semantic labels.

Example contract source: [`examples/icons/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/icons/manifest.json).
