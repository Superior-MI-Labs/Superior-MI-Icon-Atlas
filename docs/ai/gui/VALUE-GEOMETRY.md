# Value-visual fidelity: meters, sliders and progress controls

**Mandatory for AI-generated visual packs whose appearance communicates a numeric value.** Read this with [GUI recipe](README.md) and the shared [release checklist](../RELEASE-CHECKLIST.md). This is production guidance for the existing `smi-visual-pack/1` contract, not a new manifest format.

## Incident: Fantasy HUD Wave 1, v0.1 → v0.2

A ZIP passed structural tests while its appearance was misleading. Three independent defects caused it:
1. An SVG `viewBox` had a different aspect ratio than the rendered canvas. Default preserveAspectRatio *letterboxed* the long bar. Exact source dimensions do not guarantee full-size artwork.
2. Slider thumb, yellow fill trail and decorative track were mapped from different start/end coordinates. Some extreme values placed the thumb incorrectly relative to the meaningful track.
3. A decorative HP badge overlaid the beginning of a resource meter. A nominally correct 1% or 5% fill was completely hidden, so changing the input did not visibly change the display.

**Do not solve this by tweaking only the manifest or by adding a passing JSON test.** Correct the source image geometry, shared placement contract, and rendered QA as necessary.

## Author one usable interval per value-controlled control

For native input `v` with `min < max`, compute `t = clamp((v-min)/(max-min), 0, 1)`. Preserve native units and values in host outputs.

- **Meter:** define the *visible, unobstructed* start and end of its data-bearing interior. `fill_extent = t * usable_length`; 0% reveals no fill and 100% reaches the final usable pixel. Decorative borders cannot conceal that range.
- **Slider:** define *thumb center* start and end; the physical thumb is wider than its center-travel interval. Its center must stay within the component and its full visible silhouette inside allowed bounds. The active trail ends at the thumb center, with the same origin and travel interval; no second guessed `from_px` or fill width.
- **Source raster:** isolate fills, tracks, thumbs, badges and rims. Match SVG `viewBox` aspect to canvas output, avoid hidden letterboxing, keep intentional alpha gutters, and inspect the resulting **actual** PNG bounds.
- **Layering:** overlays and ornaments must not hide the data-bearing pixels at low values. If a badge occupies space, allocate the badge its own layout space or explicitly shorten the visual data interval and document it.
- **Rounded ends:** pixel-area coverage may not be exactly linear at 1%, but monotonicity, correct visible endpoints and legibility are mandatory.

The rendering API already supports `clip`, `position_from_input`, `offset_px`, `size_px`, layered compositions, and normalized number inputs. Prefer one geometry definition in the asset generator that derives both `clip` sizing and handle travel. No hard-coded UI-specific renderer or duplicate manifest registry.

## Required acceptance before export

1. Render **every one** of `0, 1, 5, 10, 25, 50, 75, 90, 99, 100` percent (map to the declared native numeric range). Include min/max of any nonzero-start ranges.
2. Compare the *actual canvas pixels*, not just the emitted value or a changing hash. Assert empty at min, visible nonzero fill at 1% or 5%, monotonic active area, approximate halfway coverage at 50%, and full usable extent at max.
3. Measure the handle center at both endpoints, inspect the actual thumb alpha silhouette, assert no unintended clip, and verify trail endpoint matches center at multiple sample values.
4. Inspect **all** visual states and compatible options, including disabled/hover/pressed, against the same geometry.
5. Check badge, frame, mask and glow overlap over the lowest nonzero values. Test with transparent and dark preview backgrounds.
6. Confirm every PNG region and the final ZIP pass the official validator and strict pixel scan. Do not suppress or mislabel crop warnings.
7. Export the final ZIP, reimport **that exact ZIP**, rerun its browser-state cases and attach screenshots + a machine-readable test receipt. Any mismatch is **NEEDS FIXES**, not ready.

**Negative acceptance examples:** a 100% bar stopping early, a 1% bar hidden under a badge, a thumb leaving its legal interval, a visible trail ending beyond the thumb, or a mismatched SVG source aspect must make the release gate fail. Visual-artistic review is still separate from these measurable tests.
