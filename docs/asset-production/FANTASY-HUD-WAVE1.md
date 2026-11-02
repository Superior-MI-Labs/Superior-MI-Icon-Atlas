# Fantasy RPG HUD Wave 1 — Approved asset pack

**Release:** v0.2.0, approved by the creator. Source artwork is original procedural vector art offered under CC0-1.0 by its author. The earlier v0.1 candidate is superseded; do not publish it.

## Canonical packaging

- `examples/fantasy-rpg-hud-wave1/collection.json` — one collection index
- `examples/fantasy-rpg-hud-wave1/manifest.json` — one authored `smi-visual-pack/1` manifest, not an additional registry
- `examples/fantasy-rpg-hud-wave1/textures/fantasy-hud-00.png` — verified 2048×1024 RGBA atlas
- `examples/fantasy-rpg-hud-wave1/README.md` and `LICENSE.md` — authoring/rights notes
- `production/fantasy-rpg-hud-wave1/generate.py`, `PRODUCTION-INVENTORY.json`, `source-svg/` — reproducible source, not a second authored manifest
- `production/fantasy-rpg-hud-wave1/QA-RECEIPT.json`, `visual-scenarios.json`, `verify_visual_fidelity.py` — evidence and reproducible checks

The `tools/build_site.py` code automatically packages valid examples into `site/demo/fantasy-rpg-hud-wave1.zip`, then discovers the pack in `featured-packs.json`. **Never hand-maintain a duplicate ZIP under `web/demo/` or a second featured-asset list.** Do not include screenshots or original source SVG in the runtime ZIP.

## Approved scope

57 isolated atlas regions, 70 addressable manifest assets, 10 compositions, 3 slider appearance sets. Five meter types, three slider styles, fractional heart systems, hover/pressed handle appearances, compatible Health/Mana swaps. Existing icon registry is unaffected.

## Regression that must remain mandatory

The v0.1 artwork technically passed structural checks but misrepresented data. Corrected v0.2 has: a measured SVG viewBox matching the actual PNG canvas; visible meter endpoints; an HP/MP/ST badge outside the value-bearing interval; one shared slider thumb-center and fill-trail interval (25–295 px on a 320 px control); a 40 px thumb that stays within bounds.

The pack must render at `0,1,5,10,25,50,75,90,99,100` percent. Check actual canvas pixels for monotonic bar fill and visible low-end values, 100% endpoint coverage, bounded thumbs, aligned trails, and no unexpected alpha cropping or badge occlusion. Include negative tests where a false assertion fails. **A passing manifest alone is not approval.**

Run the official `tools/validate_visual_pack.py` and `tools/qualify_asset_zip.py --strict`, creator-specific acceptance and actual Chromium scenarios on **the finished ZIP**. Ensure that the export/reimport reproduces rendering at fixed values. Follow [GUI recipe](../ai/gui/README.md), [value geometry](../ai/gui/VALUE-GEOMETRY.md), and [release checklist](../ai/RELEASE-CHECKLIST.md).

## Publication control

This document records the accepted design and required source layout. The runtime art is only publicly downloadable **after the above authored files are committed under `examples/fantasy-rpg-hud-wave1/` and CI deploy succeeds**. The installed user's ZIP is not magically published by this documentation.
