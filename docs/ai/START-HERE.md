# Visual Atlas — AI authoring entrypoint (v1)

**Goal:** turn the creator's actual request into original artwork and a self-contained ZIP that opens in the [private Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html). Do not invent assets, tool capabilities, approvals or test results.

## Workflow (in order)

- [ ] **Understand.** Reconstruct the intent, style, constraints, target and acceptance checks. For substantial or ambiguous work use [Creator preflight](CREATOR-PREFLIGHT.md). Ask only material blocking questions; respect delegated decisions.
- [ ] **Route.** Choose the relevant [recipe](INDEX.md) and [manifest contract](FORMAT-API.md). Use existing capabilities and examples, not a competing renderer or invented keys.
- [ ] **Create.** Give the image engine only a short, positive [visual brief](IMAGE-ENGINE-WORKFLOW.md), using a clean context where supported. For multi-asset/frame sheets, attach a suitable [transparent layout grid](TEMPLATES.md) when supported. Qualify a representative slice, then batch artwork and deterministic processing. Inspect real pixels; repack measured regions, preserve alpha, alignment and stable IDs.
- [ ] **Connect.** Package local textures and dependencies; use layers, states, slots, presets and inputs as applicable. Provide meaningful defaults, names, tags, subjects and [browse classification](BROWSE-TAXONOMY.md). Keep game logic and unsupported behaviors host-owned.
- [ ] **Qualify.** Follow the [release checklist](RELEASE-CHECKLIST.md) and applicable recipe. Inspect every region, exercise declared inputs and states, run creator-specific acceptance and applicable [browser scenarios](VISUAL-RENDER-QA.md) on the exact delivered ZIP. Review artistic fidelity separately.
- [ ] **Deliver.** Return the ZIP, previews, and evidence-backed receipt with PASS / FAIL / WARN / NOT RUN. Do not turn an incomplete or inaccessible gate into a PASS.

## Choose the available execution path

- **Conversation-only:** inspect references and guide; produce only files the available tools can really create. If unable to generate a valid archive, provide a useful brief or handoff instead. Never claim it is a working pack.
- **File/code tools:** generate and inspect real assets. Obtain the [repository checkout](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/archive/refs/heads/main.zip) when possible; run the command below. If tools or Chromium are unavailable, report NOT RUN and give the exact missing step. A private Builder import is useful for manual preview, not a substitute for automated qualification.
- **Repository-connected:** preserve source ownership, stage exact PNG/manifest files, use official CI, and publish only with rights and release authorization. Report CI, manual review and deployment separately. Never infer successful deployment from a commit.

## Qualify a candidate

From the repository root, with Python dependencies from `requirements-test.txt`:

```bash
python3 tools/ai_acceptance.py YOUR-PACK.zip --acceptance YOUR-ACCEPTANCE.json --out qa/your-pack
```

This already invokes the archive validator and crop scan. For actual browser qualification, install Playwright/Chromium and add `--visual-spec YOUR-VISUAL-SCENARIOS.json`. Exact ZIP QA uses authored Builder files; no full site build needed. See [browser QA](VISUAL-RENDER-QA.md). `bash RUN-ALL.sh` is the separate full repository gate.

Do not load all recipes into context. Use the [release checklist](RELEASE-CHECKLIST.md) as the shared authority; the schema and implemented runtime define supported features.
