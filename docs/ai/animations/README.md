# Recipe: animated icons, characters, objects and effects

**Start from:** [three-frame pulse icon](../../demo/animated-icons.zip) or [robot idle/walk states](../../demo/character-animations.zip). For layered animation, see [glass/weather](../../demo/starter-pack.zip).

1. Identify the target object's states and animations. This is **not limited to characters**: water, indicators, buttons, equipment and banners use the same format.
2. Produce complete frames with consistent logical size and pivot. Inspect the sheet and isolate every frame before packing; no guessed grid boundaries.
3. Define each frame as a `region`, each ordered animation as a `sequence` with default FPS/optional frame durations/playback, and alternative named animations as a `state_set`.
4. For overlays and movement, use a `composition` with layers, optional timeline tracks and typed controls. Avoid frame-by-frame duplication of an entire background where a reusable overlay suffices.
5. Test state transitions, first/middle/last frame, loop boundary and any alternate animation speed. Run [release checklist](../RELEASE-CHECKLIST.md).

Contract source: [`examples/character-animations/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/character-animations/manifest.json).
