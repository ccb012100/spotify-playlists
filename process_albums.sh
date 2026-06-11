#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="$SCRIPT_DIR/albums/all_albums_sorted.tsv"
ARTISTS_DIR="$SCRIPT_DIR/artists"
CHECKOUT_DIR="$SCRIPT_DIR/check out"

mkdir -p "$ARTISTS_DIR"
mkdir -p "$CHECKOUT_DIR"

# Skip header line, process each row
tail -n +2 "$INPUT_FILE" | while IFS=$'\t' read -r artist album track_count release_date added_at playlist; do
    # Sanitize names for use as file/directory names (replace / with _)
    safe_artist="${artist//\//_}"
    safe_album="${album//\//_}"

    # Ensure artists/<artist>/unheard/ exists
    if [[ ! -d "$ARTISTS_DIR/$safe_artist" ]]; then
        mkdir -p "$ARTISTS_DIR/$safe_artist/unheard"
    fi

    # Reconstruct the full row
    full_row="${artist}	${album}	${track_count}	${release_date}	${added_at}	${playlist}"

    if [[ "$playlist" == Starred* ]]; then
        # Starred playlist: file goes in artists/<artist>/<album>
        album_file="$ARTISTS_DIR/$safe_artist/$safe_album"
        if [[ ! -f "$album_file" ]]; then
            touch "$album_file"
        fi
        echo "$full_row" >> "$album_file"

    elif [[ "$playlist" == *"check out"* ]]; then
        # Check out playlist: file goes in "check out"/<artist>/<album>
        if [[ ! -d "$CHECKOUT_DIR/$safe_artist" ]]; then
            mkdir -p "$CHECKOUT_DIR/$safe_artist"
        fi
        album_file="$CHECKOUT_DIR/$safe_artist/$safe_album"
        touch "$album_file"
        echo "$full_row" >> "$album_file"

    else
        # All other playlists: file goes in artists/<artist>/unheard/<album>
        mkdir -p "$ARTISTS_DIR/$safe_artist/unheard"
        album_file="$ARTISTS_DIR/$safe_artist/unheard/$safe_album"
        if [[ ! -f "$album_file" ]]; then
            touch "$album_file"
        fi
        echo "$full_row" >> "$album_file"
    fi
done

echo "Done processing albums."
