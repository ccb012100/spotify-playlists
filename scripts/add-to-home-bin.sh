#!/usr/bin/env bash
set -eou pipefail

repo=$(dirname -- "$(readlink -f -- "$0")")

ln -s "$repo"/../dbsearch.py "$HOME"/bin/playlist-dbsearch.py
ln -s "$repo"/../search.sh "$HOME"/bin/playlist-search.sh