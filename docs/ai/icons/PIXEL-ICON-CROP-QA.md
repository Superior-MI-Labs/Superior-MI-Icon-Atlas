# Pixel-game icon crop, alignment and Builder release gate

**Required companion to:** [GAME-PIXEL-ART.md](GAME-PIXEL-ART.md), [the icon recipe](README.md), [the GUI interaction recipe](../gui/README.md), and [the release checklist](../RELEASE-CHECKLIST.md).

## Why this gate exists (Wave 1 regression, November 2026)

A generated **promotional concept board** was mistakenly treated as a source atlas. Extraction used hard-coded foreground truncation (`binary[:, 158:] = 0`, an extra 51-pixel cutoff for the spellbook), deleting parts of the art *before* the 128×128 rectangles were packed. The manifest rectangles were numerically correct for a sheet, but the **pixels inside** those rectangles were permanently clipped. Removing the hard limits without isolating background chrome also introduced stray gold corner/line fragments. The prior local `verify_pack.py` reported PASS while testing no actual compositional or state-set references because those checks were incorrectly unreachable after `continue`.

This is an **artwork extraction and release qualification failure**, not a justification for compensatory CSS transforms, per-icon manifest nudges, or another renderer. **Correct source/extraction first**, regenerate the packed PNG, update the manifest texture hash, then verify final UI output. Manifest rectangle changes alone cannot recover missing silhouettes.

## Production authoring rule

1. **Require a source-art fidelity check before packing.** The preferred source is an isolated, transparent, final-quality raster item. If images are a flat presentation board, treat the extraction as a *candidate* requiring every silhouette's recovery and background decontamination. No frame, title, checkerboard or neighboring art belongs in item pixels.
2. **Never blindly crop the foreground with magic constants.** Only bounds measured from the actual alpha silhouette may drive fitting. A source-specific calibration/exclusion may remove *known frame chrome* if independently verified, but it must never erase subject geometry. Do not assume generated grid rows/columns are exact.
3. **Keep logical geometry stable.** For a 128px icon, measured alpha should fit within the intended 128×128 canvas with a visible transparent gutter. The manifest owns the exact region `rect_px`, `logical_size_px`, texture path and SHA-256. Keep IDs immutable across repacking. Render positions are not fixed by runtime CSS offsets.
4. **Review the full gallery, not one example.** Generate labeled 1× contact sheets showing each 128px region over both a checkerboard and contrasting backgrounds, with the actual alpha bounding box and full cell rectangle. Inspect every single region for clipping, crooked alignment, stray border pixels, unexpected mattes, partial components and optical scale. A bounds check alone cannot prove semantic completeness.
5. **Review every composition in the real Builder.** Import **the final ZIP** into the existing Visual Atlas Builder, view each icon, switch compatible slots, exercise hover/pressed/selected/disabled, cooldown endpoints and combined states, and capture actual browser screenshots from the application's shared renderer. The host controls real pointer/keyboard events. Compare the Builder view to the decoded PNG contact; an independent QA page is useful diagnostic evidence but **not a substitute** for the real Builder.
6. **Treat change as invalidating approval.** Modifying crop logic, source art, textures or relevant manifest geometry after review requires regenerated hashes, rerendered screenshots, reimport, and renewed per-icon inspection. Avoid updating golden pixel baselines automatically in the same operation that changes pixels.
7. **Run the actual repo tests** (`RUN-ALL.sh`, `tools/validate_visual_pack.py`, `tools/qualify_asset_zip.py`, `tools/ai_acceptance.py`, `tests/browser_visual_matrix.py` with a request-specific scenario) and verify ZIP export/reimport. Any test that cannot run must be recorded `NOT RUN`, never converted to PASS.
8. **Publish only after quality and rights approval.** Passing alpha, geometry and static Canvas tests means ready for **live Builder review** at most. No publication allowance until creator-approved art, source/rights review and official Builder tests all pass.

## Mandatory release evidence

- `manifest.json`, `collection.json`, actual packed textures, and source-art provenance.
- `qa/all-32-bounds-contact.png` or equivalent **every-icon** contact at native resolution, including alpha boxes and cell boundaries.
- `qa/alignment-audit.json` with alpha bbox, gutter and centroid for every icon; flag outliers rather than silently translating them.
- Real browser-rendered evidence for all required states and combination cases. Source-reference pixel parity should be tested for all asset IDs, not a handful.
- A negative crop test that deliberately shifts an atlas rectangle or deletes 20+ px of subject art and is required to **fail**. This prevents another false PASS for geometry-only checks.
- Truthful receipt: `manifest/refs`, `crop/geometry`, `pixel baseline`, `independent Chromium`, `official Builder`, `export/reimport`, `semantic/rights approval` each PASS/FAIL/NOT RUN, no ambiguous overall PASS.

## Diagnostic lesson: geometry vs content

The source image can contain a severed sword even when its atlas `rect_px` is `[0, 0, 128, 128]` and its visible alpha is perfectly centered. Thus **manifest geometry, source silhouette, and assembled UI rendering require separate QA stages**. A "repack all" command must not be trusted as creative validation. Never claim the Builder was inspected if only a standalone preview was run.

## Standalone Wave 1–2 candidate handoff

The accompanying 32-icon candidate includes `build_pack.py`, `verify_pack.py`, `qa/generate_contact.py`, `qa/browser_qa.py`, and a manually inspected Chromium gallery. This verifies the **authored** atlas and offline Canvas behavior. It is not a patch to replace the production renderer. The actual Builder gate remains pending until the ZIP is imported in that project environment.
