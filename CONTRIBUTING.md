# Contributing to Icon Atlas

We welcome additions that are **distinctive, useful and independently authored**.

- Check whether the intended concept and artwork already exist before designing a new symbol.
- Preserve stable existing IDs, variants and pixel locations. Add sheets instead of renumbering icons.
- Use IDs like `icons.original.domain.concept.symbol`, with separate `.badge` and `.tile` variants only where useful.
- Include everyday search terms as tags (e.g. `png`, `image`, `picture`, `photo`), plus abbreviations and misspellings where warranted. Avoid assigning synonyms that conflate different concepts.
- Every icon must have source/provenance, license, a quality-review flag, exact cell and pixel coordinates, and a genuine RGBA transparent export.
- Do not trace, extract, or lightly recolor proprietary art and claim it as original. Permissively licensed third-party icon sets belong in separately named and attributed packs.
- Verify 24 × 8 atlases, 96 px cells, deterministic rebuilds, crop hashes, and the black-outline vs tint-mask separation.
- Keep the manifest authoritative. Do not add new independent search catalogs or Studio node semantics.

Before submitting a pull request, run the project's validation, website build, and tests. Explain new concepts, visual changes, and licensing evidence in your pull request.
