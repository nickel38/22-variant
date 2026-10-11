#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
tmp_vfs="$(mktemp)"
trap 'rm -f "$tmp_vfs"' EXIT
printf 'placeholder' >"$tmp_vfs"
if ./run.sh --vfs "$tmp_vfs" --startup scripts/stage2_error.txt; then
    echo "Ожидалась ошибка стартового скрипта." >&2
    exit 1
fi

