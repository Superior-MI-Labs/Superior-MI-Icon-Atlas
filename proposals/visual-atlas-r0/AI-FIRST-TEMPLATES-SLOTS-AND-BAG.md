# Visual Atlas — AI-first template and pack workflow (Design RFC)

**Status:** proposal for v0.8+, not a production feature. Public v0.7 behavior remains unchanged.

## Product promise

**Tell an AI what you want → receive ZIP → drop into browser → preview everything with manifest defaults → choose only compatible presets → export ZIP.**

Do **not** turn the normal experience into a professional animation editor. The timeline, layers, crop geometry, and transform controls remain under a collapsed **Advanced** panel for diagnosis and repair. The default UI needs only *Browse, My Bag, Templates, Preview, Export*.

The website is a static GitHub Pages app. No login, database server, processing service or private asset uploads are required.

## Roles of the manifest

The single authored pack manifest describes:
- `textures`: file paths, dimensions, alpha, optional checksums
- `assets`: stable IDs, kinds (region/sequence/composition/state_set), source regions, animation timing, layers, states, typed controls
- `interfaces`: optional **versioned slot contracts** for interchangeable visual pieces
- `slots`: optional choices on a composition, with a compatible contract, default and allowed choices
- `presets`: named parameter/slot selections for one composition, e.g. Health, Mana, Poison, Empty
- `presentation`: optional entry asset, title, preview stage, and whether animation should autoplay

**Important:** templates are ordinary compositions plus slots and presets, **not** a fifth renderer kind. A completed asset may have no slots; it still loads automatically. Frame count is derived from `frames`; FPS/time comes from its sequence. Pixel coordinates are attached to the referenced regions, never copied into every sequence frame.

## Versioned compatibility contracts

Example: `smi.slot.potion.round64.fluid/1`. A contract defines **logical canvas size, local origin/pivot, alignment and optional clipping mask**. Each candidate fluid asset declares `implements` IDs. A composition slot declares `accepts`, `default`, and an explicit `options` list.

Compatibility algorithm:
1. Verify the exact interface ID **including its version**. Similar names are *not* equivalent.
2. Verify logical dimensions, anchor/pivot and mask requirements; render under the slot's clipping bounds.
3. Verify the candidate asset is reachable and its dependency graph is valid.
4. Only show assets explicitly listed by the pack as supported options by default. Assets from other packs can be marked **suggested** when the contract matches, but are not silently certified visually or substituted.
5. Resolve nested states and animated sequences through the existing asset renderer. Swapping a static green liquid with an animated blue liquid changes only the slot reference, not the bottle/glass/framing assets.
6. Prevent cycles, missing dependencies, incompatible geometry and undefined controls **before** display or export.

`implements` is a capability claim, not proof that two textures actually fit. AI-generated ZIPs remain **candidate** until validated and previewed. An explicit compatibility declaration plus machine checks beats guessing from tags, category or shared texture sheet. Same sheet is neither required nor sufficient for compatibility.

## Minimal template example

A potion pack can contain one bottle base, an overlay/highlight, multiple compatible fluid regions/sequences and an optional bubble sequence. The composition has `slots.fluid`. The manifest defines a `Health` preset selecting the green liquid, a `Mana` preset selecting animated blue liquid, and a `Poison` preset selecting purple liquid. Layer order is base → fluid → highlights → cap/label. A non-potion product can use the exact same contract mechanism for health bars, hoverable buttons, indicators, banners, equipment swaps, and animated icon overlays.

Slots are interchangeable **referenced assets**; presets are **saved selections of slot IDs and typed input values**. They do not duplicate textures or require an alternate rendering engine.

## Builder interaction

**Browse:** public approved assets, categorized and filterable. Public icons remain first-class entries.

**Templates:** curated starter pack examples: icon with badge, button states, liquid meter, potion bottle, glass/weather overlay, sprite animation, web banner. Clicking a template creates a local working copy; no account needed.

**My Bag:** a card per privately imported ZIP with its filename, pack ID, version, size, license, number of assets, import status, and timestamp. Keep data in IndexedDB **with user consent and a visible stored-locally indicator**; use session-only storage when blocked. Provide Open, Remove, Export and Clear All. Avoid silently persisting sensitive customer assets. On every reopen, revalidate the pack before activating it. A ZIP must not overwrite a different pack with the same ID/version without explicit replacement.

**Drop zone:** drag-and-drop ZIP anywhere on the builder, show validation result, add a Bag card, and select the pack's default composition or `presentation.entry`. Individual loose files remain an advanced import path.

**Preview:** auto-render manifest default state and animation. Show only manifest-declared meaningful controls, e.g. Fluid [Health/Mana/Poison], Damage [Intact/Cracked], Rain [On/Off]. No need to expose arbitrary layer transforms to ordinary visitors.

**Export:** produce a self-contained ZIP with the root composition, dependency closure (including **all allowed slot options** unless user requests flattened single preset), textures, manifest, license and source notices, and a basic readme. For embedded art, also support PNG states/frames. Store and reproduce versioned dependencies; never export broken references.

**Advanced:** optional timeline, frame crop inspection, layer editor and JSON diagnostics. This is not the main user journey.

## AI handoff link

Create a stable, versioned `/ai/visual-pack-v1.html` with:
- Current schema and safe ZIP structure, one example per supported template
- Instructions to generate the original images and manifest together
- Pixel/anchor, texture size, naming, dependencies and slot-compatibility rules
- `RUN-ALL` local validator and common error examples
- The required deliverable: ZIP containing manifest + texture files + attribution/rights metadata, no remote links
- The public builder URL and one instruction: “Drop the ZIP here to preview it.”

A user can simply give this URL to an AI assistant, describe the result, then import the AI's output. The guide must version the contract so a later schema change does not break older chat instructions.

## Safety and privacy requirements

- No arbitrary JS, expressions, CSS, SVG scripting, HTML, external texture URLs, shaders or executable plugins in manifests.
- Reject `../`, absolute paths, duplicate ZIP member paths, symlinks, encrypted archives, unexpected file types, decompression bombs, excessive frame counts and huge textures.
- Parse and validate locally; never auto-run code from imported packs.
- Strict upper limits on browser decoded image pixels, not only compressed ZIP size; dispose/revoke images and textures after removal.
- Persistent Bag uses local browser storage (IndexedDB) where supported, with eviction/quota warnings. **It is not an unlimited, synced cloud account.** Browser-data clearing or different devices will lose saved Bag content unless users export backups.
- Licenses are per asset/pack. CC0 only for rights-cleared source assets; unspecified rights cannot be silently overridden.

## Testing gates

1. Existing 2,073 icon IDs and pixels unchanged.
2. AI example pack opens directly to its declared entry, with no manual layer editing.
3. Static/animated fluids for a potion pass compatibility matching; incompatible aspect/anchor, unknown interface or wrong version are rejected.
4. Preset selection changes only the intended layer(s); non-swapped base/outline pixels remain stable.
5. Bag ZIPs survive reload when persistence is enabled; imports remain local; remove/clear actually delete stored data.
6. ZIP export then reimport produces identical manifest controls, compatible choices, and a pixel-identical preview at a fixed time.
7. Path traversal, inflated ZIP size, duplicate ID, missing file, undefined slot, invalid state and cycle all fail visibly.
8. Existing site runs on GitHub Pages and from the downloaded repository; no external CDN is required.

## Migration strategy

A new versioned extension to `smi-visual-pack/1` is backward-compatible when `interfaces`, `slots`, `presets` and `presentation` are optional. Validate new fields with JSON Schema **and** semantic graph checks. Keep production v0.7 packs compatible. First implement the validator and real potion sample pack, then an automatic preview/preset UI, then persistent Bag. Add professional editing features only if the simple workflow cannot express a use case.
