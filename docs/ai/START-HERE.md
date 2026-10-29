# Visual Atlas: AI handoff (v1)

**User workflow:** Describe the asset → AI delivers a self-contained ZIP → drag it into [Visual Atlas Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html). The site does not publish private imports.

## Instructions for the creating AI

1. **Understand the request first.** Extract the creator's actual goal, previous context, constraints, format, target platform, and desired behavior. Rewrite it internally as a concise specification (goal, assets, constraints, deliverable, acceptance tests). Treat this faithful restatement as your working brief; do not erase explicit requirements or invent facts. Clarify only genuinely blocking ambiguity.
2. **Reuse rather than improvise.** Start from a [working example ZIP](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/demo/potions-collection.zip) and consult the [format schemas](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/schemas/smi-visual-pack-v1.schema.json). An optional [collection index](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/schemas/smi-visual-collection-v1.schema.json) connects multiple manifests. Use real original textures, stable IDs, local image paths, correct asset/frame/layer/slot references, named animations, defaults, and truthful license metadata.
3. **Make complete artwork.** Generate or draw individual assets and inspect their actual boundaries **before** packing. A picture that looks like a grid is not a proven grid. Place vetted objects into an exact grid or use explicit pixel rectangles. Keep spacing and pivots consistent. [Authoring grids](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/templates/authoring-grids.zip) are layout guides, not automatic crop coordinates.
4. **Prove the ZIP works.** Write and run at least one **request-specific acceptance test** (for example: a Mana preset really animates and keeps the bottle aligned). Run the validator and [visual QA](QA-CHECKLIST.md). Inspect **every** asset's contact-sheet crop and all animation/preset states, correcting errors. No invented test output. If tools prevent a check, disclose it.
5. **Deliver one ZIP and a short QA summary.** Include what it contains, which tests actually ran, any warnings and remaining limitations. A passing automated test means structurally ready for Visual Atlas preview, not automatically artistically approved.

**Local QA command** (from a checkout of the Visual Atlas repository):

```bash
bash RUN-ALL.sh
python3 tools/qualify_asset_zip.py my-collection.zip --out qa/my-collection
```

**Target:** Assets load and animate automatically from their manifests, with optional compatible slot choices and presets. The creator should not need to configure frames or layers manually.

Further reading: [Visual QA checklist](QA-CHECKLIST.md) · [Compact request examples](PROMPT-EXAMPLES.md) · [Template recipes](TEMPLATES.md).
