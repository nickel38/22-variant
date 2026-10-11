#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
./run.sh --vfs examples/vfs/files.xml --startup scripts/stage2_success.txt

