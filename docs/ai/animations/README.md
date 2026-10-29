# Recipe: animated icons, characters, objects and effects

**Start from:** [three-frame pulse icon](../../demo/animated-icons.zip) or [robot idle/walk states](../../demo/character-animations.zip). For layered animation, see [glass/weather](../../demo/starter-pack.zip).

1. Identify the target object's states and animations. This is **not limited to characters**: water, indicators, buttons, equipment and banners use the same format.
2. Produce complete frames with consistent logical size and pivot. Inspect the sheet and isolate every frame before packing; no guessed grid boundaries.
3. Define each frame as a `region`, each ordered animation as a `sequence` with default FPS/optional frame durations/playback, and alternative named animations as a `state_set`.
4. For overlays and movement, use a `composition` with layers, optional timeline tracks and typed controls. Avoid frame-by-frame duplication of an entire background where a reusable overlay suffices.
5. Test state transitions, first/middle/last frame, loop boundary and any alternate animation speed. Run [release checklist](../RELEASE-CHECKLIST.md).

Contract source: [`examples/character-animations/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/character-animations/manifest.json).

## Character / directional animation production pipeline

1. Confirm creator brief, reference identity, states, directions, art style and deliverable.
2. Inspect existing Visual Atlas animation recipes, manifest, tests; reuse contracts.
3. Fix consistent camera, scale, canvas, alpha, palette, baseline and ground pivot.
4. Produce canonical direction poses; inspect identity, anatomy, apparel and silhouettes **before** creating action frames.
5. Draw actual key poses (breathing, blinking, foot articulation, shifts in weight); do not fake action by globally warping one sprite.
6. Draw/investigate in-betweens; allow action-dependent frame counts and timing.
7. Inspect **every** frame: crop, alpha, identity, outline and details.
8. Compare **every adjacent** pair and last-to-first seam for anchors, contact and velocity jumps.
9. Play **all sequences** at native game scale and target FPS, including transition states; revise defects.
10. Pack vetted isolated frames into measured rectangles, preserving stable asset IDs and pivots.
11. Run official archive validation, strict pixel QA and a creator-specific executable acceptance test.
12. Import the **final** ZIP into the builder, exercise every direction/state and export/reimport.
13. Preserve contact sheets, full motion previews and failure/correction evidence.
14. Verify provenance, licensing, texture dependencies and ZIP integrity.
15. Release only with passing gates; else mark **NEEDS FIXES** and repeat affected validation.

The shared [browser visual matrix](../../../tests/visual-scenarios.json) captures real icon/character frames, state changes and exact loop repeats. Add cases for all requested states and motion; inspect adjacent-frame and seam quality visually as well as with automated differences.
