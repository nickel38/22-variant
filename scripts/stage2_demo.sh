#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
tmp_vfs="$(mktemp)"
trap 'rm -f "$tmp_vfs"' EXIT
printf 'placeholder' >"$tmp_vfs"
./run.sh --vfs "$tmp_vfs" --startup scripts/stage2_success.txt

