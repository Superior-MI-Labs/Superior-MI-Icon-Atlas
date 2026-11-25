# Visual Atlas AI authoring library

**Start with [START-HERE.md](START-HERE.md).** It is the shared entrypoint for an assistant. Read only the recipe(s) matching the creator's request, then the mandatory [release checklist](RELEASE-CHECKLIST.md).

| What you're building | Recipe | Contract example |
|---|---|---|
| Static icons and tintable glyphs | [Icons](icons/README.md) | [Single icon](../demo/icons.zip) |
| Multi-frame icons and object/character animations | [Animations](animations/README.md) | [Animated icon](../demo/animated-icons.zip) · [Character states](../demo/character-animations.zip) |
| Buttons, toggles, sliders, progress/health bars | [GUI and interactions](gui/README.md) | [Interactive HUD](../demo/interactive-hud.zip) |
| Multiple manifests, slot compatibility and presets | [Collections](collections/README.md) | [Potion Lab](../demo/potions-collection.zip) |
| Glass, cracks, rain and layered effects | [Materials and layers](materials/README.md) | [Glass/weather demo](../demo/starter-pack.zip) |
| World and environment artwork, directional sprites, interactive objects | [World assets](world/README.md) | [Composition and slot examples](collections/README.md) |

**Executable acceptance examples:** [Interactive HUD](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/interactive-hud.json) · [`character.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/character.json) · [`potion.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/acceptance/potion.json). The checker prints a real PASS/FAIL and never claims human visual inspection.

**Shared authoring:** [Creator preflight](CREATOR-PREFLIGHT.md) · [Image source workflow](IMAGE-ENGINE-WORKFLOW.md) (when relevant).

**GIF inspection and animation import:** [Review before converting GIFs to canonical texture sheets](animations/GIF-TO-ATLAS.md). Inspect first; packaging requires explicit human approval.

**Side-scrolling character production:** [Canonical references, action families, animation transitions and first motion qualification](animations/SIDE-SCROLLER-PRODUCTION.md) (only for applicable requests; project-specific history is linked within that guide).

**Independent AI evaluation:** [Benchmark protocol](BENCHMARK.md) (only for evaluating the workflow).

**Shared reference:** [Manifest/API contract](FORMAT-API.md) · [QA release checklist](RELEASE-CHECKLIST.md) · [Request examples](PROMPT-EXAMPLES.md) · [Grid references and packing templates](TEMPLATES.md).

## Why the directions are separated

The creator describes *what* to make. The assistant loads the short core instructions, then just one relevant recipe and the common release gate. The guides govern the production agent. For image generation, delegate just the relevant positive visual brief through the [image workflow](IMAGE-ENGINE-WORKFLOW.md). Load engineering references when needed for packing or qualification. Other recipes are available if the deliverable combines those features. The assistant should not override the user's actual request with a template's demo aesthetics.

## About examples

Internal fixture links may lead to source folders on the hosted site. Use a checkout to build those ZIPs. For direct importable examples, use [Fantasy RPG HUD](../demo/fantasy-rpg-hud-wave1.zip), [Royal Forge complete HUD](../demo/royal-forge-complete.zip), and [Minimal White Tech](../demo/minimal-white-tech.zip). Internal fixture artwork is deliberately simple; **reuse the contracts, not necessarily the visuals**. The builder accepts a ZIP containing many manifests and texture sheets. An AI should include complete assets, dependencies, and truthful licensing metadata.

**HD fantasy game item icons and interaction states:** [Pixel-art item production contract](icons/GAME-PIXEL-ART.md). This requires raster source art, true measured transparent crops, a shared effect composition and publication QA, not procedural vector substitutes.

For Hex World, use the host role specification linked from the world assets recipe for assignments and physical scale; follow the existing Atlas packaging, licensing and visual acceptance gates. The fixture is an integration example, not an approved art master. Keep agent packs separate and do not invent new Atlas schema fields.
