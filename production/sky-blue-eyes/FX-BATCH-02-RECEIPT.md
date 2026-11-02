# Sky Blue Eyes — FX production batch 02 (candidate)

**Status:** actual assets built, local structural & source-pixel QA **PASS**; **official Visual Atlas Builder import NOT TESTED**, creator style approval **PENDING**. **Do not publish** this pack in `publications.json` yet.

## Handoff

Delivered separately in this conversation, not committed to GitHub:

- `sky-fx-foundation-v0.2.zip` — import this exact ZIP in the live/local-first Visual Atlas Builder.
- `Sky-Animation-Production-Batch-02.zip` — complete reproducible source delivery: all 240 full-canvas PNG frame masters, two trimmed atlases, manifest, Python builder and validator, interactive offline preview, GIFs, contact sheets, and QA receipt.

This is a continuation of `Sky-Production-Kickoff-v1.zip`; version 0.2 **preserves all first seven effect IDs**. It does not rewrite published assets or interfere with the separate image-optimization agent.

## Measured output

| Metric | Observed |
|---|---:|
| Effects / sequences | **20** (7 inherited + 13 new) |
| Complete authored 256×256 RGBA source frames | **240** (12 per effect) |
| Visual Atlas addressable assets | **265** (240 regions, 20 sequences, 5 state selectors) |
| Texture sheets | **2** lossless RGBA PNG pages (2040×2048 and 2040×1416) |
| Import ZIP | **5,640,077 bytes** (~5.38 MiB) |
| Decoded atlas memory | **28,266,240 bytes** |
| Naive untrimmed 240×256² RGBA memory | **62,914,560 bytes** |
| Measured decoded-memory reduction | **55.1%** |
| Authored playback | **16 FPS** (12-frame loops/one-shots) |

**New families:** heavy-landing sand ring, directional dash trail, guard break, ember eruption, gale vortex, radiant reveal, lightning branches, spirit mist, sword hilt-grab lock flash, recall trail, loot glint, healing pulse, and martial claw arc. Three loop candidates (`cohesion`, `gale`, `spirit`) passed *numeric* loop-seam heuristics; this does **not** establish visual smoothness.

## Exact checks passed locally

- ZIP integrity and manifest/texture members; exact versioned IDs, all state targets, no duplicate asset IDs.
- 240 frame rectangles within two 2048-maximum-size PNG atlases, original full logical canvas and trim offsets validated.
- **Byte-for-byte exact RGBA reconstruction of every original source frame** from atlas coordinates, including transparent RGB channels; do not reduce this to perceived similarity.
- Unique/nonblank frame controls, playback state and frame timing checks, crude loop-seam thresholds.
- No novel runtime types, no sword shard rig, no body art with swords baked in.

## Critical production lesson

The original packer used `alpha_composite` when copying non-overlapping trimmed frame rectangles onto a transparent atlas. This subtly modified hidden RGB values for some pixels even though the effects looked identical. **Root cause:** blending with an empty destination is still compositing, not a raw data copy. **Fix:** use a straight RGBA `paste` for deterministic, non-overlapping packed rects. **Regression:** reconstruct each packed frame to its full 256×256 logical canvas and compare `.tobytes()` to the canonical PNG source. This caught a real defect that ordinary alpha-bound tests missed.

Trimmed frame `logical_size_px`, `trim_offset_px`, and `pivot` reuse the existing shared Canvas renderer contract. No renderer fork or second metadata registry.

## Unresolved gates

1. Import **the exact new ZIP** in [Visual Atlas Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html), verify all 20 selectors and animations, check frame and clip dimensions and capture browser screenshots. Local Chromium blocked navigation even to a `data:` page, so there is **no browser PASS** for this candidate.
2. Judge art style and readability at the actual game scale, including transparent edges, bright/dark backgrounds and real action overlap; no false visual approval from a contact sheet alone.
3. The traditionally *drawn complete sword hover/cast/recall* and **swordless Sky body motion** are still pending actual source animation frames. Do not confuse these standalone effects with sword or character animation.
4. Only after both user style approval and actual ZIP import qualification, submit an intentional separate asset-publication PR.

## Next qualified production batch

Rather than return to concept images, create genuinely isolated Sky key poses and real adjacent frame drawings for `body.idle.relaxed`, `body.run.loop`, `body.run.stop`, `tails.idle`, `sword.back_hover`, and `sword.orbit`. Keep hilt and foot anchors and hip-rooted three tails consistent, no physical sheath, no wings and no procedural shard controller. Submit source PNGs, exact frames/trim metadata, preview and a PASS/HOLD receipt.
