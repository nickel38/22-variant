#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if ./run.sh --vfs examples/vfs/files.xml --startup scripts/stage2_error.txt; then
    echo "Ожидалась ошибка стартового скрипта." >&2
    exit 1
fi

