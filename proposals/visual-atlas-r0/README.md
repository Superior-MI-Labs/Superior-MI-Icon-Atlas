# Superior MI Visual Atlas — Architecture Proposal R0

Status: **design proposal, not a production release**. This branch does not alter the public Icon Atlas, its existing 2,073 IDs, textures, browser, or GitHub Pages deployment.

## Decision

Preserve the **v0.5.0 root index + authored per-sheet manifests + generated projections**. Extend the resolver to read generalized *visual packs* alongside legacy icon sheets. Do not fork the search engine, create one special renderer per asset category, or treat the browser as a second source of truth.

**Four asset kinds:**
- `region`: reference a source texture and exact pixel rectangle; optional logical frame size, trim offset, normalized pivot, nine-slice insets.
- `sequence`: an ordered list of region/asset references with `default_fps`, frame-specific duration override and playback mode (`once`, `loop`, `pingpong`). **Frame count is derived** from the list, never maintained separately.
- `composition`: an ordered stack of asset references, transform offsets, opacity, tint, blend mode, visibility condition, and optional fraction clip. Can include sequences, state sets, or other compositions.
- `state_set`: stable state names mapping to assets. A composition layer can select a nested state set from a typed input.

These are **asset descriptions**, not an execution language. The host app owns mouse input, physics, gameplay, network effects, event dispatch, and clock scheduling. The preview controller may simulate host-supplied parameters.

## Core contracts

1. Asset ID is stable and independent of atlas position. Preserve legacy IDs; resolve them using an adapter, not a rewritten manifest.
2. Pixel rectangles `[x,y,w,h]` are canonical. A regular 24x8, 96px grid is an optional *authoring shorthand*, never an assumption about generated art.
3. Named animation frame references are authoritative. Source coordinates live in the referenced regions, preventing duplicated frame rectangles. `default_fps` determines duration only when `duration_ms` is omitted.
4. All visual layers are ordered, static JSON references. No JavaScript expressions, embedded HTML, remote resources, user-defined code, or arbitrary shaders in manifests.
5. User inputs are typed (`boolean`, `number`, `enum`). V1 supports exact-value visibility conditions, fraction clipping, and state selection from an enum; arbitrary scriptable logic is deliberately out of scope.
6. All referenced IDs must exist; asset dependency graph must be acyclic. Input bindings must resolve against the composition's declared inputs.
7. Review status, license, attribution and provenance remain separate from semantic descriptions and art quality. Redistribution/export must preserve relevant notices.
8. The one authored pack file owns assets, refs and visual behavior. Runtime index, thumbnails, search index, UI previews and exports are generated artifacts.
9. Repack textures without invalidating stable IDs, keeping logical frame size and pivot stable; test that rotated/trimmed frames remain aligned before enabling rotation packing.
10. Unknown property, invalid rectangle, invalid nine-slice, missing file/hash, bad state, missing dependency, invalid input or reference cycle fails validation.

## GitHub Pages browser and local-first builder

GitHub Pages already hosts a read-only catalog. Evolve its existing browser incrementally:

**Browse**: one search index over both legacy icons and new visual packs. Facets generated from real metadata: type, style, animation, layer count, states, inputs, tintability, resolution, license and review status.

**Inspect**: region preview; sequence playback with step/pause/speed; composition layer visibility; state-switcher; input controls (slider, toggle, enum) generated from manifest definitions.

**Build**: allow user to select assets; assemble a composition; bind states/inputs; preview on canvas; validate through the shared resolver. No new per-widget business logic.

**Export**: browser-produced ZIP with only referenced dependencies, their license notices, a portable pack manifest, and optional PNG frames or flattened states. Use a vetted locally bundled ZIP library. Enforce safe relative paths and image dimension limits. No server is needed to edit or download locally. Publishing shared assets into the official GitHub repository is a separate reviewed contribution, not an anonymous site write.

**Rendering R0**: ordinary RGBA Canvas 2D, ordered layers, source pixel rectangles, pivots, basic blend modes, sequences, state sets, optional nine-slice and fraction clips. Start without WebGL, physics, shaders, or a generic node graph. Never make a second rendering code path exclusively for the browser.

## Examples as contract probes

- `examples/animated-icon.json`: animated pulse layer, static base and independently toggled badge.
- `examples/ui-button.json`: independent normal/hover/pressed/disabled states with nine-slice geometry.
- `examples/health-bar.json`: one numeric value clips a fill layer, with a scalable frame.
- `examples/glass-rain.json`: glass base, crack state set and independently toggled rain sequence.
- `examples/ui-slider.json`: a normalized value drives both a clipped fill and the thumb position; no slider-specific renderer.

These fixtures declare imaginary asset filenames **for schema exploration only**; they are not published artwork or functional previews. Rendering QA requires real textures later.

## Migration / delivery sequence

0. Keep the working Icon Atlas site and v0.5.0 manifests untouched.
1. Merge only validated general schema + fixture tests and add a read-only legacy adapter in the *existing* catalog loader.
2. Add one `region` pack with real artwork and prove search, individual download and arbitrary rectangle cropping.
3. Add `sequence` and `composition` in the same renderer, then prove an animated layered icon.
4. Add `state_set`, typed inputs, nine-slice and fraction clips; prove button, health bar and glass.
5. Make the browser builder export portable ZIPs with dependency closure and deterministic filenames.
6. Expand compatibility exporters (Aseprite-style frame data, Godot nine-patch, CSS/Canvas, game engines) only against actual demand; never put engine-specific fields into the canonical pack.

**Non-goals for R0**: multiplayer editing, cloud database, shader graph, arbitrary scripts, asset marketplace, real-time collaboration, authoring a complete animation editor, full editor migration, or any claim that a reference fixture is production-ready.

## Open design questions requiring measured prototypes

Frame alignment across trimmed artwork, animation transition blending, how independently ticking nested sequences synchronize, nearest vs smooth filtering, whether to support non-uniform nine-slice tiling, and browser memory limits for large image collections. Define contracts using working prototypes, not speculative options.

Sources: [Aseprite slices](https://aseprite.com/docs/slices/), [Godot NinePatchRect](https://docs.godotengine.org/en/latest/classes/class_ninepatchrect.html), [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
