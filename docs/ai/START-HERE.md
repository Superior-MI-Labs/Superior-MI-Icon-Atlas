# Visual Atlas — short instruction to creating AI (v1)

**Creator goal:** deliver a self-contained, working Visual Atlas ZIP that opens in [the private builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html). One ZIP may contain multiple manifests, textures, animations, states and compatible presets.

## Mandatory checklist (do in order)

- [ ] **Understand:** For substantial or ambiguous commissions use [Creator preflight](CREATOR-PREFLIGHT.md); it distinguishes confirmed constraints from proposals and explains when approval is genuinely necessary. Do not repeatedly ask for approval after the creator has delegated the decision. Extract what the creator actually wants from this conversation. Internally restate a brief with subject, visual style, target environment, behaviors, exact constraints, package contents and acceptance tests. Honor explicit constraints; do not invent requirements or insist on nonessential questions.
- [ ] **Select:** Open the [recipe index](INDEX.md) and read **only** the relevant recipe(s), plus [format/API guide](FORMAT-API.md) when needed. Use a working example ZIP rather than guessing field names.
- [ ] **Create:** If generating source art, follow [Image-engine workflow](IMAGE-ENGINE-WORKFLOW.md); its output is not proof of real grid/alpha/animation data. Produce real original artwork and the actual manifest(s). Do not hand over placeholders. Individual assets must be measured and laid out on exact pixel rectangles; **never assume a generated image has an exact grid**. A grid guide is a packing destination, not proof of alignment.
- [ ] **Connect:** Include all texture references, sequences and timings, states, layers, optional input/output contracts, compatible slots/presets, names and searchable tags. Supply useful defaults so the builder opens ready to preview.
- [ ] **Preview as an integrator:** Before release, ask **“How will a developer explore this in their own game or app?”** Every configurable asset must expose its meaningful inputs and state choices in the current Builder, with a visible default, readable value and actual visual feedback. For hearts/pips, try 1, 4 and 20 capacity and both a single row and wrapped rows; for bars, scrub the full range; for controls, test on/off, hover/pressed/disabled; for animations, scrub/play frames. If the existing manifest/host cannot express a requested control, disclose the limitation rather than creating decorative fake UI. **Import the final ZIP** and use that exact artifact for preview and test evidence.
- [ ] **Validate:** Run [release checklist](RELEASE-CHECKLIST.md), fix failures, inspect every image crop and animation/preset visually. Create and **run** at least one creator-specific declarative acceptance test (`smi-ai-acceptance/1`) with assertions grounded in the request. Never fabricate a run or claim visual inspection without seeing the images.
- [ ] **Deliver:** One ZIP, a short content summary, and a truthful QA receipt stating PASS / WARN / NOT RUN for each gate. If tools cannot verify a requirement, say so and do not claim a full pass.

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
