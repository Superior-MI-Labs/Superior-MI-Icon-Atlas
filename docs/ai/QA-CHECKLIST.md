# Visual quality and release checklist

The structural validator **cannot** tell whether a visual represents its name or whether a chopped-off fragment is an icon. An AI-generated picture may have uneven rows and inconsistent spacing, even when the intended layout is “24 × 8”.

## Before packing

1. Decide the logical size, padding, scale, alignment and style. Draw/export isolated assets or measure actual object bounds. Never derive crop rectangles solely from an AI-generated grid's claimed row/column count.
2. Verify each source image visually and measure the icon/sprite's true occupied pixel bounding box. When re-packing, place each verified image on a clean canvas with explicit coordinates; do not cut across adjacent objects.
3. Define each region with exact pixels `[x,y,w,h]`. Check source and target resolutions, alpha, trimming, anchors and any UI nine-slice margins.
4. For every sequence, check **each frame** for alignment, correct order, intended contents and sensible timing. Preview the first, middle and final frame; also inspect transitions and looping. For state sets, slots and presets, preview each selectable option.

## Before handing over

Run `python3 tools/qualify_asset_zip.py COLLECTION.zip --out qa/collection` with Pillow and jsonschema installed. It runs structural validation, examines every region's real pixels and creates labeled contact sheets and a machine report. Investigate all findings. Use `--strict` when every region is supposed to be an isolated padded sprite (full-bleed images are legitimate but cannot pass that policy).

Create one or more acceptance checks tailored to the creator's request (e.g. every required character state exists and the named animation actually uses distinct correct frames; every slider preset returns the expected value). Run them, not just the generic validator.

Manually/visually inspect **every** region in the generated contact sheets. Check for cut-off symbols, unrelated fragments, duplicate/wrongly labeled art, unexpected background pixels, and inconsistent line weights. View composites, every preset/slot option, and representative animation times in the live builder. Re-run after fixes.

Do not state “all icons visually passed” unless all were actually examined. Automated checks can prove only the tested constraints. Do not fabricate an image inspection, browser test, run log, or test success.

## Required user-facing QA receipt

```text
VISUAL ATLAS HANDOFF
Archive: <name>.zip
Assets / regions / animations: <actual counts>
Manifest and dependency validation: PASS / FAIL / NOT RUN
Pixel boundary and empty-region scan: PASS / WARN / FAIL / NOT RUN
Contact sheets: <number> generated; <number> visually reviewed
Animation, presets and state preview: PASS / PARTIAL / NOT RUN
Creator-specific acceptance test: PASS / FAIL / NOT RUN
Remaining warnings: <real list or none>
Delivery status: READY FOR PREVIEW / NEEDS FIXES
```

**Release gate:** Do not claim ready-for-preview if structural validation fails, an expected region is empty, or source paths are missing. Warnings need review; `READY FOR PREVIEW` is not proof of commercial rights or artistic quality.
