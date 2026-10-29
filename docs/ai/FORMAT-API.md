# Visual Atlas manifest/API contract — authoring guide

This is a **data contract**, not a network service or executable scripting API. An application loads a ZIP and resolves asset IDs through its manifests. The builder runs in the browser without sending private files to Superior MI Labs.

## Packaging

```text
collection.json                     # optional: for several manifests
packs/robot/manifest.json          # smi-visual-pack/1
packs/robot/textures/body.png      # paths relative to that pack manifest
packs/gui/manifest.json            # another pack in same bag
packs/gui/textures/controls.png
```

One-manifest ZIPs can simply contain `manifest.json` and `textures/...`. Each pack must declare `schema`, `pack_id`, `version`, `textures` and `assets`. A collection index can declare `collection_id`, `name`, `packs[].manifest`, and a default `entry_asset`. Do not duplicate or rename IDs across manifests. The index enumerates actual manifests; paths must be safe and relative. Use the [collection schema](../schemas/smi-visual-collection-v1.schema.json) and [pack schema](../schemas/smi-visual-pack-v1.schema.json) instead of inventing fields.

## Fundamental asset kinds

- **region:** points to an exact `[x, y, width, height]` rectangle and texture ID. Optional logical size, pivot and nine-slice margins. This is also the correct representation for one cell of a grid.
- **sequence:** list of asset/frame references, `default_fps`, `playback` and optional per-frame `duration_ms`. Frame count is derived from `frames`; name and tags describe the animation.
- **composition:** ordered layers referencing assets, typed inputs, optional animated property tracks, slots and presets. Can compose static and animated sources.
- **state_set:** maps state names (e.g. idle/walk/hurt, hover/pressed, on/off) to asset IDs, with a default state.

**Interactions:** optional `behavior` declares a role, named events, safe set/toggle/emit operations and typed outputs. Host applications own real mouse/keyboard/game input. No arbitrary JS or code is executed from uploaded packs.

**Slots/presets:** optional versioned interface definitions and explicit compatible options permit a composition to swap a fluid fill, equipment layer or stateful animation, without relying on fuzzy tags. A matching interface declaration is necessary but cannot prove artistic alignment by itself. Presets choose only declared slot options and typed input values.

## Searching and discovery

Search metadata is attached to authored asset records: `id`, `name`, `description`, `tags`, `subjects`, and optional style/license. Use words **grounded in visible content and intended behavior**, not invented keyword stuffing. Root/sheet icon manifests stay authoritative; site search and export indexes are derived. IDs must be stable even after repacking textures.

## Request-specific acceptance tests

The AI writes a small **separate** `smi-ai-acceptance/1` JSON describing what the user requested. The local runner can prove that an asset has the right kind, animation length, distinct frame images, named states, preset slot selections, declared inputs, and meaningful tags. See [`examples/acceptance/character.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/character.json) and [`examples/acceptance/potion.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/potion.json).

```bash
python3 tools/ai_acceptance.py OUTPUT.zip --acceptance MY-ACCEPTANCE.json --out qa/acceptance
```

This machine gate **cannot** certify correct creative meaning or design aesthetics. Inspect contact sheets and live previews as required in the release checklist.

## Existing public icon CLI

In a full repository checkout, the bundled resolver supports stable icon IDs and curated search terms:

```bash
python3 atlasctl.py search flame
python3 atlasctl.py search picture --status reviewed
python3 atlasctl.py info icons.candidate.programming.r04i19
python3 atlasctl.py crop icons.candidate.programming.r04i19 --out flame.png
```

Browser packs use `id`, human-readable `name`, `tags`, `subjects`, styles and asset-kind facets; generated discovery data is **derived from the source manifests**. Do not edit the generated search index instead of a manifest.

## Rendering and export

Manifests define the geometry, defaults, frames, state mapping, layer order and compatible choices; host applications decide how to draw and respond to events. Source pixels are separate from generated previews. Export must carry the transitive dependencies and all chosen options, along with license/attribution notices.

**Important limitations:** v1 uses supported Canvas 2D properties only. Don't require code execution, unknown shaders, rotated packing or unsupported blend/easing behavior from this format. See [examples by task](INDEX.md) and run [release QA](RELEASE-CHECKLIST.md).

### Non-unit numeric interaction values (important)

The creator may specify a number input with `min:0, max:100` or `min:40, max:60`. The manifest stores native values and outputs (e.g. 72%, 50°C). Preview clipping and position bindings convert those values to a unit fraction using `(value-min)/(max-min)`. Never feed 72 directly to a renderer that expects a 0..1 fraction. Check min / mid / max **visually**, including layer occlusion. Invalid numeric range (max <= min) is not a working contract.
