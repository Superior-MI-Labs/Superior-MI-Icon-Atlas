# GitHub Pages publishing

The static site is generated from `manifest.json` and the original art sheets by `tools/build_site.py`. No additional database or server is required.

## First-time publication

1. Upload the complete Icon Atlas source release to the repository, including `manifest.json`, `web/`, `tools/`, `tests/`, and `sheets/`.
2. Configure **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The `Publish Icon Atlas` workflow builds the browser and deploys its generated `site/` folder.
4. Verify the deployment in **Actions** and confirm the live page at https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/.

Do not manually maintain `site/catalog-data.js`; it is derived from the manifest. The browser crops icons from the RGBA atlas and downloads `<manifest-id>.png`, preserving transparency.

## Developer workflow

```bash
python3 tools/build_site.py
python3 -m unittest discover -s tests -p 'test_site.py' -v
python3 -m http.server --directory site 8000
```

Open http://localhost:8000.

## Licensing boundary

Only the independently constructed original starter should be made public by default. Historical v10 mixed-license assets require an explicit separate provenance and license review before import.
