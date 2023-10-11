#!/usr/bin/env bash
set -eou pipefail

repo=$(dirname -- "$(readlink -f -- "$0")")

ln -s "$repo"/../search.py "$HOME"/bin/playlist-search.py
ln -s "$repo"/../search.sh "$HOME"/bin/playlist-search.sh