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

By default, the runner uses `/usr/bin/chromium` when present, otherwise Playwright's installed Chromium. It injects the built JS and ZIP bytes without a server or network. A nonzero exit means a failed check or a render that couldn't be performed.

## Author a new case

Copy a case from [`tests/visual-scenarios.json`](../../tests/visual-scenarios.json) and replace the pack name, entry/asset, sample controls, times, and assertions. **Assertions must follow the creator's request**, not a blanket requirement that every frame differ.

- GUI/slider: 0%, 50%, 100% visibly increase fill; outputs preserve raw values.
- Animated character: idle differs from walk; walk frames advance; a loop repeats the starting frame. Inspect neighboring frames and seams *by eye*.
- Layered rain/glass: cracks differ from intact glass; enabling rain changes the overlay; time advances rain.
- Potion/GUI presets: Health, Mana, Poison visually differ; animated Mana advances.
- Unchanged parts: use a `same` assertion to verify inputs that shouldn't affect appearance.

The versioned JSON format accepts `inputs`, `state`, `preset`, and `time_ms`; assertions `different`, `same`, `green_increases` and `output_equals`. The different/same checks compare decoded transparent RGBA pixels, not the checkerboard CSS behind a canvas. Choose pixel thresholds deliberately. The green-specific assertion is **not universal**; use it only for known green test art.

The runner saves PNG evidence for every sample and a report JSON with per-assertion PASS/FAIL. CI uploads that evidence and **blocks GitHub Pages deployment when visual cases fail**. If the local browser is unavailable, disclose NOT RUN in the handoff; the mandatory CI gate still applies to public releases.

## Why this gate exists

The first interactive energy meter passed JSON validation while hiding its fill and treating 0–100 input values as 0–1. A manifest can be syntactically valid and visually wrong.

**Do not overclaim:** distinct frames do not prove good animation, natural motion, character identity, correct pivot, or seamless motion at native FPS. Creator-specific visual review remains mandatory.
