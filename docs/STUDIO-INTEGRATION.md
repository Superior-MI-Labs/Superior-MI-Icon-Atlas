# Studio integration contract

Use the existing Studio graph/node/type/port model. Icons are presentation references; they cannot create executable operations or grant capabilities.

The `manifest.json` is authoritative for IDs, paths, geometry, source and variants. Search indexes and HTML browsers are generated projections, not other sources of truth. Preserve any selected concept ID when rendering alternate visual variants. Missing IDs use Studio's existing icon fallback and emit a diagnostic.

**Default shared assets**
- Linux: `${XDG_DATA_HOME:-$HOME/.local/share}/superior-mi/icon-atlas`
- Windows: `%LOCALAPPDATA%\SuperiorMILabs\icon-atlas`

For each manifest icon, crop the sheet using `rect_px`, not glyph-detection guesses. To tint, draw its fixed black outline and composite the chosen foreground color using `foreground-mask.png`. Never recolor the outline with a whole-image CSS filter. `uv` values are normalized to the full sheet and use top-left origin.

Applications should store only the stable `id` or `concept_id` and a presentation preference, not raw sheet-cell coordinates in component descriptors. Resolve at runtime against the installed catalog. Enforce original-only policy for public distributions.
