# Browse classification

Use the [canonical browse vocabulary](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/browse-taxonomy.json). New assets may declare optional `classification` at collection-index level for shared defaults and asset level for overrides. This is discovery metadata only; existing domain, subjects, style, tags, licenses and runtime contracts remain authoritative. Example:

```json
{"classification":{"category_path":["world.props.containers.chests"],"perspective":["isometric"],"theme":["fantasy"],"medium":["raster-2d"],"family":"painterly-fantasy"}}
```

Choose actual categories; use multiple paths only when genuinely applicable. The builder derives parent categories. Perspective describes intended visual presentation, not a certified projection angle or game-engine compatibility. Isometric art can still be 2D raster; screen-space, side-view and top-down are independent of theme and category. Use unknown or omit unsupported classifications. The existing formats are PNG-backed 2D raster; a future 3D model category does not implement 3D rendering. Runtime capabilities are derived from actual manifests, not inferred from taxonomy. Never claim compatibility from category tags.

Existing collections have conservative migration defaults in the taxonomy, avoiding changes to their ZIPs. For new families or categories, extend vocabulary once and use manifest declarations; do not add a second per-asset registry or hardcode navigation. Published browsing counts are generated from actual standalone entries; collection downloads also contain reusable dependencies. Archive browsing is separate from published discovery. Do not infer artistic review or host support from a directory label.
