# Required acceptance checklist — run before handing over a ZIP

Do not label an asset ready merely because its JSON parses. Structural validation, image inspection, actual behavior, and request-specific acceptance are separate gates.

## 1. Creator brief and coverage

For substantial commissions, use [creator preflight](CREATOR-PREFLIGHT.md) before expensive production; image generation follows [source-art workflow](IMAGE-ENGINE-WORKFLOW.md) when relevant. Do not invent acceptance or approval.
- [ ] All assets the creator requested are included; unexpected simplifications are disclosed.
- [ ] Names, tags, style, animation/state names, defaults, licensing and rights claims are accurate.
- [ ] A compact request-specific acceptance test exists (examples: "Mana preset selects three animated frames", "walk and idle state changes remain aligned", "slider outputs value 12 when set to 12").

## 2. Textures and exact geometry
- [ ] Source art was inspected; each object is complete and properly positioned. A generated grid's implied layout was **not** blindly trusted.
- [ ] Texture dimensions, region rectangles, transparency and per-cell spacing were measured against actual pixels; none cuts into a neighbor.
- [ ] New raster textures have a documented size check against lossless optimization, including before/after bytes and exact decoded-pixel comparison when changed. A candidate is accepted only if smaller without changing pixels, geometry or required PNG encoding, and final file checksums match the authored manifests. Preserve source-image provenance metadata; use no lossy or downscaled substitute without explicit approval. Already-optimized files do not need repeated recompression.
- [ ] A contact sheet was created and **every asset region** was visually reviewed, not just the first image.
- [ ] Full-bleed artwork was identified as intentional; edge-contact warnings were investigated, not automatically ignored.

## 3. Manifest and behavior
- [ ] All images are packaged and paths resolve locally with no external dependencies.
- [ ] All asset references, ordering, animation FPS/frame durations, state maps, events, inputs/outputs and presets are valid.
- [ ] Every animation, state and compatible option is previewed; visually check frame 1, middle, end, loop boundary and independent overlays.
- [ ] For **every input-controlled visual**, render **0%, 1%, 5%, 10%, 25%, 50%, 75%, 90%, 99%, 100%** over the declared range (plus request-specific states); compare actual pixels, not only output labels. A low nonzero value cannot disappear behind a badge or mask. These samples include the minimum, midpoint, maximum; test those three for every non-percent input range as well.
- [ ] Numeric values with non-unit ranges (e.g. 0..100) are normalized correctly for clipping and positioning, while output values preserve their declared units.
- [ ] For globe, vial, battery and other bounded fill meters, the `clip` source is tightly measured to the actual **visible interior**, with no invisible transparent gutter consuming 1–10% or 90–100%. Verify all ten required values on the **assembled output**; correct source geometry before modifying renderer logic.
- [ ] For discrete radial, pip and fractional-heart `state_set` variants, inspect **every named state** and assert neighboring states render different actual pixels. Do not advertise a continuous numeric radial input unless the manifest and shared renderer genuinely implement it.
- [ ] Layer order, alpha, masks and clipping are checked against real preview: opaque frames or decorative badges cannot hide a required fill or animated layer.
- [ ] Sliders and bars use one measured usable interval: 100% reaches its actual endpoint, 50% visually reads as half, the thumb center and active trail share endpoints, the thumb stays in bounds, and a mismatched SVG viewBox cannot letterbox the artwork. See [value-geometry gate](gui/VALUE-GEOMETRY.md).
- [ ] Adaptive heart, pip, gem, leaf or armor layouts test 1, 4 and 20 maximum items, one/two/multiple rows, current value 0/full/partial and columns less than/equal to maximum. Verify the live numeric slider matches the visible value and clamps when maximum capacity decreases; preserve independently addressable state assets.
- [ ] Discrete state sets are navigable via a synchronized dropdown **and** draggable step slider in both builder and public preview. A state selector must never be mistaken for a continuous numeric fill control.
- [ ] Decorative rim highlights, top-frame seams, badges, runes and studs must not cross one another in the assembled rendering. Review assembled compositions at 100% native pixels, not only per-region contact sheets. A rim stroke that cuts through ornamental detail is a visual failure even if geometry and JSON pass.
- [ ] Frame-boundary and animation loop tests cover anchor/pivot continuity; do not claim approval from sprite-sheet geometry alone.
- [ ] Opening the ZIP automatically previews the intended default asset, without hand-configuring layers.

## 3a. Developer usability and preview acceptance

- [ ] For every publicly addressable **interactive composition**, the preview demonstrates every meaningful input, state or compatibility choice actually used by a host game/application. A visually changing screenshot alone is insufficient; it must be controlled by an explicit manifest input or state.
- [ ] On first import of the **final ZIP**, the selected entry asset is a useful assembled widget rather than a raw cropped component, with a visible and legible default.
- [ ] Vary numeric controls at endpoints and intermediate values using real sliders; for repeatable counters independently vary maximum capacity, fill count and wrap columns. Test at least 1, 4 and 20 indicators and 10-column wrap when the declared range permits.
- [ ] For state sets, preview each state using both dropdown and synchronized step slider; for a composition, inspect its own bound state/value inputs. A state-only artwork must never be mislabeled as a continuous 0–100% meter.
- [ ] Document game-engine integration boundaries: pixels and state/behavior declarations are portable; host handles pointer hit-testing, keyboard/gamepad mapping, input signals, layout in the destination engine, and font rendering unless explicitly implemented.
- [ ] Preserve the same previewable behavior and dimensions after export/import of the **exact delivered ZIP**, and save evidence. Block publication when a named interactive asset lacks a working preview control or silently hides a demanded value.

## 4. Executed QA and packaging
- [ ] Run `python3 tools/validate_visual_pack.py OUTPUT.zip` and fix any errors.
- [ ] Run `python3 tools/qualify_asset_zip.py OUTPUT.zip --out QA-DIR` and inspect `contact-*.png` and the receipt.
- [ ] Write an acceptance JSON with assertions derived from the creator request; execute `python3 tools/ai_acceptance.py OUTPUT.zip --acceptance MY-ACCEPTANCE.json --out QA-DIR` and inspect its output. [Robot](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/character.json) and [potion](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/potion.json) are examples. Never print PASS for unexecuted tests.
- [ ] Run **rendered-state QA** against the final ZIP using [the visual scenario format](../../tests/visual-scenarios.json) and shared Chromium runner. Cover min/mid/max, distinct states, overlays and loop frames where relevant, and assert actual pixel changes rather than just a valid manifest. See [visual QA guide](VISUAL-RENDER-QA.md).
- [ ] Include the browser screenshots and test report. If browser testing cannot run, report **NOT RUN**, never PASS.
- [ ] Re-import the final ZIP into the builder and check preset/state behavior and **actual visual response**, then export/reimport and compare at least one fixed-time preview.
- [ ] Hand off the ZIP, a brief contents description and a truthful QA receipt.

## QA receipt to include in the final answer

```text
VISUAL ATLAS HANDOFF
Archive: <filename>.zip
Collections / manifests / assets / textures: <actual counts>
Manifest & dependency checks: PASS | FAIL | NOT RUN
Pixel / crop scan: PASS | WARN | FAIL | NOT RUN
Contact sheet review: <reviewed count>/<total regions>
Animation, states & preset previews: PASS | PARTIAL | NOT RUN
Creator-specific acceptance test: PASS | FAIL | NOT RUN
Remaining warnings: <facts or none>
Delivery: READY FOR PREVIEW | NEEDS FIXES
```

**Rules:** Unrun checks say NOT RUN. Structural PASS does **not** mean artistic or rights clearance. A missing texture, empty required region, invalid dependency or impossible coordinate must block READY FOR PREVIEW. Keep detailed QA evidence separate from the creator-facing one-page result.
