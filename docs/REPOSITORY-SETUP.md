# GitHub publication setup

Proposed repository: **Superior-MI-Labs/Superior-MI-Icon-Atlas**

Description: **An extensible, searchable, source-attributed icon atlas for visual programming, computing, science, games, media and real-world systems.**

Suggested topics: `icons`, `icon-atlas`, `spritesheet`, `svg`, `texture-atlas`, `visual-programming`, `open-source`, `python`, `assets`, `superior-mi-labs`.

**Initial visibility:** Public, once the original-starter release is reviewed. License: Apache-2.0 (root `LICENSE` is included). **Do not pick a separate license or initialize README on the GitHub New Repository form** if uploading this prepared source; that avoids unnecessary merge conflicts.

The connected GitHub app currently cannot create repositories. The authorized GitHub account has admin privileges on some existing org repositories, but this does not itself prove organization repo-create permission. Creation requires the organization UI or an authenticated GitHub CLI session with the relevant permission.

## CLI method from the extracted directory

```bash
cd "$HOME/Projects/Superior Mind/Superior-MI-Icon-Atlas"
git init -b main
git add .
git commit -m "Initial original-only Icon Atlas starter"
gh auth login
gh repo create Superior-MI-Labs/Superior-MI-Icon-Atlas \
  --public --source . --remote origin --push \
  --description "An extensible, searchable original icon atlas for Superior MI Labs"
```

If the repo was already created empty in the GitHub UI, replace the final command with:

```bash
git remote add origin https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas.git
git push -u origin main
```

Do not push any older v10 `sheets/` directories or source fonts into this repository until rights and provenance reviews are completed.

## Release strategy

Keep the generator, SVG source and authoritative manifest in Git; publish compiled sheet bundles as versioned GitHub Releases. Do not keep repeatedly committing tens or hundreds of megabytes of generated texture revisions. No Git LFS dependency is needed for this small starter.

## Website deployment

See [`GITHUB-PAGES.md`](GITHUB-PAGES.md). The `pages.yml` workflow deploys the manifest-derived static browser; no manually maintained `gh-pages` branch or duplicate asset registry. Under Settings → Pages select **GitHub Actions** for the publishing source.
