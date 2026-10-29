# Visual Atlas AI authoring library

**Start with [START-HERE.md](START-HERE.md).** It is the only required entrypoint for an assistant. Read only the one recipe matching the creator's request, then the mandatory [release checklist](RELEASE-CHECKLIST.md).

| What you're building | Recipe | Working ZIP |
|---|---|---|
| Static icons and tintable glyphs | [Icons](icons/README.md) | [Single icon](../demo/icons.zip) |
| Multi-frame icons and object/character animations | [Animations](animations/README.md) | [Animated icon](../demo/animated-icons.zip) · [Character states](../demo/character-animations.zip) |
| Buttons, toggles, sliders, progress/health bars | [GUI and interactions](gui/README.md) | [Interactive HUD](../demo/interactive-hud.zip) |
| Multiple manifests, slot compatibility and presets | [Collections](collections/README.md) | [Potion Lab](../demo/potions-collection.zip) |
| Glass, cracks, rain and layered effects | [Materials and layers](materials/README.md) | [Glass/weather demo](../demo/starter-pack.zip) |

**Executable acceptance examples:** [`character.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/character.json) · [`potion.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/potion.json). The checker prints a real PASS/FAIL and never claims human visual inspection.

**Shared reference:** [Manifest/API contract](FORMAT-API.md) · [QA release checklist](RELEASE-CHECKLIST.md) · [Request examples](PROMPT-EXAMPLES.md) · [Grid starters](../templates/authoring-grids.zip).

## Why the directions are separated

The creator describes *what* to make. The assistant loads the short core instructions, then just one relevant recipe and the common release gate. Do not paste all guides into a long prompt. Other recipes are available if the deliverable actually combines those features. The assistant should not override the user's actual request with a template's demo aesthetics.

## About examples

The ZIPs are real, downloadable, manifest-driven test fixtures and can be opened privately in the builder. Their artwork is deliberately simple; **reuse the contracts, not necessarily the visuals**. The builder accepts a ZIP containing many manifests and texture sheets. An AI should include complete assets, dependencies, and truthful licensing metadata.
