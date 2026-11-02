# Pixel Fantasy — HD game items and interaction effects

**Published collection · 48 item icons · 65 addressable assets · CC0-1.0**

This collection contains 48 HD fantasy pixel-art items and 17 reusable interface assets (13 visible effect regions, one transparent-state composition, two state sets, one configurable item-slot composition). Subjects include potions, equipment, jewelry, weapons, spells, resources, tools, food, and quest items. All art uses 128 × 128 logical icon canvases with transparent alpha and stable IDs. Three 512 × 512 icon sheets and one effects sheet are owned by one `smi-visual-pack/1` manifest. 

[Explore the collection](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/) · [Open the Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html)

## Integrating

Download `pixel-fantasy-icons.zip` from the public catalog, or build a ZIP from this folder with `python3 package_candidate.py`. The `collection.json` points to the entry composition `smi.game.pixel01.widget.item`, which can swap among 48 compatible items using its `icon` slot. `interaction`, `rarity`, `cooldown`, `selected`, `equipped`, `locked` and `new` are independent typed appearance inputs. The host game owns the actual gameplay, mouse and keyboard actions. `cooldown` is a **linear** clip, not a radial sweep.

Every region has exact `rect_px` texture coordinates; the manifest is the sole authoritative runtime contract. The public search index and ZIP are generated. Icon ID stability does not depend on physical sheet position.

## Artwork and QA

Wave 1 was redrawn from a frame-free source to replace clipped original art; Wave 2 and Wave 3 come from separate image-generation source sheets. The included crops were checked for texture dimensions, refs, transparent padding, texture SHA-256 and 48 per-item pixel baselines. Pixel baselines detect accidental edits and rect shifts, but **cannot prove a drawing has its complete intended silhouette**. The original source images and `qa/all-48-contact.png` are included for future art improvements. Some source images were background-extracted from generated RGB artwork and can have imperfect alpha boundaries. This published collection is a usable first release, not a guarantee that all silhouettes or cleanup details are final.

The [AI crop and Builder QA guide](../../docs/ai/icons/PIXEL-ICON-CROP-QA.md) records earlier regressions (health potion bottom, fireball edge) and requires actual Builder renders for future asset changes.

## Rebuild and qualify

- `python3 assemble_wave123.py` — deterministic pack from source images; requires Pillow, NumPy and OpenCV. Artwork changes require regenerating corresponding QA baselines after review.
- `python3 verify_pack.py` — validate geometry, alpha gutters, references and pixel baseline (Pillow).
- `python3 package_candidate.py` — deterministic import ZIP. Script name retained for compatibility with existing authoring workflows.
- Repository qualification: `python3 tools/validate_visual_pack.py site/demo/pixel-fantasy-icons.zip` and `python3 tools/ai_acceptance.py site/demo/pixel-fantasy-icons.zip --acceptance examples/pixel-fantasy-icons/qa/acceptance.json --out /tmp/pixel-qa`.
- The normal CI browser-visual matrix exercises the actual Builder composition and checks that all 48 slot options produce different renderings where expected.

**Originality/licensing:** Original AI-generated illustrations contributed for use under CC0-1.0. The art direction is fantasy RPG pixel art; it is not a copy of assets from Zelda, D&D or another game's protected icon library.
