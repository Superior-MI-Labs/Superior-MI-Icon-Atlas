#!/usr/bin/env bash
# Reproducible project QA. Installs dependencies only into a private, reusable venv.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export GIT_PAGER=cat PAGER=cat
PY=python3
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
"$PY" atlasctl.py validate
"$PY" tools/build_site.py
"$PY" atlasctl.py validate --deep
"$PY" -m unittest discover -s tests -p 'test_*.py' -v
"$PY" tools/validate_visual_pack.py web/demo/starter-pack.zip
"$PY" tools/validate_visual_pack.py web/demo/potions-collection.zip
"$PY" tools/qualify_asset_zip.py web/demo/potions-collection.zip --out "${TMPDIR:-/tmp}/smi-visual-atlas-potions-qa"
if command -v node >/dev/null 2>&1; then
  for f in web/app.js web/builder.js web/timeline-core.js web/collection-core.js web/bag-store.js web/interaction-core.js web/slot-core.js; do node --check "$f"; done
  node tests/browser-search.cjs
  node tests/builder-contract.cjs
  node tests/timeline-core.cjs
  node tests/collections-interaction.cjs
  node tests/slots-presets.cjs
else echo 'WARNING: Node tests unavailable (Node not installed). GitHub CI will run these tests.'; fi
printf '\nPASS: All locally available validations. Run: bash RUN-LOCALLY.sh\n'
