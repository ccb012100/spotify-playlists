#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="$SCRIPT_DIR/albums/all_albums_sorted.tsv"
ARTISTS_DIR="$SCRIPT_DIR/artists_sh"
CHECKOUT_DIR="$ARTISTS_DIR/_check_out"

shopt -s extglob

trim_whitespace() {
    local value="$1"
    value="${value##+([[:space:]])}"
    value="${value%%+([[:space:]])}"
    printf '%s' "$value"
}

rm -rf "$ARTISTS_DIR"
mkdir -p "$ARTISTS_DIR"
mkdir -p "$CHECKOUT_DIR"

# Skip header line, process each row
tail -n +2 "$INPUT_FILE" | while IFS=$'\t' read -r artist album track_count release_date added_at playlist; do
    # Trim whitespace
    artist="$(trim_whitespace "$artist")"
    album="$(trim_whitespace "$album")"
    track_count="$(trim_whitespace "$track_count")"
    release_date="$(trim_whitespace "$release_date")"
    added_at="$(trim_whitespace "$added_at")"
    playlist="$(trim_whitespace "$playlist")"

    # Skip rows with empty artist or album
    if [[ -z "$artist" ]] || [[ -z "$album" ]]; then
        continue
    fi

    # Sanitize names for use as file/directory names (replace / with _) and limit to 200 chars
    safe_artist="${artist//\//_}"
    safe_artist="${safe_artist:0:200}"
    safe_album="${album//\//_}"
    safe_album="${safe_album:0:200}"

    # Ensure artists/<artist>/_unheard/ exists
    if [[ ! -d "$ARTISTS_DIR/$safe_artist" ]]; then
        mkdir -p "$ARTISTS_DIR/$safe_artist/_unheard"
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
        # All other playlists: file goes in artists/<artist>/_unheard/<album>
        mkdir -p "$ARTISTS_DIR/$safe_artist/_unheard"
        album_file="$ARTISTS_DIR/$safe_artist/_unheard/$safe_album"
        if [[ ! -f "$album_file" ]]; then
            touch "$album_file"
        fi
        echo "$full_row" >> "$album_file"
    fi
done

echo "Done processing albums."
