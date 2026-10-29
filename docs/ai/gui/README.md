# Recipe: GUI controls, HUDs, buttons and interactive visuals

**Start from:** [interactive meter ZIP](../../demo/interactive-hud.zip) and [potion presets](../../demo/potions-collection.zip).

1. Write down what inputs the host application supplies (e.g. `value: 0..100`, `enabled`, `pressed`) and what outputs/events it needs (e.g. `value_changed`, `activate`).
2. Separate appearance from behavior. Use regions and optional nine-slice geometry, compositions for ordered layers, state sets for appearance variants, and typed `behavior` for allowed events/outputs.
3. Define sensible defaults. A health bar should display something immediately; a slider should expose a numeric output, not just a moving graphic.
4. Use compatible slots/presets for alternative fills, skins, equipment or colors. Reference only actual assets and versioned interfaces.
5. Open in builder, exercise each declared control/event/preset and verify visual bounds and returned values. Run [release checklist](../RELEASE-CHECKLIST.md).

Host application owns actual pointer/keyboard/game input. The manifest must not contain executable code.
