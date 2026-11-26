#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Build the FAD R/Shiny release archive.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

version="$(tr -d '[:space:]' < VERSION)"
if [[ -z "$version" ]]; then
  echo "error: VERSION is empty" >&2
  exit 1
fi

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
root="$stage/FAD"
mkdir -p "$root"
cp -R app.R R VERSION FAD_REFERENCE README.md CHANGELOG.md "$root/"
cp ../LICENSE "$root/"
find "$root" -name '.Rhistory' -delete 2>/dev/null || true

chmod -R a+rX "$root"
mkdir -p dist
zip_name="FAD-R-${version}.zip"
out="$(pwd)/dist"
rm -f "${out}/${zip_name}" "${out}/SHA256SUMS"
( cd "$stage" && zip -qr "${out}/${zip_name}" FAD )
( cd dist
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${zip_name}" > SHA256SUMS
  else
    shasum -a 256 "${zip_name}" > SHA256SUMS
  fi )
echo "Created:"
ls -lh "dist/${zip_name}" dist/SHA256SUMS
cat dist/SHA256SUMS
