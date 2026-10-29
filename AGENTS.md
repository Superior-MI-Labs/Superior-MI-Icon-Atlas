# Visual Atlas agent entrypoint

**Creator-first:** Preserve the user's actual goals, context and constraints. Translate them into a concise internal brief and a request-specific acceptance test. Do not substitute a generic demo for the requested artwork.

1. Read [docs/ai/START-HERE.md](docs/ai/START-HERE.md) (short checklist).
2. Choose **only the relevant** recipe from [docs/ai/INDEX.md](docs/ai/INDEX.md). Read [docs/ai/FORMAT-API.md](docs/ai/FORMAT-API.md) for schema questions; do not invent manifest keys.
3. Work from the actual example packs and authoring grids. A generated texture grid is **not** evidence of exact spacing; inspect individual shapes, repack to measured pixel rectangles and preserve alpha/pivots.
4. Follow [docs/ai/RELEASE-CHECKLIST.md](docs/ai/RELEASE-CHECKLIST.md). Run the ZIP validator, per-region contact-sheet QA and a **creator-specific acceptance test** using `tools/ai_acceptance.py` with real, user-derived assertions. Check all animated and compatible presets.
5. Deliver an actual self-contained ZIP plus a truthful PASS/WARN/NOT RUN receipt. Never claim artwork or tests were reviewed if they weren't.

Project QA: `bash RUN-ALL.sh`. The public builder runs locally and imports ZIPs privately. Do not modify the existing 2,073 icons or overwrite GitHub `main` without matching the expected branch revision.
