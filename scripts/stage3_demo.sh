#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for image in minimal files deep; do
    ./run.sh --vfs "examples/vfs/$image.xml" --startup scripts/stage3.txt
done

