# Visual tagging guide

Use the icon pixels, not an inferred software role. Name a flame **Flame** whether its physical source sheet happens to be `programming` or `nature`. Assign the cross-domain subject `nature.fire` and include directly observable discovery words such as `fire`, `flame`, `burn`, `heat`, `blaze`.

Avoid generating 100 tags for one symbol, generic tags already present as facets (`white`, `tintable`, `monoline`), or concepts a symbol might theoretically be used for. Synonym groups in `manifest.json` should be small and curated. Distinguish `function` from a language-specific token `def`; an icon is not a substitute for a typed programming contract.

A reviewed record needs a human-friendly name, at least one meaningful visible tag, a visual subject/facet, and a review evidence note. Metadata review is not copyright clearance. Run `python3 atlasctl.py validate --deep` and browser search tests before publishing.
