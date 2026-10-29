#!/usr/bin/env bash
# Start the Visual Atlas static builder entirely on this machine; Ctrl+C stops.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8000}"
cd "$ROOT"
command -v python3 >/dev/null || { echo 'Install Python 3 to run the local builder.' >&2; exit 1; }
python3 tools/build_site.py
printf '\nVisual Atlas Builder: http://127.0.0.1:%s/builder.html\n' "$PORT"
printf 'Icon Gallery:        http://127.0.0.1:%s/\n' "$PORT"
printf 'No account or internet required. Local browser files stay local. Ctrl+C to stop.\n\n'
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT/site"
