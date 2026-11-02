# Visual Atlas agent entrypoint

**Creator-first:** Preserve the user's actual goals, context and constraints. Translate them into a concise internal brief and a request-specific acceptance test. Do not substitute a generic demo for the requested artwork.

1. Read [docs/ai/START-HERE.md](docs/ai/START-HERE.md) (short checklist). For substantial/ambiguous work consult its linked creator preflight and image-source workflow rather than improvising a second process.
2. Choose **only the relevant** recipe from [docs/ai/INDEX.md](docs/ai/INDEX.md). Read [docs/ai/FORMAT-API.md](docs/ai/FORMAT-API.md) for schema questions; do not invent manifest keys.
3. Work from the actual example packs and authoring grids. A generated texture grid is **not** evidence of exact spacing; inspect individual shapes, repack to measured pixel rectangles and preserve alpha/pivots.
4. **Stop before bulk animation** if the actual first source frame does not match user-approved art. Compare source and candidate side-by-side at native-gameplay and art resolutions; require explicit creator/artist approval. Passing PNG geometry, manifests, or counts never overrides an obvious art mismatch. See the [Sky rejection audit](production/sky-blue-eyes/ART-FIDELITY-AUDIT-2026-11-02.md) for the failure that introduced this gate.
5. Follow [docs/ai/RELEASE-CHECKLIST.md](docs/ai/RELEASE-CHECKLIST.md). Run the ZIP validator, per-region contact-sheet QA, relevant **visual state-change regression**, and a **creator-specific acceptance test** using `tools/ai_acceptance.py` with real, user-derived assertions. Check all animated and compatible presets.
6. Deliver an actual self-contained ZIP plus a truthful PASS/WARN/NOT RUN receipt. Never claim artwork or tests were reviewed if they weren't.

For side-scrolling character requests, route from the existing [animation recipe](docs/ai/animations/README.md) to its focused [production guide](docs/ai/animations/SIDE-SCROLLER-PRODUCTION.md). Validate the candidate production plan with `python3 tools/validate_animation_plan.py production/sky-blue-eyes/plan.json`. Planning PASS is **not** image/animation QA or authorization to publish. Source images from conversation attachments must not be silently treated as approved/relicensed artwork.

Project QA: `bash RUN-ALL.sh`. The public builder runs locally and imports ZIPs privately. Do not modify the existing 2,073 icons or overwrite GitHub `main` without matching the expected branch revision.

**Pixel-art RPG icon tasks:** Read [the dedicated raster icon standard](docs/ai/icons/GAME-PIXEL-ART.md) in addition to the general icon/GUI recipes. Preserve painted pixel-art source; do not turn item creation into vector glyph generation. Do not publish a concept-board extraction without explicit art review and full visual/ZIP QA.
