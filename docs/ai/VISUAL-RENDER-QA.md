# Rendered-state QA: one reusable browser test for any asset kind

Use this **after** ZIP validation, per-region pixel scans and the creator-specific acceptance JSON. It checks **actual Canvas output** from the Visual Atlas builder, not merely JSON structure. It cannot prove semantic accuracy, art quality, natural motion, licensing, or correct artistic alignment.

## Run

```bash
python3 -m pip install -r requirements-test.txt playwright
python3 -m playwright install chromium   # only if no system Chromium is installed
python3 tools/build_site.py
python3 tests/browser_visual_matrix.py \
  --spec tests/visual-scenarios.json --out /tmp/visual-render-QA
```

For an external candidate, pass `--archive /path/to/candidate.zip` (all cases must use the same safe pack label). This imports the exact bytes, without copying the pack into source or publishing it. Prefer the existing acceptance command with `--visual-spec` for a single combined receipt. Each browser case records the ZIP SHA-256, asset ID and covered samples. Missing browser evidence is not a PASS.

By default, the runner uses `/usr/bin/chromium` when present, otherwise Playwright's installed Chromium. It injects the built JS and ZIP bytes without a server or network. A nonzero exit means a failed check or a render that couldn't be performed.

## Collection regression suites

Keep the shared `tests/visual-scenarios.json` baseline intact. Put new collection-specific regression specifications in `tests/visual-packs/<collection-slug>/<suite>.json`, using the same existing schema and runner. Each file contains 1–40 cases, with unique IDs and a matching local ZIP basename. CI runs every such file and archives its report. For collections needing more than 40 cases, add further bounded suites in the same collection directory.

## Author a new case

Copy a case from [`tests/visual-scenarios.json`](../../tests/visual-scenarios.json) and replace the pack name, entry/asset, sample controls, times, and assertions. **Assertions must follow the creator's request**, not a blanket requirement that every frame differ.

- GUI/slider: 0%, 50%, 100% visibly increase fill; outputs preserve raw values.
- Animated character: idle differs from walk; walk frames advance; a loop repeats the starting frame. Inspect neighboring frames and seams *by eye*.
- Layered rain/glass: cracks differ from intact glass; enabling rain changes the overlay; time advances rain.
- Potion/GUI presets: Health, Mana, Poison visually differ; animated Mana advances.
- Unchanged parts: use a `same` assertion to verify inputs that shouldn't affect appearance.

The versioned JSON format accepts `inputs`, `state`, `preset`, and `time_ms`; assertions `different`, `same`, `green_increases`, `output_equals` and `changed_area_fraction`. The different/same checks compare decoded transparent RGBA pixels, not the checkerboard CSS behind a canvas. Choose pixel thresholds deliberately. A difference alone does not prove increasing fill or correct position. Specify semantic pixel/geometry checks where relevant, including all ten numeric samples from the GUI value guide; record manual checks or gaps explicitly. Each declared case is scoped evidence, not complete coverage of every asset. The green-specific assertion is **not universal**; use it only for known green test art.

The runner saves PNG evidence for every sample and a report JSON with per-assertion PASS/FAIL. CI uploads that evidence and **blocks GitHub Pages deployment when visual cases fail**. If the local browser is unavailable, disclose NOT RUN in the handoff; the mandatory CI gate still applies to public releases.

## Why this gate exists

The first interactive energy meter passed JSON validation while hiding its fill and treating 0–100 input values as 0–1. A manifest can be syntactically valid and visually wrong.

**Do not overclaim:** distinct frames do not prove good animation, natural motion, character identity, correct pivot, or seamless motion at native FPS. Creator-specific visual review remains mandatory.

`bash RUN-ALL.sh --ci` is the same structural/Node gate used by Pages; CI fails if Node is unavailable. The visual matrix targets stable input, slot and preset identifiers, applying presets before sample overrides. Private fixtures are supplied through a test-only catalog using the same production Builder loader. After pruning, CI also runs `python3 tests/browser_catalog_smoke.py --published-only` against the actual deployable files.

### Proportional fill regression

For a stationary meter whose only changing pixels are the fill, use `changed_area_fraction` with ordered sample/fraction pairs from 0 to 1 (for example `{ "sample": "v50", "fraction": 0.5 }`). It measures actual changed pixels relative to the empty frame and full-frame change, requires strict growth including low-end values, and checks the expected fraction within `max_fraction_error` (default 0.04, maximum 0.1). Use `output_equals` to verify raw values. This is color-independent, but not suitable for moving thumbs, animated backgrounds, or changing canvas size: use other geometry/state assertions for those. It does not prove absolute fill geometry or artwork quality. Each report records the explicit sample controls and scope; untested assets/inputs are not qualified by a passing representative case.

**Loop timing regression:** fractional default frame periods (e.g. 12 FPS) previously accumulated floating-point drift, selecting the last frame at the exact one-second loop boundary. The shared renderer now derives cumulative boundaries from explicit millisecond holds plus the count of default frames. Keep exact-period and just-before-period tests for fractional FPS and mixed holds; do not relax loop-equality assertions to hide timing errors.
