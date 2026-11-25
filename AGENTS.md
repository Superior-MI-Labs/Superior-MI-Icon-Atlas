# Visual Atlas agent entrypoint

**Creator-first:** Preserve the user's actual goals, context and constraints. Translate them into a concise internal brief and a request-specific acceptance test. Do not substitute a generic demo for the requested artwork.

1. Read [docs/ai/START-HERE.md](docs/ai/START-HERE.md) (short checklist). For substantial/ambiguous work consult its linked creator preflight and image-source workflow rather than improvising a second process.
2. Choose **only the relevant** recipe from [docs/ai/INDEX.md](docs/ai/INDEX.md). Read [docs/ai/FORMAT-API.md](docs/ai/FORMAT-API.md) for schema questions; do not invent manifest keys.
3. Work from the actual example packs and authoring grids. A generated texture grid is **not** evidence of exact spacing; inspect individual shapes, repack to measured pixel rectangles and preserve alpha/pivots.
4. **Stop before bulk animation** if the actual first source frame does not match user-approved art. Compare source and candidate side-by-side at native-gameplay and art resolutions; require explicit creator/artist approval. Passing PNG geometry, manifests, or counts never overrides an obvious art mismatch.
5. Follow [docs/ai/RELEASE-CHECKLIST.md](docs/ai/RELEASE-CHECKLIST.md). Use the official `tools/ai_acceptance.py` workflow on the exact delivered ZIP, with creator-specific assertions and applicable browser scenarios (`--visual-spec`). It already runs archive validation and crop scanning. Inspect every region, meaningful state and compatible preset; technical qualification does not establish artistic or rights approval.
6. Follow the execution path in START-HERE that matches the available tools. Deliver an actual self-contained ZIP when capable, with a truthful PASS/FAIL/WARN/NOT RUN receipt; otherwise state the missing capability. Never claim artwork or tests were reviewed if they weren't.

For complex character work, route from the [animation recipe](docs/ai/animations/README.md) to the applicable focused production guide. Use only the current project's references and acceptance requirements; historical case studies and their project-specific commands are not general prerequisites. Planning PASS is **not** image/animation QA or authorization to publish. Source images from conversation attachments must not be silently treated as approved/relicensed artwork.

Project QA: `bash RUN-ALL.sh`. The public builder runs locally and imports ZIPs privately. Do not modify the existing 2,073 icons or overwrite GitHub `main` without matching the expected branch revision.

**Pixel-art RPG icon tasks:** Read [the dedicated raster icon standard](docs/ai/icons/GAME-PIXEL-ART.md) in addition to the general icon/GUI recipes. Preserve painted pixel-art source; do not turn item creation into vector glyph generation. Do not publish a concept-board extraction without explicit art review and full visual/ZIP QA.
