# Required acceptance checklist — run before handing over a ZIP

Do not label an asset ready merely because its JSON parses. Structural validation, image inspection, actual behavior, and request-specific acceptance are separate gates.

## 1. Creator brief and coverage
- [ ] All assets the creator requested are included; unexpected simplifications are disclosed.
- [ ] Names, tags, style, animation/state names, defaults, licensing and rights claims are accurate.
- [ ] A compact request-specific acceptance test exists (examples: "Mana preset selects three animated frames", "walk and idle state changes remain aligned", "slider outputs value 12 when set to 12").

## 2. Textures and exact geometry
- [ ] Source art was inspected; each object is complete and properly positioned. A generated grid's implied layout was **not** blindly trusted.
- [ ] Texture dimensions, region rectangles, transparency and per-cell spacing were measured against actual pixels; none cuts into a neighbor.
- [ ] A contact sheet was created and **every asset region** was visually reviewed, not just the first image.
- [ ] Full-bleed artwork was identified as intentional; edge-contact warnings were investigated, not automatically ignored.

## 3. Manifest and behavior
- [ ] All images are packaged and paths resolve locally with no external dependencies.
- [ ] All asset references, ordering, animation FPS/frame durations, state maps, events, inputs/outputs and presets are valid.
- [ ] Every animation, state and compatible option is previewed; visually check frame 1, middle, end, loop boundary and independent overlays.
- [ ] Opening the ZIP automatically previews the intended default asset, without hand-configuring layers.

## 4. Executed QA and packaging
- [ ] Run `python3 tools/validate_visual_pack.py OUTPUT.zip` and fix any errors.
- [ ] Run `python3 tools/qualify_asset_zip.py OUTPUT.zip --out QA-DIR` and inspect `contact-*.png` and the receipt.
- [ ] Write an acceptance JSON with assertions derived from the creator request; execute `python3 tools/ai_acceptance.py OUTPUT.zip --acceptance MY-ACCEPTANCE.json --out QA-DIR` and inspect its output. [Robot](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/character.json) and [potion](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/potion.json) are examples. Never print PASS for unexecuted tests.
- [ ] Re-import the final ZIP into the builder and check preset/state behavior, then optionally export/reimport once more.
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
