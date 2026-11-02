# Sky Blue Eyes — Production Batch 03: independent drawn Sunblade

**Status:** 7 **real candidate animation sequences** and source sprites built; local exact-RGBA/manifest QA **PASS**; visual identity review, actual Builder ZIP import, and public release **PENDING**. **No new character/body animations are being claimed.**

This follows [FX Batch 02](FX-BATCH-02-RECEIPT.md) and the 315-clip [production inventory](ANIMATION-INVENTORY.json), using **existing `smi-visual-pack/1` region, sequence and state_set assets**. The user explicitly chose traditionally drawn *whole-sword sprites*, so there are no runtime shard meshes, per-shard manifests or procedural fragment state-machine additions.

## Binary handoff (conversation archive; not committed)

- `Sky-Animation-Production-Batch-03.zip` — reviewed source directory: full 84 PNG drawings, standalone sword import ZIP, the unchanged FX 0.2 import ZIP, two atlas pages, offline SVG/Python source, six composite GIF reviews, seven source animation GIFs, local QA script, exact receipt, and an offline HTML review page.
- `sky-sunblade-drawn-v0.1.zip` — independent **5,097,676-byte** Visual Atlas import candidate, `pack_id: smi.sky.sunblade.drawn`, `version: 0.1.0`.
- `sky-fx-foundation-v0.2.zip` — **unchanged** 20-effect library from the prior batch; not repacked and not published by this PR.

The artifacts live as user-visible conversation downloads, not in GitHub. A future agent must receive that handoff before claiming to inspect its pixels or run it in Builder.

## Confirmed source/pack measurements

| Metric | Measured |
|---|---:|
| Completely drawn sword frames | 84 (7 clips × 12) |
| Clip names | back_hover, orbit, cast, recall, grab_lock, held_slash, release |
| Playback | back_hover and orbit loop; five others are one-shots |
| Authored FPS | 16 |
| Full source canvas | 360 × 480 RGBA |
| Addressable visual assets | 92 (84 regions, 7 sequences, 1 state_set) |
| Atlas pages | 2: 2024×2048 and 1992×1392 |
| Import ZIP bytes | **5,097,676** (4.86 MiB) |
| Decoded atlas RGBA bytes | **27,672,064** |
| Naive untrimmed RGBA bytes | **58,060,800** |
| Decoded atlas reduction | **52.3%** |
| Byte-exact atlas → canonical source reconstruction | **84/84 PASS** |
| Unique frames per clip | **12/12 PASS** |
| Numeric loop-edge heuristics | back_hover and orbit PASS |
| Existing public CI for repo docs/tests | separate PR required |
| Exact candidate ZIP Browser import | **NOT TESTED** |
| Creator approval of ornate sword style | **PENDING** |
| Full Sky body/tail motion art | **NOT PRODUCED** |

The artwork itself is **offline vector-painted complete sword frames**, rendered to PNG; it is deliberately not a per-fragment runtime rig. It depicts readable fractured negative space, swirling energy, old cloth, feather ties and a solar guard, but it is **simpler than the user's approved ornate Shattered Sunblade references**. **Do not label it final canonical sword art.** The prior image-generation attempt produced yet another decorated *production poster*, not actual source sprites, and was excluded from both ZIPs.

### Local checks and what they prove

1. All seven states are actual 12-frame `sequence` assets under a single `state_set`, without a runtime fragment graph.
2. All 84 full-canvas source PNGs have nonempty transparency and distinct content; every region rectangle is inside the declared PNG sheet and `logical_size_px`/trim data is consistent.
3. The exact packed atlas frame reconstructs **byte-for-byte** to the original full PNG source for 84/84 frames, including hidden RGB.
4. ZIP CRC, all references, 24 MiB per-member and 120 MiB expanded limits pass. The two default looping states pass numeric adjacent-vs-seam diagnostics.
5. Six **review-only GIFs** combine original sword drawings with earlier FX sources (cast+ember, orbit+gale, back_hover+cohesion, recall+recall FX, grab_lock+grab flash, held_slash+claw), without introducing a broken cross-pack manifest dependency.

**These checks do NOT certify:** an actual browser import of the new ZIP, good body-to-sword hand attachment, combat physics, an artist-approved 2D animation loop, or final quality/identity match. GIFs are not a substitute for the existing browser visual QA gate.

## Learning to carry forward

- **Repeated model failure:** requesting original source drawings yielded a large attractive infographic asserting imaginary 'complete' asset counts. Only files with real per-frame alpha PNGs, manifests and tests count. If generation continues to return posters, pivot to a reversible source drawing/renderer *for technical qualification*, and disclose aesthetic differences rather than declaring it hand-painted production-ready.
- **Source-of-truth discipline:** keep the original complete source frames and stable region/sequence IDs. Optimize by trimming/pasting and preserve all RGBA channels, not by overwriting approved source art or duplicating the runtime pipeline.
- **Separate actor:** sword pixels never appear in Sky's swordless body sprites. Hilt-to-hand attachment is an independent host-game transition, not achieved by drawing a static sword on Sky's back.
- **Do not combine manifests blindly:** to make a compound scene, the host renderer must explicitly load both independent visual packs; the standalone ZIPs have no hidden cross-pack dependencies. The six preview-only GIF composites demonstrate art timing, not actual runtime interoperability.
- **Scope:** user has asked to move past references. The next expensive art effort is genuine swordless Sky idle/run/stop **poses and frame-by-frame tails**, plus visual polish of the complete sword drawings. Do not reopen concept sheets or a procedural-shard A/B debate.
- **Other agent:** do not recompress or rewrite already-published repository textures while the separate optimization agent owns that work.

## Promotion gate

Open the exact sword ZIP with the live [Visual Atlas Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html), select `sky.sunblade.full.preview` and inspect all seven states. Review the visual style against the six original Sunblade concepts and test hand/grip alignment in a character preview before approving. Only then consider publishing in a *separate* PR and including searchable tags/asset catalog. Preserve the candidate archive for reproducibility.
