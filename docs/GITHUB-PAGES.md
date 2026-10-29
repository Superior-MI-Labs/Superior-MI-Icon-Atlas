# Public Icon Atlas browser on GitHub Pages

The public website and installed offline browser use the **same source** (`web/`). `manifest.json` remains the sole icon authority; `tools/build_site.py` regenerates the small browser index and copies only the approved original textures. No API, database, login, runtime server, or NPM build is required.

## Publish

1. The public repository `Superior-MI-Labs/Superior-MI-Icon-Atlas` already exists.
2. Run `bash publish-to-github.sh` from an extracted release; this safely publishes the original-only source files and texture atlas while preserving remote documentation.
3. On GitHub open **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. The included `.github/workflows/pages.yml` validates and builds `site/` on push, then deploys. Inspect the **Actions** tab if deployment fails.

Expected URL after GitHub confirms publication:

`https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/`

Do not advertise this as a live site until GitHub's deployment shows success.

## Browser features

- Search ID, display name, concept and manifest search tags.
- Filter by category, visual style and artwork review state.
- Preview icons on a checkerboard (not part of the export).
- Open an icon for full manifest ID, crop geometry, copyright/license and tags.
- Download exactly one **96×96 transparent PNG**, cropped in the browser from the production atlas with `Canvas`.
- The individual download filename is the icon's exact `id` followed by `.png`, e.g. `icons.original.programming.bug.symbol.png`.
- Optional foreground tint reads the tint mask and black outline images; the downloaded filename is still the icon ID.
- Copy an icon ID or a direct link (`?icon=icons.original.programming.bug.symbol`).

**Security**: No text from the manifest is inserted as HTML. Uploaded assets must pass review before being included in the publicly served manifest. GitHub Pages is a public website and all served artwork can be downloaded.

## Local browser

From a clone:

```bash
python3 tools/build_site.py
python3 -m http.server --directory site 8000
```

Open `http://localhost:8000`. Python is the only build requirement; production rendering/reconstruction is a separate optional pipeline.

`site/index.html` may also open from local files, but some browsers block canvas export or clipboard permissions for `file://` pages. Use the local HTTP server if download or recoloring is blocked. `catalog.html` redirects to the built browser.

## Scaling the library

- Add icons and sheets to `manifest.json` and render their source atlases.
- Run `python3 tools/build_site.py` and `python3 -m unittest discover -s tests -p 'test_site.py' -v`.
- Commit artwork, manifest, sources and browser templates. Do **not** check in generated `site/` (ignored), and do not hand-edit `catalog-data.js`.
- Each new asset must specify an existing sheet, correct pixel crop, tags, variant and rights status. This build intentionally serves **only the original-only starter collection**. The old mixed-license v10 pack is not included.

This packaging avoids a second icon catalog and uses relative paths so the website works under the GitHub Pages project subdirectory.
