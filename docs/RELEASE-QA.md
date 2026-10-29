# Superior MI Icon Atlas 0.1.0 — Actual qualification evidence

Executed 2026-10-28 (container runtime):

| Check | Result |
| --- | --- |
| 64 unique concepts / 192 unique IDs and three variants per concept | PASS |
| 24 × 8 atlas at 96 px/cell, transparent RGBA | PASS |
| Cell bounds, collisions, UV rectangles, nonempty crops | PASS |
| Each icon crop SHA-256, full-sheet SHA-256 | PASS |
| Foreground-mask and independent pure-black outline layers | PASS |
| Search regression: bug/defect, int/i32, picture, family, ocean | PASS |
| CLI crop and red tint preserving black outline | PASS |
| Portable offline installer, protected overwrite, backup on upgrade | PASS |
| Fresh-directory SVG rebuild reproduces exact PNG and manifest | PASS |
| Generated offline browser JavaScript syntax | PASS |
| Release ZIP CRC and clean extraction | PASS |
| Full manual visual review at actual Studio UI sizes | NOT RUN |
| Actual Studio/Linux/Windows app runtime qualification | NOT RUN |
| Remote GitHub repository creation or push | NOT RUN |

No older v10 third-party assets were included in the original starter. This is a source-based provenance check, not an external legal opinion or originality guarantee.

## v0.2.0 GitHub Pages browser (current)

- PASS: generated offline/Pages site from authoritative `manifest.json`, 192 icon records.
- PASS: duplicate ID and path/rectangle validation, all produced files present, PNG RGBA source verified.
- PASS: `node --check` JavaScript syntax.
- PASS: 5 standard-library `tests/test_site.py` tests.
- PASS: original 64-concept/192-icon release integration test, including installation and upgrade.
- PASS: real Chromium in-memory test of a generated manifest entry: gallery, filter, detail modal, transparent 96×96 PNG crop, exact filename, optional foreground tint and unchanged black outlines. Test uses original atlas PNG bytes embedded as data URLs because automation policy blocks navigation even to localhost or file URLs.
- NOT TESTED: GitHub Pages remote deployment / full HTTP browser navigation. The remote repository has not yet been created.
- CONTINUING ART REVIEW: starter icons retain their `candidate-human-review` status; legacy v10 third-party atlas is not included.
