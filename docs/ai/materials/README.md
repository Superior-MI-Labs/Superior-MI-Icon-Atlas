# Recipe: layered materials and environmental effects

**Start from:** [glass + rain ZIP](../../demo/starter-pack.zip).

1. Identify reusable components (glass base, cracks, dirt, weather, shine) and separate static layers from sequences.
2. Give every region its own measured coordinates; animated overlays use referenced sequences rather than copying the base surface into every frame.
3. Compose in a stable order with named states and typed controls (e.g. `damage: intact/hairline/shattered`, `raining: true/false`).
4. Preview every layer combination and loop transition; verify alpha, blend and alignment on the intended background.
5. Run [release checklist](../RELEASE-CHECKLIST.md); do not require unsupported shaders or executable manifest code.

The same approach works for glass, water, smoke, weather, fire, backgrounds, game decals, and website overlays.
