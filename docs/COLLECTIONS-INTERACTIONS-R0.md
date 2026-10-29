# Visual Atlas v0.8 — ZIP collections and declarative interaction contracts

## Design rule

**One ZIP is a collection, not one sprite.** A ZIP may include one or many independent `smi-visual-pack/1` manifests. Every pack may own multiple sheets, many regions, animation sequences, layered compositions and state sets. An optional root `smi-visual-collection/1` `collection.json` defines the display name, ordered pack groups and default entry asset. Cross-manifest references use stable asset IDs; all references must be within the ZIP.

`collection.json` is a lightweight index and does not repeat individual asset definitions. Every asset has exactly one owning manifest. The public Icon Atlas catalog continues to resolve its legacy icon sheets independently.

Example structure:

```
collection.json
packs/character/manifest.json
packs/character/textures/idle.png
packs/character/textures/movement.png
packs/combat/manifest.json
packs/combat/textures/attack.png
packs/hud/manifest.json
packs/hud/textures/ui.png
```

One ZIP becomes one **My Bag** entry. Opening the bag shows the collection's default asset and allows filtering by sub-manifest. The data is kept in browser memory unless the visitor explicitly enables local IndexedDB persistence for future imports. Local browser storage is not cloud storage or a reliable backup. A removed bag should no longer contribute assets, texture references or composition layers to the session.

## Interaction contract (optional)

Rendering is separate from functionality. The host sends semantic events and receives typed outputs; the manifest contains no executable code. The `behavior` object is optional, compatible with older `smi-visual-pack/1` assets:

```json
{
  "id": "demo.slider",
  "kind": "composition",
  "size_px": [240, 30],
  "inputs": {"value": {"type":"number", "default":0.1, "min":0, "max":1}},
  "layers": [{"id":"fill", "asset":"demo.slider.fill", "clip":{"input":"value","axis":"x","origin":"start"}}],
  "behavior": {
    "role": "slider",
    "outputs": {"value": {"from_input":"value", "unit":"normalized"}},
    "on": {
      "set_value": [
        {"op":"set", "input":"value", "source":"event.value"},
        {"op":"emit", "event":"value_changed"}
      ]
    }
  }
}
```

The sample is **an illustration**; its referenced texture asset must exist in the same collection for the ZIP to validate. `set_value` with `event.value = 0.12` produces output `value = 0.12`. A host can display this as 12%, bind it to an application variable, or use it to update a game state. The contract does not run application code itself.

Supported event-handler actions in v0.8: `toggle` (boolean input), `set` (constant or supplied event value) and `emit` (named event carrying the updated output snapshot). Host adapters can supply `activate`, `hit`, `toggle_rain` and other semantic event names. They must not infer pointer/keyboard behavior from an image alone. The browser currently offers test buttons and native generated controls; direct canvas hit-testing is not yet implemented.

For GUI slider accessibility, the host adapter must implement a real range control or equivalent keyboard-accessible semantics, with current/min/max values. For a game character, an `animation` enum input can drive a state set, while `hit` or `attack` events can request a state change. The renderer still uses the same regions, sequences, layers and state-set engine.

## Compatibility and future templates

**Named slots and presets** are the next independent extension. Templates remain compositions, not a new rendering engine. A slot contract declares what can be substituted (geometry, clipping bounds, anchor, compatibility version); a preset binds a list of compatible choices and parameter values. Two similarly tagged textures are *not* automatically compatible. Require explicit interface compatibility and validated geometry, especially for potion fluids, HUD fills, armor, character paper dolls and GUI skins.

## Deployment and safety

The builder is static and GitHub Pages compatible. ZIPs are parsed in-browser. No private files are uploaded to the hosting organization. The importer rejects unsafe relative paths, excessive ZIP members, oversized texture entries, broken references, duplicate IDs and reference cycles. The Python validator also checks declared image geometry, ZIP symlinks and schema validity. Imported files must never contain script execution or external texture references.

GitHub Pages hosts the catalog/builder; it is **not** a storage service for visitor-owned ZIPs. Publishing a public collection remains a separate reviewed GitHub contribution.

## Test evidence

- 20-manifest ZIP with cross-sheet composition passes the browser importer and Python validator.
- One private Bag is created; users may open and filter individual manifest groups, export or remove the original ZIP.
- Typed `toggle`, `slider` and `actor` events pass standalone JavaScript tests.
- Demo imports expose live output changes. One browser export of a multi-sheet composition passes standalone ZIP validation after removing ephemeral Bag bookkeeping fields.
- The existing 2,073 icon IDs and texture rectangles remain unchanged.
