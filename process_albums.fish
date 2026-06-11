#!/usr/bin/env fish

set SCRIPT_DIR (cd (dirname (status filename)); and pwd)
set INPUT_FILE "$SCRIPT_DIR/albums/all_albums_sorted.tsv"
set ARTISTS_DIR "$SCRIPT_DIR/artists"
set CHECKOUT_DIR "$ARTISTS_DIR/_check_out"

mkdir -p "$ARTISTS_DIR"
mkdir -p "$CHECKOUT_DIR"

# Skip header line, process each row
set -l line_num 0
while read -l line
    set line_num (math $line_num + 1)
    if test $line_num -eq 1
        continue
    end

    # Split on tab
    set -l fields (string split \t "$line")
    set -l artist (string trim $fields[1])
    set -l album (string trim $fields[2])
    set -l track_count (string trim $fields[3])
    set -l release_date (string trim $fields[4])
    set -l added_at (string trim $fields[5])
    set -l playlist (string trim $fields[6])

    # Skip rows with empty artist or album
    if test -z "$artist" || test -z "$album"
        continue
    end

    # Sanitize names for use as file/directory names (replace / with _) and limit to 200 chars
    set -l safe_artist (string replace -a '/' '_' "$artist" | string sub -l 200)
    set -l safe_album (string replace -a '/' '_' "$album" | string sub -l 200)

    # Ensure artists/<artist>/_unheard/ exists
    if not test -d "$ARTISTS_DIR/$safe_artist"
        mkdir -p "$ARTISTS_DIR/$safe_artist/_unheard"
    end

    # Reconstruct the full row
    set -l full_row "$artist\t$album\t$track_count\t$release_date\t$added_at\t$playlist"

    if string match -q 'Starred*' "$playlist"
        # Starred playlist: file goes in artists/<artist>/<album>
        set -l album_file "$ARTISTS_DIR/$safe_artist/$safe_album"
        if not test -f "$album_file"
            touch "$album_file"
        end
        echo -e "$full_row" >>"$album_file"

    else if string match -q '*check out*' "$playlist"
        # Check out playlist: file goes in "check out"/<artist>/<album>
        if not test -d "$CHECKOUT_DIR/$safe_artist"
            mkdir -p "$CHECKOUT_DIR/$safe_artist"
        end
        set -l album_file "$CHECKOUT_DIR/$safe_artist/$safe_album"
        touch "$album_file"
        echo -e "$full_row" >>"$album_file"

    else
        # All other playlists: file goes in artists/<artist>/_unheard/<album>
        mkdir -p "$ARTISTS_DIR/$safe_artist/_unheard"
        set -l album_file "$ARTISTS_DIR/$safe_artist/_unheard/$safe_album"
        if not test -f "$album_file"
            touch "$album_file"
        end
        echo -e "$full_row" >>"$album_file"
    end
end <"$INPUT_FILE"

echo "Done processing albums."
