#!/usr/bin/env bash
# Run as `bash publish-to-github.sh`. Fails only in this child process.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE='https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas.git'
# Reviewed live main head at the beginning of this audit. Refuse to discard later edits.
EXPECTED_HEAD='e95f979a82c32a3f77216148bff47432ebf86837'
LOG="$HOME/Downloads/icon-atlas-v0.5.0-publish.log"
mkdir -p "$(dirname "$LOG")"
command -v git >/dev/null || { echo 'ERROR: git is required' >&2; exit 1; }
command -v python3 >/dev/null || { echo 'ERROR: python3 is required' >&2; exit 1; }
(
  cd "$ROOT"
  python3 atlasctl.py validate
  python3 tools/build_site.py
  if python3 -c 'from PIL import Image' >/dev/null 2>&1; then
    python3 atlasctl.py validate --deep
    python3 -m unittest discover -s tests -p 'test_site.py' -v
  else
    echo 'NOTE: Pillow not installed locally. Quick validation passed; CI will run deep pixel checks.'
  fi
  if command -v node >/dev/null; then node --check web/app.js && node tests/browser-search.cjs; fi
) 2>&1 | tee "$LOG"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf '\nFetching the existing GitHub repository...\n'
git clone -q --single-branch --branch main "$REMOTE" "$TMP/repo" || { echo "Clone failed; log: $LOG"; exit 1; }
ACTUAL="$(git -C "$TMP/repo" rev-parse HEAD)"
if [ "$ACTUAL" != "$EXPECTED_HEAD" ]; then
  echo 'STOP: GitHub main changed since this package was prepared.'
  echo "Expected: $EXPECTED_HEAD"
  echo "Found:    $ACTUAL"
  echo 'No files changed; ask for a refreshed patch to reconcile the newer work.'
  exit 2
fi
if [ -n "$(git -C "$TMP/repo" status --porcelain)" ]; then echo 'STOP: Clone not clean';exit 3;fi
# Full audited release replacement only after verifying exact known old branch head.
find "$TMP/repo" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf -- {} +
cp -a "$ROOT"/. "$TMP/repo"/
rm -rf "$TMP/repo/site"
find "$TMP/repo" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$TMP/repo" -type f -name '*.pyc' -delete
(
  cd "$TMP/repo"
  git add -A
  git diff --cached --check
  if git diff --cached --quiet; then echo 'Already current; nothing to publish.';exit 0;fi
  git diff --cached --stat
  git -c user.name='Superior MI Labs' -c user.email='superior.mi.labs@gmail.com' commit -m 'refactor: sheet-owned manifests, visual search, semantic curation v0.5.0'
  git push origin main
)
echo 'Published. GitHub Pages workflow will deploy automatically from main.'
echo 'https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/actions'
