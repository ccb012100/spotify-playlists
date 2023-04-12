#!/usr/bin/env bash
set -euo pipefail

sqlite3 --readonly "$HOME/playlister.db" ".read get_starred_albums.sql"
# find duplicates and print every duplicate line
# source: https://unix.stackexchange.com/a/225419
awk -F ',' 'n=x[$1]{print n"\n"$0;} {x[$1]=$0;}' starred_playlist_albums.csv >duplicates.csv
