#!/usr/bin/env bash
# Only the qualified main-branch workflow calls this. No force push or pruning.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
site="$(realpath "$1")"
branch=atlas-archive-retention
store="$(mktemp -d)"
rmdir "$store"
cleanup() { git worktree remove --force "$store" >/dev/null 2>&1 || true; }
trap cleanup EXIT
bootstrap=()
status=0
git ls-remote --exit-code --heads origin "refs/heads/$branch" >/dev/null || status=$?
case "$status" in
  0) git fetch --no-tags origin "refs/heads/$branch"
     git worktree add --detach "$store" FETCH_HEAD ;;
  2) git worktree add --detach --no-checkout "$store" HEAD
     git -C "$store" switch --orphan "$branch"
     bootstrap=(--bootstrap) ;;
  *) echo "Could not inspect retention branch; refusing to bootstrap" >&2; exit "$status" ;;
esac
python3 tools/retain_archives.py "$site" "$store/sha256" "${bootstrap[@]}"
git -C "$store" add -- sha256
# Existing archived paths may never change or disappear.
if [[ -n "$(git -C "$store" diff --cached --name-only --diff-filter=CDMRTUXB)" ]]; then
  echo "Retention history is append-only" >&2
  exit 1
fi
if ! git -C "$store" diff --cached --quiet; then
  git -C "$store" -c user.name='github-actions[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' commit -m "Retain qualified Atlas archives for $GITHUB_SHA"
  git -C "$store" push origin "HEAD:refs/heads/$branch"
fi
