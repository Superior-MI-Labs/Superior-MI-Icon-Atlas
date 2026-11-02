# Sky Blue Eyes / Shattered Sunblade — Art fidelity failure audit

**Decision: REJECT the current generated character, sword and effect sprites as production artwork.** This is a quality disposition, **not** a claim that ZIPs are corrupt or a request to delete reproducible source files.

**Scope audited:** conversation-approved Sky reference `image(20261102-125259).png`, creator angle/low-tail crop `image(20261102-135059).png`, original six Shattered Sunblade designs `image(20261102-113243).png`; reference handoffs v0.3/v0.4/v0.5; FX source & import ZIPs v0.1/v0.2; complete-sword Batch 03 and swordless body Batch 04; SVG/Python generators and local QA receipts; repository animation-plan tests and CI workflow. All relevant source archives were actually inspected, and the four local artifact validators were rerun successfully on 2026-11-02.

The original visual comparisons are provided as **conversation review attachments**, not public repo textures, to avoid redistributing or altering the user's reference images. Their file names are `body-reference-vs-batch04.jpg`, `sunblade-reference-vs-batch03.jpg`, and `body-motion-sampling.jpg`.

## Final disposition by actual deliverable

| Source | Verified contents | Technical result | Art-direction verdict | Reuse |
|---|---|---|---|---|
| Approved character ref | Hooded, masked 3/4 desert wanderer; fine cloth, fur, gilding, luminous blue eyes; later 3 low feathered tails | Authentic user-supplied reference; not a clean alpha sprite | **APPROVED IDENTITY REFERENCE**; sword depiction must **not** be baked into body frames | Reuse for all newly painted source poses |
| Original six Sunblades | Dramatically shattered relics, ornate star/sun guards, stone-metal surface, cloth and blue/orange energy through gaps | Authentic user concept material, not frames | **APPROVED WEAPON DESIGN LANGUAGE** | Reuse for new sword master and every frame |
| Reference kit v0.3/v0.4 | Includes concept collages and character candidate showing apparent worn/sheathed sword | Files present | **QUARANTINE AS PRODUCTION INPUT** — contradicts the separate autonomous sword | Use approved originals only |
| Reference kit v0.5 | Contains angle crop, six-sword concept and now-obsolete procedural A/B proofs; **does not contain the original full approved cloak image** as a separately named canonical input | ZIP intact | **REBUILD HANDOFF** — input regressed and deprecated workflow is mixed into it | Recreate clean role-separated reference kit |
| FX v0.1 | 7 clips, 84 PNGs | Local validator **PASS** | **REJECT AS FINAL GAME FX** — minimal radial spokes, flat dust, simple arc/curve motifs | Preserve timing/IDs and asset pipeline |
| FX v0.2 | 20 clips, 240 frame references, 265 manifest assets; 2 atlases | Local validator **PASS**, 240/240 source crop reconstruction | **REJECT AS FINAL GAME FX** — simplified geometric symbols, sparse detail, limited depth/material; only **224 unique RGBA image contents** according to its own QA receipt | Preserve effect taxonomy, timing concepts, packer and IDs; redraw FX |
| Sunblade Batch 03 | 7 clips, 84 PNGs, 92 manifest assets | Local validator **PASS**, 84/84 exact source pixels | **REJECT AS CANONICAL SWORD ART** — simplified guard, chunk polygons, flat surfaces, missing ornate complexity, physical form not faithful | Preserve seven clip IDs, timing studies, separate actor contract, atlas tools |
| Body Batch 04 | 9 clips, 92 PNGs, 103 assets | Local validator **PASS**, no clipping, 92/92 exact source pixels | **REJECT AS CANONICAL SKY ART** — geometric/puppet-like humanoid, simplified apparel, barely recognizable feline facial structure, rigid spiky tails, weak 3/4 depth; exaggerated departure from approved materials | Preserve nine clip IDs, logical canvas/trim and animation-state plan; repaint body and key poses |
| Prototype A/B | Procedural fragment demo and precomposed demo | Historical structural experiment | **RETIRED by creator** — do not resume fragment rig | Retain records only |

FX v0.1 is superseded by FX v0.2: **do not add its counts a second time**. Current distinct *candidate* clips: **20 FX + 7 sword + 9 body = 36**; current frame records: **240 + 84 + 92 = 416**. **Art-direction-qualified clips: 0.** Planned 315-action backlog is only a planning inventory, not shipped animation art. Technical PASS means a frame exists and is decodable; it says nothing about matching the approved design.

## Actual root causes (not speculative)

1. **Incorrect source-generation method.** `draw_sky.py` manufactures the body using SVG polygon/gradient primitives and sinusoidal joint parameters; `build_sunblade.py` similarly constructs the sword from generated polygon clusters and rotates/translates the composite; `build_fx_v02.py` generates rings, dots, lines and spirals. None of those draw from the fine-grained approved canonical painting. The algorithms are legitimate **technical fixtures** but fundamentally unsuitable as professional painted source art.
2. **Reference fidelity was never an enforced gate.** No side-by-side model-sheet-to-sprite review, consistent cloth seam/ornamentation landmarks, anatomy/face/eye/tail construction check or art-director approval blocked bulk generation. The assets went through dozens of clips even while the artwork was visibly off-target.
3. **Misleading progress metrics.** Pixel reconstruction, distinct IDs and 16 FPS loops were foregrounded as a sign of production readiness. They are *only* data-integrity checks. FX v0.2 has 240 addressable frames but 224 unique pixel images, demonstrating that “240 distinct drawings” would be false.
4. **Mismatched production inputs.** The character concept image includes a sword-like form by the back, but swordless body sprite production requires a **clean body-only visual reference**. Reference kit v0.5 removed the full approved cloak image rather than replacing that dependence with a correct clean body master. The character source never achieved a visually qualified painterly pose.
5. **Motion and continuity not demonstrated.** Per-frame mathematical deformation and image differences do not prove convincing hand-drawn character acting, planted feet, weight transfer, run-stop phase entry, scarf/tail follow-through, hand contact, or body/sword sync. The existing GIF composites are review images, not engine-integration tests.
6. **Irrelevant CI success.** GitHub CI exercised existing demo packs, plan assertions, shared renderer tests and public site snapshots; it did **not import or screenshot these exact new candidate ZIPs in the Builder**, nor compare their frames to the approved reference. The local Browser restriction is real, but it should have been a stop sign rather than a reason to proceed with more unapproved art.
7. **Instruction drift.** AI guides contained correct warnings (“not final”, “do not publish”) but still allowed production agents to *repeatedly* extend poor-quality assets. A quality warning with no enforced stop decision is not a production gate.

## Immediate action — stop expanding this art

- **Quarantine** all four historical candidate packs as **TECHNICAL FIXTURES / ART REJECTED**. Do not publish, advertise as finished, or build further clips by copying their body/weapon/FX drawing style. Do **not delete** the source ZIPs: they are useful for manifest, alpha and renderer regression.
- **Preserve what passed:** import/ZIP contracts, stable IDs, full-frame source preservation, logical canvas/trim/pivot, 16-FPS metadata, alpha-exact packer, computed atlas-memory savings, and the separate Sky/Sunblade actor contract. Preserve the *reviewed concept references* and 315-action inventory as planning material. No need to rewrite the Visual Atlas renderer.
- **Redo the art:** replace the body and sword **from scratch as paintings**, not as progressively embellished vector polygons. Redraw FX after the body/sword style has been established. Do not spend effort merely upscaling, applying global textures, overlays or filter effects to the old frames.
- **Repair reference handoff:** canonical user-approved full cloak image (original), correct low-hip three-tail placement crop, original Sunblade six-concept image, clean **swordless** 3/4 body master, isolated sword master, unframed head/eye study. Make derivative reference outputs optional; no decorative posters or procedural A/B references.
- **Spend art-production effort on the smallest real fidelity gate:** first one full-size professional-quality **swordless Sky pose** with correct feline build, cloth/ornament, ears, mouth veil, galactic eye, three low feathered tails and shallow 3/4 depth; independently one **dormant sword pose** true to the ornate original six-concept reference. Evaluate both at native gameplay scale *and* close-up. **Do not animate either until these two actual drawn source assets are accepted.**

## The non-negotiable approval stages

**G0 — Canonical art source:** actual user-supplied originals, role/provenance/license, no misleading back-worn sword in body-only inputs.

**G1 — Visual master approval:** side-by-side comparison shows identity, silhouette, anatomy, coverage and shape of clothes, material finish, tails, iris and sword complexity. An art-director/user must expressly approve the *actual source PNG*, not its description. **Any obvious style mismatch = FAIL.** Save visual comparisons and frame source paths, not just test booleans.

**G2 — Motion approval:** only after G1; create 4–8 actual key drawings and real in-betweens for one idle/action. Inspect EVERY adjacent pair, first/last seam, planted feet, root consistency, tails, cloth, sword energy and hand marker. Clip must be approved at real gameplay size.

**G3 — Exact ZIP/Builder approval:** preserve existing format, run exact RGBA reconstruction and official import/preview of the *exact* ZIP. Do not infer import PASS from generic repo CI.

**G4 — Publication:** only after visual-source approval, motion approval, exact ZIP/browser tests and rights confirmation. `publications.json` remains unchanged until all gates pass.

The production system should be **fail-closed**: until G1 passes, batch generators may make only **technical fixtures**, not publishable player characters or final sword/FX assets. An “AI one-shot” run is allowed to spend multiple steps qualifying and correcting its output; it may not change the art target to make the success test easier.

## Required future evidence

A reproducible visual review must include: exact input references (or private hashes), a consistent-scale side-by-side of original vs candidate, clean unframed source frame, front/3/4/back construction as needed for that motion, short 16 FPS animation review, explicit human approval, and the exact ZIP tested in the live renderer. If an external renderer blocks testing, return **HOLD** and report the blocker. Do not generate the next 50 clips while on HOLD.

**Recommendation:** salvage the technical pipeline and production inventory; **remake nearly all artwork** in FX v0.1/v0.2, sword v0.1 and body v0.1. This is a real reset of image quality, not a reset of the entire repository.
