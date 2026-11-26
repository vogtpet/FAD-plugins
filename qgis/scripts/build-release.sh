#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Build the FAD QGIS plugin archive.
#
# The archive contains the plugin folder fad/ at its root so that it can be
# installed with QGIS: Plugins -> Manage and Install Plugins -> Install from
# ZIP. Documentation and licenses are placed inside that folder.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

version="$(tr -d '[:space:]' < VERSION)"
if ! grep -q "^version=${version}$" fad/metadata.txt; then
  echo "error: fad/metadata.txt does not match VERSION (${version})" >&2
  exit 1
fi
if ! grep -q "^PLUGIN_VERSION = \"${version}\"$" fad/fad.py; then
  echo "error: PLUGIN_VERSION in fad/fad.py does not match VERSION (${version})" >&2
  exit 1
fi

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

cp -R fad "$stage/"
find "$stage/fad" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$stage/fad" -name '*.pyc' -delete 2>/dev/null || true

cp README.md CHANGELOG.md VERSION FAD_REFERENCE "$stage/fad/"
cp ../LICENSE "$stage/fad/"

chmod -R a+rX "$stage"

mkdir -p dist
zip_name="FAD-QGIS-${version}.zip"
out="$(pwd)/dist"
rm -f "${out}/${zip_name}" "${out}/SHA256SUMS"
( cd "$stage" && zip -qr "${out}/${zip_name}" fad )

( cd dist
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${zip_name}" > SHA256SUMS
  else
    shasum -a 256 "${zip_name}" > SHA256SUMS
  fi )

echo "Created:"
ls -lh "dist/${zip_name}" dist/SHA256SUMS
cat dist/SHA256SUMS
