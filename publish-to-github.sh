#!/usr/bin/env bash
# Run as `bash publish-to-github.sh`. Fails only in this child process.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="${SMI_ATLAS_REMOTE:-https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas.git}"
# Reviewed live main head at the beginning of this audit. Refuse to discard later edits.
EXPECTED_HEAD="${SMI_EXPECTED_HEAD:-4a553b2add4afa406e68c66b61dab7f61fb0ebf0}"
LOG="$HOME/Downloads/visual-atlas-v0.13.0-publish.log"
export GIT_PAGER=cat PAGER=cat
mkdir -p "$(dirname "$LOG")"
command -v git >/dev/null || { echo 'ERROR: git is required' >&2; exit 1; }
# Fast safety check before expensive QA. The clone is checked again after QA.
HEAD_NOW="$(git ls-remote --heads "$REMOTE" main | awk '{print $1}')"
if [ "$HEAD_NOW" != "$EXPECTED_HEAD" ]; then
  echo 'STOP: GitHub main changed since this release package was prepared.'
  echo "Expected: $EXPECTED_HEAD"
  echo "Found:    $HEAD_NOW"
  echo 'No files changed. Refresh the package against the new revision.'
  exit 2
fi
command -v python3 >/dev/null || { echo 'ERROR: python3 is required' >&2; exit 1; }
(
  cd "$ROOT"
  bash RUN-ALL.sh

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
  git --no-pager diff --cached --stat
  git -c user.name='Superior MI Labs' -c user.email='superior.mi.labs@gmail.com' commit -m 'test: Visual Atlas v0.13 rendered-state visual QA and AI release gate'
  git push origin main
)
echo 'Published. GitHub Pages workflow will deploy automatically from main.'
echo 'https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/actions'
