# Recipe: GUI controls, HUDs, buttons and interactive visuals

**Start from:** [interactive meter ZIP](../../demo/interactive-hud.zip) and [potion presets](../../demo/potions-collection.zip).

1. Write down what inputs the host application supplies (e.g. `value: 0..100`, `enabled`, `pressed`) and what outputs/events it needs (e.g. `value_changed`, `activate`).
2. Separate appearance from behavior. Use regions and optional nine-slice geometry, compositions for ordered layers, state sets for appearance variants, and typed `behavior` for allowed events/outputs.
3. Define sensible defaults. A health bar should display something immediately; a slider should expose a numeric output, not just a moving graphic.
4. Use compatible slots/presets for alternative fills, skins, equipment or colors. Reference only actual assets and versioned interfaces.
5. Open in builder, exercise each declared control/event/preset and verify visual bounds and returned values. Run [release checklist](../RELEASE-CHECKLIST.md).

Host application owns actual pointer/keyboard/game input. The manifest must not contain executable code.

## Required GUI interaction production pipeline

1. Define intended host interactions, typed inputs, min/max/default values, output units and named states.
2. Identify each visual layer and order explicitly: background, fill, borders, control handle, overlay.
3. Match each region to measured source image rectangles; inspect alpha over transparent and dark backgrounds.
4. Normalize non-unit numeric inputs **for rendering** (e.g. 72 of 100 = 72% width), but preserve source values for outputs.
5. Show visual previews at min, 25%, midpoint, 75%, max and every named state/preset.
6. Verify the fill isn't hidden by an opaque border/frame, the thumb tracks the same numeric input, and text/labels match values.
7. Verify event contracts and accessible host semantics; no executable scripts inside manifests.
8. Add request-specific executable assertions for layer order, input range, clip/position bindings and outputs.
9. Run ZIP validator, strict crop/contact-sheet QA and a **real browser render test** comparing min/mid/max pixels (`python3 tests/browser_hud_pixels.py` when Playwright + Chromium are installed).
10. Export the final ZIP; reopen it and verify behavior, geometry, licensing and dependencies before claiming READY.

Reference test: `examples/acceptance/interactive-hud.json` (request-specific assertions) and `tests/visual-core.cjs` (normalization + layer order regression). These support but do not replace browser visual QA.

For a machine-verifiable preview, extend [visual scenarios](../../../tests/visual-scenarios.json) with input samples and pixel/output assertions. Run `python3 tests/browser_visual_matrix.py --spec tests/visual-scenarios.json --out QA-DIR` after building the site. Include min/mid/max; check changing fill and output value.
