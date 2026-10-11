#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
printf 'ls "$HOME"\ncd "Мои документы"\nunknown\nexit\n' | ./run.sh

