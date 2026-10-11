#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
./run.sh --vfs examples/vfs/files.xml --startup scripts/stage4_success.txt
if ./run.sh --vfs examples/vfs/files.xml --startup scripts/stage4_error.txt; then
    echo "Ожидалась ошибка ls." >&2
    exit 1
fi

