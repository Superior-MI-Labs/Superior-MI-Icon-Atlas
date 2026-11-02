# Sky Blue Eyes — P0 canonical artwork review (2026-11-02)

**Status: DESIGN IDENTITY APPROVED · CANONICAL DIRECTIONAL ART NOT QUALIFIED · ANIMATION FRAMES NOT PRODUCED.**

This is the single **project-specific review**, linked from the reusable [side-scrolling production recipe](../../docs/ai/animations/SIDE-SCROLLER-PRODUCTION.md) and machine-readable [plan](plan.json). The current approved clothing source is the image **supplied and positively selected by the creator** in conversation (`image(20261102-125259).png`, SHA-256 `5f0aa77d1514c1f859a5143732d4a39a3295a2afbb3b0fc0731878c98d95c97f`). The original pixels are not stored in this repo. A future agent must obtain the exact source image before generating derivative production views or certifying visual parity.

## Confirmed, user-approved identity

- Grounded desert wanderer, no wings. Tall spotted feline monk, draped cream/saffron hood, red tattered cloth layers, gold sun emblem, covered nose/muzzle/mouth, only eyes visible beneath the hood.
- **Three feathered tails**, each anatomically separate, orange/red with restrained teal/blue accents. The reference image alone does not unambiguously prove three roots; creator's new instruction overrides that ambiguity. Do not silently reduce to two or one because the angle occludes them.
- Cosmic eyes: black-hole-like pupil at the iris center, swirling blue/teal accretion dust, tiny stars and faint short light trails. Read as blue from a distance; detailed cosmic effect visible close up. Keep the eyes readable, not blinding and not invented as a red "low HP" form.
- Dialogue identity concealed: **no exposed mouth and no framed portrait baked into the art**; masked speech via eye focus, ears, scarf tension, subtle head movement. Separate front, three-quarter and side close-up masters.
- Normal body visual tier: health **above 36%**. Low-health body visual tier: health **36% or below**. No intermediate/fatigued tier in V1, plus independent death.
- Dormant Shattered Sunblade: single base silhouette, wrapped bands and tied phoenix feathers, barely perceptible cohesion magic. Fire, frost, wind, radiant, storm and spirit variants are optional overlay/progression explorations, not separate baseline models.
- **Drawn Shattered Sunblade animation (latest creator decision):** the sword is visually fragmented, with separated relic pieces flexing and magical energy weaving between them **in hand-drawn complete sword frames**. Do not use runtime-controlled shard objects or an A/B procedural comparison. The sword stays a separate actor near Sky's back, not sheathed; when held, the complete animated sword follows the hilt/hand anchor.

### Weapon-art qualification still pending

The sword concept reference is **not** a finished animation. Produce isolated sword-only key poses, real in-between whole-sword PNG frames and matching energy/gap motion. Check the hilt/hand contact, hover loop, adjacent frames, true alpha bounds and browser ZIP import. The previous procedural-shard experiment is closed; do not require separate fragment textures, a shard rig, or an energy endpoint solver. Never approve a static sword with decorative cracks as completed animation.

## November 2 — approved stance angle and lower tail roots

The creator has approved the masked desert-wanderer style and a **shallow right-facing three-quarter hero presentation** (cropped original: `image(20261102-135059).png`). This camera/stance angle is deliberately not an entirely flattened side profile: the torso, feet, hood and robes retain modest depth while Sky faces right.

**Correction to the earlier tall isolated study:** its upper two tails are attached too high. **All three** tails must arise in the lower back/pelvic/hip region, then sweep backward and downward with plausible overlap, as in the creator's approved crop. Do not lower their tips alone; relocate their **roots and intervening feather bases** while preserving the cloth and belt construction. The back view must reveal three distinct attachments; the hero view can naturally overlap them.

The eight-view technical turnaround **still includes a true 90-degree side** as a construction proof, but the right-facing **hero master is a shallow oblique** image. Angle approval does not mean the generated tall study with high tails passed. A corrected full-resolution one-character source, unframed dialogue heads and separately articulated Sunblade source assets are still required.

The latest generated multipanel comparison poster is again **presentation-only**; it is not usable individual-frame source art. Keep it out of animation qualification/published packs. The right-side portrait with orange background is also a **candidate** until its tail-root and angle corrections are demonstrated. See [dual-stick combat and reference proposal](CONTROL-AND-COMBO-PROPOSAL.md).

## Eight-view canonical direction list

| Key | Reference orientation | Critical verification |
|---|---|---|
| front | facing viewer | cloak clasp, scarf, ears, bilateral paws; tail roots mostly hidden |
| front_right | 45° toward viewer/right | hood embroidery and brooch placement |
| right | 90° true side | orthographic body / exact ground baseline / shoulder profile |
| back_right | 135° | three tail roots and overlap, cape/strap continuity |
| back | 180° rear | three distinct tail roots and cloak/hood back construction |
| back_left | 225° | symmetric anatomy but consistent asymmetrical costume |
| left | 270° true side | independent full-resolution source, compare mirror feasibility |
| front_left | 315° | keep all garment seams and access to one visible eye |

Do not confuse this **turnaround reference coverage** with a commitment to make every action in all eight facings. Initial playable P1 remains right-facing idle/run and left-facing compatibility tests.

## QA observations from the exploration

| Observation | Root cause | Correction | Gate |
|---|---|---|---|
| Several outputs combine diagrams, swords, portraits and eight tiny full-body figures | The image engine optimized for an attractive reference poster | Isolated **one full-height orthographic pose per generation**, no headers or boxes | One visible unclipped character, ground line, identity consistent at gameplay scale |
| Full-body figures are too small to compare robe seams or tail anatomy | Packing eight figures onto one canvas consumes detail | Author full-resolution per-facing masters **before** a derived summary board | Side/back overlay/landmark comparisons at equal scale |
| Some heads are framed/insets rather than reusable sprites | Dialogue preview and source art were conflated | Generate separate unframed head/bust assets on transparent/flat neutral background | No baked frame; correct eye and veil appearance in each facing |
| Galactic-eye concepts vary between generated heads | No locked iris/pupil reference and inconsistent effect prompts | Lock blue/teal accretion structure around dark pupil, limited glow strength, consistent lens position | Close-up eye crop and game-size readability review |
| Exact tail number and roots unclear in miniature views | Side-view overlap plus over-composed source | Require 3 distinct rear roots with consistent attachment and composited occlusion | Inspect back and both back-three-quarter views; 3 distinct tails |
| Generated boards invented health-dependent eye color and effects | Broad status wording introduced optional design changes | Exactly two art tiers at creator's **36%** boundary; no color swap without approval | Plan asserts health boundaries; runtime later verifies selector |

No supplied art from these poster experiments has passed source-frame/alpha/pivot validation. All are **CONCEPT ONLY**. The uploaded reference is approved for identity; it is not a completed P0 turnaround.

## Qualification sequence

1. Derive a corrected full-height shallow right-front-three-quarter hero pose with the creator-approved perspective and **lower hip-rooted three-tail anatomy**; then produce the **strict 90° right-side** technical check without sword overlap. Confirm body proportions, feet baseline, hem, robe seams, and realistic root/occlusion relationships.
2. Derive full-height back (180°) from the same construction reference; expose all three feathered tails and actual attachment positions. Then front (0°), left (270°), and the four diagonals.
3. Produce separate **unframed** head references (front, side, three-quarter) with the same scarf/hood/ears/galactic iris. Confirm masked talk, blink, listening, and neutral studies are genuinely different but consistent.
4. Produce the separate **dormant** blade canonical art without baked element effects. Review its scale, cloth/frayed wraps and phoenix-feather ties.
5. Apply the existing [release QA](../../docs/ai/RELEASE-CHECKLIST.md) only after real frame PNGs and a self-contained manifest ZIP exist. Passes on the **plan validator** never imply animation/art PASS.

## Present QA receipt

- Creator identity and wardrobe selection: **APPROVED**.
- Three tails / galaxy-eye / two-tier health requirements: **SPECIFIED**.
- Eight individual matching canonical views: **NOT QUALIFIED**.
- Unframed reusable dialogue head masters: **NOT QUALIFIED**.
- Source image redistribution/licensing provenance: **NOT VERIFIED**.
- Real PNG sprite frames, atlases, P1 animation ZIP: **NOT PRODUCED**.
- Frame-by-frame visual QA and pack import/export: **NOT RUN**.
