# Repository audit — v0.3.2 → v0.4.0

Scope: live public repo `Superior-MI-Labs/Superior-MI-Icon-Atlas`, `main` inspected 2026-10-29, corroborated against the locally mounted matching v0.3.2 release package. **No upstream files were changed during this audit.**

## Observed issues

| Finding | Evidence | Resolution |
|---|---|---|
| Monolithic icon registry | 3,344,586-byte `manifest.json`, 2,073 inline candidate entries | Split into compact index and 20 sheet-owned manifests; `atlasctl.load()` composes runtime view |
| Poor search relevance | Only 29 unique generic tags across 2,073 entries; 789 records repeated their own tag | Eliminate inherited generic tags from icon records, add reviewed names / curated tags / real subjects; weighted token search |
| Missing flame metadata | `icons.candidate.programming.r04i19` had only category/row/tint tags | Confirm visible flame; tag `fire`, `flame`, `burn`, `blaze`, `heat`, etc. with cross-domain subject |
| Unreviewed visual meaning | No reliable names for most AI-extracted candidate art | Label 49 unambiguous symbols, leave remaining 2,024 unreviewed and filterable |
| Duplicate atlas masks | All 20 `foreground-mask.png` files **byte-identical** to `atlas.png` | Delete duplicate files, refer to atlas alpha for tinting |
| Unnecessary duplicated CI step | `.github/workflows/pages.yml` installed image validation requirements twice | Reduce to one step |
| Source images mistaken for production assets | Raw irregularly aligned source images stored under `source-images/` | Keep them only for provenance; do not publish in website or use for runtime, document distinction |
| Inspection previews present | `inspection-preview.png` files on 20 sheets | Retain for human review; exclude from site build |
| QA screenshot at repo root | `before-after-alignment.png` is unreferenced by runtime or tests | Remove from production branch; old release archive retains historical evidence |

## Policy for future visual tags

No bulk inference from filenames, sheet category or neighboring sprite positions. Review each icon crop on a neutral backdrop at both 96×96 and UI size, then apply `name`, `aliases`, `tags`, `subjects`, `concept_id`, `review.status` through `tools/review_icon.py`. Record visual confidence separately from art quality and copyright/provenance clearance.

Review is ongoing; new search behavior is reliable for **reviewed** concepts. It is not a claim that all 2,073 assets have been semantically classified.
