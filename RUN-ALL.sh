#!/usr/bin/env bash
# Reproducible project QA. Installs dependencies only into a private, reusable venv.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export GIT_PAGER=cat PAGER=cat
PY=python3
MODE="${1:-local}"
usage() {
  echo 'Usage: bash RUN-ALL.sh [--ci | --collection SLUG [OUT] | --collection-regressions [OUT]]' >&2
  exit 2
}
case "$MODE" in
  local|--ci) (( $# <= 1 )) || usage ;;
  --collection)
    (( $# >= 2 && $# <= 3 )) || usage
    [[ "$2" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || usage
    [[ -d "examples/$2" && -d "tests/visual-packs/$2" ]] || {
      echo "Unknown collection or no registered visual suite: $2" >&2; exit 2;
    } ;;
  --collection-regressions) (( $# <= 2 )) || usage ;;
  *) usage ;;
esac
if ! "$PY" -c 'import PIL,jsonschema' >/dev/null 2>&1; then
  VENV="${SMI_ATLAS_VENV:-$HOME/.cache/superior-mi/visual-atlas/v0.7-venv}"
  mkdir -p "$(dirname "$VENV")"
  if [ ! -x "$VENV/bin/python" ]; then
    echo 'Creating isolated Python environment (does not change system Python)...'
    if ! python3 -m venv "$VENV"; then
      echo 'ERROR: python3-venv is missing. On Linux Mint run: sudo apt install python3-venv' >&2
      exit 2
    fi
  fi
  PY="$VENV/bin/python"
  if ! "$PY" -c 'import PIL,jsonschema' >/dev/null 2>&1; then
    echo 'Installing Pillow and jsonschema in the isolated environment...'
    "$PY" -m pip install --disable-pip-version-check -r requirements-test.txt || {
      echo 'ERROR: Dependency installation failed. Check internet access and requirements-test.txt.' >&2
      exit 2
    }
  fi
fi
# Registered collection suites are independent of the global regression gate.
# Both lanes use the same scenario files and the same browser renderer.
if [[ "$MODE" == --collection || "$MODE" == --collection-regressions ]]; then
  if ! "$PY" -c 'import playwright' >/dev/null 2>&1; then
    echo "Browser QA requires: $PY -m pip install playwright; $PY -m playwright install chromium" >&2
    exit 2
  fi
  shopt -s nullglob
  if [[ "$MODE" == --collection ]]; then
    SLUG="$2"
    SUITES=(tests/visual-packs/"$SLUG"/*.json)
    (( ${#SUITES[@]} > 0 )) || { echo "No visual suites for $SLUG" >&2; exit 2; }
    OUT="${3:-$(mktemp -d)}"
  else
    SUITES=(tests/visual-packs/*/*.json)
    (( ${#SUITES[@]} > 0 )) || { echo "No registered collection suites" >&2; exit 2; }
    OUT="${2:-$(mktemp -d)}"
  fi
  mkdir -p "$OUT"
  OUT="$(cd "$OUT" && pwd)"
  if [[ -n "$(ls -A "$OUT")" ]]; then
    echo 'Use a fresh, empty QA output directory' >&2; exit 2
  fi
  if [[ "$MODE" == --collection ]]; then
    ARCHIVE="$OUT/$SLUG.zip"
    "$PY" tools/build_site.py --collection "$SLUG" --out "$ARCHIVE"
    "$PY" tools/qualify_asset_zip.py "$ARCHIVE" --out "$OUT/pixels"
  fi
  for spec in "${SUITES[@]}"; do
    slug="$(basename "$(dirname "$spec")")"
    suite="$(basename "$spec" .json)"
    echo ">>> Collection $slug / $suite"
    if [[ "$MODE" == --collection ]]; then
      "$PY" tests/browser_visual_matrix.py --spec "$spec" --archive "$ARCHIVE" --out "$OUT/visual/$slug/$suite"
    else
      "$PY" tests/browser_visual_matrix.py --spec "$spec" --out "$OUT/$slug/$suite"
    fi
  done
  echo "COLLECTION SCENARIOS PASS: $OUT"
  if [[ "$MODE" == --collection ]]; then
    echo 'Scoped structural, pixel and registered browser checks only; full regression, creator-specific acceptance, artistic review and publication NOT established.'
  fi
  exit 0
fi
"$PY" atlasctl.py validate
time "$PY" atlasctl.py validate --deep
# The Python runner builds the site once and shares that exact artifact.
time "$PY" -m tests.run_qualification
"$PY" tools/validate_visual_pack.py web/demo/starter-pack.zip
"$PY" tools/validate_visual_pack.py web/demo/potions-collection.zip
"$PY" tools/validate_visual_pack.py site/demo/interactive-hud.zip
"$PY" tools/ai_acceptance.py site/demo/interactive-hud.zip --acceptance examples/acceptance/interactive-hud.json --out "${TMPDIR:-/tmp}/smi-visual-atlas-hud-acceptance"
"$PY" tools/qualify_asset_zip.py web/demo/potions-collection.zip --out "${TMPDIR:-/tmp}/smi-visual-atlas-potions-qa"
"$PY" tools/ai_acceptance.py site/demo/character-animations.zip --acceptance examples/acceptance/character.json --out "${TMPDIR:-/tmp}/smi-visual-atlas-character-acceptance"
"$PY" tools/ai_acceptance.py web/demo/potions-collection.zip --acceptance examples/acceptance/potion.json --out "${TMPDIR:-/tmp}/smi-visual-atlas-potion-acceptance"
"$PY" tools/ai_acceptance.py site/demo/minimal-white-tech.zip --acceptance examples/minimal-white-tech/acceptance.json --out "${TMPDIR:-/tmp}/smi-white-tech-acceptance"
if command -v node >/dev/null 2>&1; then
  for f in web/*.js; do node --check "$f"; done
  for test in tests/*.cjs; do node "$test"; done
elif [ "$MODE" = "--ci" ]; then
  echo 'ERROR: Node is required for CI qualification' >&2; exit 2
else echo 'WARNING: Node tests unavailable (Node not installed). GitHub CI will run these tests.'; fi
printf '\nPASS: All locally available validations. Run: bash RUN-LOCALLY.sh\n'
