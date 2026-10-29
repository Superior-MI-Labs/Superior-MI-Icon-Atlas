# Visual Atlas — short instruction to creating AI (v1)

**Creator goal:** deliver a self-contained, working Visual Atlas ZIP that opens in [the private builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html). One ZIP may contain multiple manifests, textures, animations, states and compatible presets.

## Mandatory checklist (do in order)

- [ ] **Reconstruct the request (4D).** Infer intent from the current conversation **and relevant, accessible** references, repositories, attached files and prior project decisions. Keep the original request and create a faithful AI-fluent working brief. Treat that reconstruction as the operative instruction **without replacing explicit user constraints**. Mark confirmed facts, inferred preferences, proposed improvements and unknowns separately. Follow [creator preflight](CREATOR-PREFLIGHT.md).
- [ ] **Research compatibility.** Inspect the creator's actual game/app requirements when available: sprite perspective, dimensions, rig/clothing layers, state names, anchor, renderer/import format and relevant templates. Reuse the [task recipe index](INDEX.md) and [format contract](FORMAT-API.md); don't invent a new manifest or pretend inaccessible project context was read.
- [ ] **Plan and secure approval.** Improve an underspecified brief with sensible *proposed* enhancements, not secret scope additions. Ask only essential unanswered architecture-changing questions; offer defaults for the rest. For multi-asset work, present the proposed production blueprint, alternative approaches, an acceptance plan and a **small qualification sample**; ask approval **before costly generation**. A previously approved plan plus explicit instruction to continue does not require repetitive confirmation.
- [ ] **Create qualified sources.** Use [image-engine workflow](IMAGE-ENGINE-WORKFLOW.md) when relevant. Make real original artwork and authored manifests; never treat a generated image's displayed grid as exact production cells. Inspect and measure isolated image pixels, alpha and anchors before deterministic packing.
- [ ] **Connect existing contracts.** Include ordered frames/timing, names, states, textures, layer/preset references and defaults in the actual supported builder format. Do not add a second source of truth.
- [ ] **Verify and iterate before release.** Run [release checklist](RELEASE-CHECKLIST.md), creator-specific executable acceptance tests, complete crop/frame visual review, and rendered-state QA for animation/layers/controls. A green JSON check is not approval of artistic quality. On failures, fix art or geometry and rerun; do not hand off a deferred-polish ZIP.
- [ ] **Deliver truthfully.** One final self-contained ZIP only after mandatory gates pass, plus reproducible evidence and honest PASS/WARN/NOT RUN receipt. If not ready, send a concise blocker report, not a falsely labeled final asset.

**Local commands** from a Visual Atlas checkout:

```bash
bash RUN-ALL.sh
python3 tools/qualify_asset_zip.py YOUR-PACK.zip --out qa/your-pack
python3 tools/validate_visual_pack.py YOUR-PACK.zip
python3 tools/ai_acceptance.py YOUR-PACK.zip --acceptance YOUR-ACCEPTANCE.json --out qa/acceptance
```

**Resources:** [Examples by task](INDEX.md) · [Manifest contract](FORMAT-API.md) · [Final checklist](RELEASE-CHECKLIST.md). Keep the creator's actual request primary. Do not consume context reading irrelevant recipes.

**Interactive asset release gate:** verify actual visible state changes (e.g. 0/50/100) and not only output text; see the GUI recipe and acceptance example.

Before delivery, also run the [rendered-state QA guide](VISUAL-RENDER-QA.md) if your asset has animation, layers, states or user-controlled appearance. If Chromium cannot render, disclose NOT RUN; structural checks cannot replace it.
