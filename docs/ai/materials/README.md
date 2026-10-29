# Recipe: layered materials and environmental effects

**Start from:** [glass + rain ZIP](../../demo/starter-pack.zip).

1. Identify reusable components (glass base, cracks, dirt, weather, shine) and separate static layers from sequences.
2. Give every region its own measured coordinates; animated overlays use referenced sequences rather than copying the base surface into every frame.
3. Compose in a stable order with named states and typed controls (e.g. `damage: intact/hairline/shattered`, `raining: true/false`).
4. Preview every layer combination and loop transition; verify alpha, blend and alignment on the intended background.
5. Run [release checklist](../RELEASE-CHECKLIST.md); do not require unsupported shaders or executable manifest code.

The same approach works for glass, water, smoke, weather, fire, backgrounds, game decals, and website overlays.


## Required layered material / effects pipeline

1. Identify base, masks, overlays, optional animations and independent states (wet, cracked, dirty, broken).
2. Verify resolution, alpha mode, mask alignment and blend modes for every layer.
3. Render every exposed state combination with layers on/off; confirm actual visual differences.
4. Inspect each source region and transitions/loops (including the seam) at intended scale.
5. Validate references, no unintended occlusion, frame timing and compatibility contracts.
6. Export, reimport and compare fixed-state preview pixels; record QA evidence.
