#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Build the FAD ArcGIS release archive.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

version="$(tr -d '[:space:]' < VERSION)"
if ! grep -q "PLUGIN_VERSION = \"${version}\"" FAD.pyt; then
  echo "error: PLUGIN_VERSION in FAD.pyt does not match VERSION (${version})" >&2
  exit 1
fi

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
root="$stage/FAD-ArcGIS"
mkdir -p "$root"
cp FAD.pyt fad_core.py fad_stats.py fad_tags.py frag_colormap.txt \
   VERSION FAD_REFERENCE README.md CHANGELOG.md "$root/"
cp ../LICENSE "$root/"
find "$root" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

chmod -R a+rX "$root"
mkdir -p dist
zip_name="FAD-ArcGIS-${version}.zip"
out="$(pwd)/dist"
rm -f "${out}/${zip_name}" "${out}/SHA256SUMS"
( cd "$stage" && zip -qr "${out}/${zip_name}" FAD-ArcGIS )
( cd dist
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${zip_name}" > SHA256SUMS
  else
    shasum -a 256 "${zip_name}" > SHA256SUMS
  fi )
echo "Created:"
ls -lh "dist/${zip_name}" dist/SHA256SUMS
cat dist/SHA256SUMS
