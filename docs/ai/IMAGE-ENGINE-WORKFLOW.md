# Image-engine workflow: generate useful source art, not fake atlases

This optional specialized guide follows [creator preflight](CREATOR-PREFLIGHT.md). It applies to character sprites, icons, GUI, world artwork and texture elements made with image generation. **Tool controls differ by environment:** inspect the actual available image-generation/editing interface instead of assuming every API option is exposed. Prompts do not enforce exact coordinates, alpha, or temporal continuity; validate output pixels.

## Capability and failure model

- Modern image models can generate and edit from text/reference images, vary aspect ratio, and request transparent backgrounds where supported. Some API surfaces offer multiple image inputs and masks/markup; **do not claim those inputs or controls are available unless the current tool exposes them**.
- Image output is a **rendered picture**. It is not guaranteed to be a real sprite sheet, pixel-perfect grid, animation, layered rig, palette-indexed texture, vector file or valid game resource. A reference image's clothing/face can drift between outputs.
- Previously failed here: "make a 208-frame sprite sheet" produced a beautiful **illustrated promotional board**, not usable frame geometry; warping a flattened character produced broken ankles; optical-flow in-betweens produced double heads and ghost limbs; a simplified single rig solved motion consistency but lost approved visual identity.
- Use an image model for *artistic identity and complete authored key poses*. Use deterministic composition/rendering for exact bounds and alpha, and genuine direction-specific animation art or a vetted rig for consistent motion.

## Source-only generation gate (all art families)

Separate the production brief from the image request. The production brief may contain repository names, manifest schemas, licensing, QA, delivery counts, roadmaps and host features; **none of that is visual subject matter**. Pass only the desired pixels, style, framing, reference roles and exclusions to the image engine. Never ask the image engine to draw the pack, manifest, contact sheet, release report, or technical alignment board. Build those later from actual measured pixels. Even a beautiful labeled board is a failed source-art result.

- For independent static objects, start with one object or 2–6 clearly separated objects on genuine transparent alpha. Specify count, subjects in reading order, complete silhouettes, generous empty gaps, projection, lighting and style. No text, logos, frames, labels, guides, shadows, ground or baked checkerboard. For textures, request one unprojected seamless square instead. Use the tool's transparency setting when available.
- Only use a clean approved object or source-only sheet as an image reference where supported; do not feed a promotional board back as the reference. Distinguish visual style references from content/pose references. If the tool automatically inherits conversation context or constructs its own prompt, use a fresh source-art-only request/session when supported. Do not claim access to an isolated prompt or reference control that the tool does not offer.
- After every generation, classify: ACCEPT (source pixels suitable for measured processing), CORRECT (one fixable visual defect), REJECT (wrong output class, fused/cropped objects, baked background or unacceptable quality). Inspect the actual alpha channel on dark and light backgrounds; count silhouettes and check separation, not merely nominal grid coordinates. Record observable evidence, not guessed internal prompt/seed.
- On a wrong-output-class rejection, change the method before retrying: drop all project/package vocabulary; use a clean source reference if supported; reduce to one subject or a smaller group. One corrected retry per unchanged method. If the same failure recurs, switch to isolated single-object generation or a fresh context where available. If neither is available or works, stop that family for the current run and package already accepted art; never repeatedly submit the same contaminated request or harvest a rejected board to inflate counts.
- Batch **deterministic** processing and release work: measure crops, preserve alpha and anchors, build manifests/contacts, run acceptance and review all regions. Expand source generation group size only after the representative group passes. For seasonal/directional/animation sets maintain matched logical canvas and anchors; distinct objects do not need forced matching silhouettes. Report generation calls, accepted sources, rejected sources, actual usable regions and unrun gates separately. Optimize accepted usable regions per call, not the advertised count on an image.

**Example source-only request (world foliage):** Six isolated painterly botanical game sprites, transparent PNG, two rows of three separated silhouettes. Top row: white clover clump, broadleaf groundcover, blackberry bramble. Bottom row: bluebells, white wood anemones, succulent rosette. Orthographic 35.264° downward view, warm highlights, cool shadows, natural organic variation, roots visible, no text, no background, no ground or cast shadow. Each plant fully inside its own allotted space with generous transparent margins.

**Observed regression (2026-11-25):** In the seasonal-fern and understory expansion rounds, two of eight returned images were usable source sheets (four seasonal ferns and six independent plants); six were branded presentation/technical boards. The source-only outputs had distinct subjects and visible spacing; rejected boards included invented counts, capabilities, manifest text and QA claims. Project-heavy conversation context is a plausible contributor, not a proven cause. This gate changes retry behavior and separates the visual request from engineering work; it does not guarantee image-engine obedience. Re-evaluate on a held-out asset family and log actual results before claiming improved yield.

## Small-scope prompting procedure

1. **Reference hierarchy.** Identify which image controls face/identity, which controls costume, which controls style, and which (if any) controls a target pose/angle. Avoid competing reference images without explicit roles. Keep a **canonical character identity sheet** separate from production frames.
2. **Lock invariants.** Explicitly describe age, silhouette, face/hair/glasses, attire/logo, palette, light direction, outline/pixel density, framing, full body and foot-contact baseline. Include exact confirmed values only.
3. **Change one variable.** Request **one facing and one action key pose at a time**, or a small set of expressly independent variations for selection. Once approved, preserve the source image and edit/pose-match it; don't regenerate the entire character from prose per frame.
4. **Production output, not a poster.** Ask for one isolated complete character on genuine transparent alpha, no text, cells, labels, guides, floor tiles, scenery, shadows or checkerboard painted into the pixels. Use PNG or WebP for alpha where supported. Separately generate presentation boards only if specifically requested.
5. **Pose-specific instruction.** Specify support foot, moving foot, contact/weight transfer, hip/shoulder/head orientation, and hands; for an impatient loop, define the emotion through measurable body actions. Supply a simple pose drawing/sketch if available. A pose may **not** be inferred from a static sprite's visual similarity.
6. **Inspect immediately.** Check the delivered alpha channel, entire silhouette, hand count, feet/sandal straps, angle fidelity, character identity, facial details and native-scale readability. Classify any miss. Make **one focused correction** at a time and compare against the canonical image. Reject an image that keeps drifting, don't keep blindly prompting.
7. **Deterministic asset build.** Isolate alpha, remove background/fringes, measure occupied bounds, align the intended foot pivot and pack onto a clean RGBA canvas. Pack regions from measured coordinates and build manifests with the existing `region` / `sequence` / `state_set` contract. Any generated pseudo-pixel art must be inspected at its actual pixel scale; naive automatic downsampling may destroy details.
8. **Temporal qualification.** Build a single complete loop with deliberately different key poses and true in-betweens; evaluate *every adjacent frame and the loop seam* at 0.5×, 1× and 2× in-game speed, then expand to the other viewpoints. Programmatic transforms only when their visual artifact is acceptable and the style calls for it.
9. **Production logging.** Record reference identifiers, intended role of each reference, current image model/tool if known, actual supported control settings, exact requested variation, result classification, correction attempts and approved source file. If the tool rewrites prompts internally, record the accessible prompt/log rather than inventing an exact hidden string.

## Prompt pattern: a single canonical game sprite

**Task:** Create ONE isolated full-body character sprite for [approved game and perspective], facing [named direction]. This is **production source artwork**, not a sprite-sheet showcase.

**Character identity (fixed):** [reference photo/image priority, face, age, hair, glasses, features]. **Costume (fixed):** [clothes, colors, markings]. **Style (fixed):** [approved pixel-art style and true target scale], [camera elevation], [lighting], [palette]. **Action (only variable):** [exact pose, grounded foot, body weight, limb directions]. **Framing:** Entire feet and hair visible; same body height and foot pivot across views.

**Output:** One isolated character, transparent alpha, no graphic panel or added text, no duplicate limbs, no ground plane, no composited scene. **Preserve:** [reference-identity features]. **Do not change:** [locked features]. The image is *subject to pixel measurement and review* after generation.

For pose-specific edits, supply the **approved canonical sprite** and **a pose reference with explicit roles** when supported, and request only the necessary joints/expression to change. Do not use generalized "make the whole sprite animated" instructions.

## Tool selection, based on actual access

| Work | First choice | Why |
| --- | --- | --- |
| Identity, art direction, canonical pose | Image generation/editing with accessible reference images | High-quality visual starting point |
| Rig/pose study | Explicit skeleton/rig rendering, if available, **as reference only** until its appearance passes approval | Correctable contact and perspective |
| Segmentation, transparent cleanup, packing | Pillow, OpenCV or ImageMagick | Actual pixel boundaries and deterministic coordinates |
| Playback previews | FFmpeg/imageio | Real timed loops; not falsely inferred from a contact sheet |
| Behavioral verification | Existing Visual Atlas Playwright/Chromium visual matrix | Checks actual builder rendering |
| Rights, identity, motion quality | Human or visually capable agent reviewing each asset | Automated validators cannot certify these |

Do not add an animation model, 3D renderer, editor plugin or license-heavy dependency to the project merely because one sample is difficult. Compare costs and concrete tests first.

**Evidence references:** OpenAI image prompting/generation docs (current capabilities): https://developers.openai.com/api/docs/guides/image-prompting and https://developers.openai.com/api/docs/guides/image-generation. These describe the public API, **not** guaranteed controls for every chat interface.
