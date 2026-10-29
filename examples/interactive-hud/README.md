# interactive-hud — geometry-only starter template

Original CC0 geometric test artwork. Replace the artwork before commercial branding.
Edit manifest.json and textures/atlas.png, then run the ZIP QA. This source directory is zipped by tools/build_site.py.

## Visual response regression

The correct layer order is frame → green fill → thumb. Input `value` is native 0..100; rendering normalizes to 0..1 before clipping or thumb motion. Do not put the opaque frame above the fill.

Run `node tests/visual-core.cjs` for numeric normalization and layer contract. Use `examples/acceptance/interactive-hud.json` with `tools/ai_acceptance.py` for structured checks. Real browser QA must show increasing filled area at 0, 50 and 100, and a moving thumb.
