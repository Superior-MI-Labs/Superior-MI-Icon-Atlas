# Visual metadata review — v0.5.0

## Scope

An additive **metadata-only** curation pass. No sprite pixels, cell coordinates, immutable icon IDs, source art or atlas hashes were modified. 685 newly recognized icons were inspected visually in contact sheets; 49 were already reviewed, for **734 reviewed / 2,073 total** (1,339 remain unreviewed).

The 685 records cover developer tools, file/media images and actions, hardware/peripherals, networking, data visualization/AI and UI interactions. Each reviewed record includes a literal human-readable name, restrained visual synonyms, a cross-domain subject, a concept ID and an evidence marker. Ambiguous glyphs remain unreviewed. Some images and symbols repeat; sharing a concept does not imply shared executable semantics.

## Important distinctions

- `review.status = reviewed` means *visual subject has been identified*, **not** artwork approved for publication or copyright-cleared.
- An asset's ID and cell location remain fixed even if its semantic name later improves.
- Search synonyms are curated related words, **not** a blanket assertion that all concepts sharing one term are interchangeable.
- Browser search/UI is a *derived projection* of the 20 authored sheet manifests; it never owns a separate editable tag catalog.
- `white-geometric-monoline` remains the atlas style. New styles should be declared at the pack level, not embedded ad hoc in tags.

## Remaining backlog

- 1,339 unreviewed crops need visual inspection or rejection. Do not automatically label based on source sheet titles.
- Review image-generator artifacts for shape correctness and rights provenance independently from metadata review.
- Audit visually duplicate silhouettes and identify when separate style variants are justified.
- Conduct a real-host browser end-to-end run and Studio integration qualification before claiming full production readiness.

## Search examples

`fire` → Flame; `picture`/`photo` → reviewed picture assets; `terminal` → shell console symbols; `database` → data storage; `microchip` → processor outlines; `wireless router` → wireless network equipment; `checkbox` → UI control.

## Regression gates

```
python3 atlasctl.py validate --deep
python3 -m unittest discover -s tests -p 'test_site.py' -v
python3 tools/build_site.py
node --check web/app.js
node tests/browser-search.cjs
```
