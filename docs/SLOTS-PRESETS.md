# Visual Atlas — versioned compatibility slots and presets (v0.9)

**Status:** implemented for `smi-visual-pack/1` as an additive extension. Existing packs and 2,073 official icons remain compatible.

## Goals

AI creates a collection ZIP containing many manifests and textures; the visitor drops one ZIP into My Bag, opens its entry asset, selects optional presets, and exports. No manual layer construction is required.

## Contract

The optional `interfaces` map is authored at the pack level. Every interface ID must be versioned with `/1`, e.g. `smi.slot.potion.fluid.96x96/1`. Each interface declares `size_px` and `allow_scale` explicitly. A candidate asset uses `implements: ["..."]` to promise it implements a contract. This is **structural compatibility**, not proof that the artwork visually matches; AI-generated imagery must still be inspected.

A composition's `slots` map binds a name to `{label, accepts, default, options}`; `options` contains explicit approved asset IDs only. Every option must declare the exact same interface ID (version included) and satisfy dimension requirements. A composition layer references either `asset` or `slot`, not both. `presets` assign named slot choices and optionally typed input values. `default_preset` names the initial preset.

An asset remains a `region`, `sequence`, `composition`, or `state_set`. A template is simply a composition with slots and presets, **not a new rendering engine**. `sequence.frames` and timings define animations; there is no duplicated frame count. The browser's generated controls use authored names, never guessed tags.

## Multi-pack example

`web/demo/potions-collection.zip` contains:

```
collection.json
packs/bottle/manifest.json
packs/bottle/textures/bottle.png
packs/fluids/manifest.json
packs/fluids/textures/fluids.png
LICENSE.txt
```

The collection's `entry_asset` is `smi.potion.bottle`. The bottle pack owns the composition and the `fluid` slot. The fluids pack defines its versioned contract and three compatible options: green static health, blue looping mana sequence (3 frames, 6 FPS), and purple poison. Presets `Health`, `Mana`, and `Poison` change the fluid without replacing the bottle. This fixture is original test artwork, not an endorsed product illustration.

To validate: `python3 tools/validate_visual_pack.py web/demo/potions-collection.zip` and `node tests/slots-presets.cjs`.

## Packaging and export invariants

- The composition's default preset is automatically selected when its Bag is opened.
- Users see only manifest-declared compatible option names. Other public/local assets are **not** silently considered interchangeable.
- Dependency closure includes **all allowed slot options**, even when only one preset is selected, so an exported pack still contains working alternatives and the required versioned interfaces.
- IDs and inter-manifest references remain stable. Pixel rectangles are exact; grids are optional.
- Private bags keep their interface declarations separate. Exporting a composition from two bags with conflicting interface definitions is rejected instead of choosing the most recent import.
- Schema + semantic checks reject unknown contracts, options not implementing a contract, invalid sizes, unused/missing slots, invalid preset values, reference cycles and missing textures.
- Authors can keep using the advanced timeline and composition tools, but the main user path is **Import → Browse Bag → Preview → Select preset → Export**.

## Boundaries

No automatic visual fit inference, state-machine scripting, shader engine, dynamic external dependency downloads, or automatic public uploads. `allow_scale` declares explicit resize compatibility, but cannot guarantee a good composition. Host code owns pointer interaction, game logic and emitted events. License and source-provenance claims remain per asset; the mere presence of a contract cannot establish rights.
