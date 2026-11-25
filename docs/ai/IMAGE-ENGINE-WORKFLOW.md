# Image generation: source artwork

Use this guide when creating raster artwork. The production agent owns the full brief, source selection, packaging and qualification. The image engine receives a small visual task.

## 1. Write a visual brief

Describe the desired pixels in a few sentences:

- Subject, count and arrangement.
- Style, palette, perspective and lighting.
- Complete silhouette, spacing, framing and background/alpha.
- Approved visual reference and its role, if needed.

Lead with what should appear. Use positive descriptions such as "unlabeled artwork on a transparent canvas" and "six separate complete silhouettes with empty space between them." A short exclusion is useful only when it addresses an essential visual constraint. Keep the technical production brief, package names, schema, feature lists, licensing, QA, historical failures and release plans with the production agent, not the image request.

### Example: independent objects

Six hand-painted woodland plants in two rows of three: clover, broadleaf groundcover, bramble, bluebells, white anemones and a succulent rosette. Orthographic three-quarter view from 35 degrees above, warm highlights, cool shadows, detailed foliage. Complete individual silhouettes and generous transparent spacing; unlabeled artwork.

### Example: character or animation key pose

One full-body painterly character, matching the approved identity and clothing reference. Three-quarter view, left foot planted, right knee raised, arms balancing the stride. Full silhouette, consistent scale, transparent canvas.

For independent icons, HUD pieces, effects and terrain, follow the same brief; describe only the relevant subjects or layers. For a seamless terrain texture request one square unprojected repeatable surface. For motion, lock identity, costume, camera and anchor; change one pose/action variable at a time. Use the focused animation recipe for timing and qualification.

## 2. Isolate the generation context

Use a fresh visual-only context or explicit prompt/reference inputs when the available interface supports them. Supply approved source artwork as the reference; assign each reference one role (style, identity, pose or angle). Keep references clean and relevant to this exact task. A production overview or contact sheet is a planning or review artifact, not a source master.

Use the available tool's transparency control where supported. If the interface automatically derives prompts from the conversation and cannot isolate context, state the concise visual brief immediately before the call. This is a mitigation, not a guarantee. Never claim access to hidden rewritten prompts, seeds, session controls or reference controls.

## 3. Select a sheet layout reference

For any generated multi-asset or multi-frame sheet, choose the closest [transparent grid reference](../templates/sprite-grids/index.html). Download its PNG and attach it as the layout reference when the image tool supports reference images. Use a separate approved art reference for style or identity if needed. Keep the visual brief positive: "Fill the referenced 3 × 2 arrangement with six individual woodland plants, one complete silhouette centered in each cell, with transparent gaps."

Select by usable pixels per subject, not maximum count. Cell pitch is canvas width / columns and canvas height / rows; use the largest practical cell size for detailed artwork. For example, a 1024 × 1024 canvas with 2 × 2 cells and a 2048 × 1024 canvas with 4 × 2 cells both give nominal 512 × 512 cells. The thin gray lines are layout guides only; the finished artwork has transparent space between subjects. Request the closest supported aspect ratio and output size; the engine may resize the reference or alter spacing.

If references cannot be attached, describe the same layout in the short visual brief and record that limitation. Single isolated objects and seamless textures need no grid. Inspect actual output geometry and alpha before packing; use measured crops, remove any guide contamination without damaging the art, and never assume the generated cells match the reference coordinates.

## 4. Generate, inspect, then expand

Start with a representative slice. For independent objects, 2–6 well-separated subjects is a practical starting group; adjust density to detail, spacing and actual successful yield. Use a single object for complex silhouettes. Expand groups and batch accepted processing when the slice works.

Inspect returned pixels: subject, count, silhouette completeness, spacing, actual alpha over light/dark backgrounds, reference fidelity and target-scale readability. For animation inspect every frame, adjacent pair and loop seam at intended playback; preserve logical canvas and anchors across states/views.

Classify each result ACCEPT (usable source), CORRECT (specific repair) or REJECT (unusable). On failure, change the method rather than lengthen the prompt: simplify to the intended subjects, use a clean approved reference, reduce the group, or isolate context. Allow one corrected retry per unchanged method. When no effective alternative is available, stop that family and process accepted artwork. Rejected results are not production sources.

Record attempted groups, accepted/rejected sources, usable regions, correction method and actual available controls. Track usable regions per generation and quality, not advertised asset counts. Record observations separately from hypotheses about why a model failed. Routine production can provide this evidence; a separate benchmark is optional.

## 5. Process source art deterministically

Image generation supplies artistic pixels, not measured asset geometry or working behavior. Use actual pixel bounds, alpha and anchors to crop/repack into the existing canonical manifest. Create contact sheets, labels, overlays, documentation and QA receipts using deterministic tools after generation. Use genuine direction-specific artwork or vetted rigs for motion; avoid transforms that break identity or anatomy.

| Task | Tool |
|---|---|
| Source art and key poses | Image generation/editing |
| Crop, alpha, packing, alignment | Pillow, OpenCV or ImageMagick |
| Timed previews | FFmpeg/imageio |
| Rendered behavior and acceptance | Existing Atlas validators and browser matrix |

Finish with the [release checklist](RELEASE-CHECKLIST.md). Art review, rights, technical acceptance and deployment are distinct gates.
