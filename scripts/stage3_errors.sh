#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if ./run.sh --vfs examples/vfs/missing.xml; then
    echo "Ожидалась ошибка отсутствующего VFS." >&2
    exit 1
fi
if ./run.sh --vfs examples/vfs/invalid.xml; then
    echo "Ожидалась ошибка формата VFS." >&2
    exit 1
fi

