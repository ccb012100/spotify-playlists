#!/usr/bin/env bash
set -Eeou pipefail
repo=$(dirname -- "$(readlink -f -- "$0")")

ln -s "$repo"/albums "$HOME"/bin/