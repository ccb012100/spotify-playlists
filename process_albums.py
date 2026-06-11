#!/usr/bin/env python3
import csv
from pathlib import Path

script_dir = Path(__file__).resolve().parent
input_file = script_dir / "albums" / "all_albums_sorted.tsv"
artists_dir = script_dir / "artists"
checkout_dir = artists_dir / "_check_out"

artists_dir.mkdir(exist_ok=True)
checkout_dir.mkdir(exist_ok=True)


def safe_name(name: str) -> str:
    return name.replace("/", "_")


with open(input_file, newline="", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    header = next(reader)  # skip header

    for row in reader:
        artist, album, track_count, release_date, added_at, playlist = row
        # Trim whitespace
        artist = artist.strip()
        album = album.strip()
        track_count = track_count.strip()
        release_date = release_date.strip()
        added_at = added_at.strip()
        playlist = playlist.strip()

        # Skip rows with empty artist or album
        if not artist or not album:
            continue

        safe_artist = safe_name(artist)
        safe_album = safe_name(album)

        # Ensure artists/<artist>/_unheard/ exists
        artist_path = artists_dir / safe_artist
        unheard_path = artist_path / "_unheard"
        if not artist_path.exists():
            unheard_path.mkdir(parents=True)

        full_row = "\t".join(row)

        if playlist.startswith("Starred"):
            # Starred playlist: file goes in artists/<artist>/<album>
            album_file = artist_path / safe_album
            with open(album_file, "a", encoding="utf-8") as af:
                af.write(full_row + "\n")

        elif "check out" in playlist:
            # Check out playlist: file goes in "check out"/<artist>/<album>
            checkout_artist_path = checkout_dir / safe_artist
            checkout_artist_path.mkdir(exist_ok=True)
            album_file = checkout_artist_path / safe_album
            with open(album_file, "a", encoding="utf-8") as af:
                af.write(full_row + "\n")

        else:
            # All other playlists: file goes in artists/<artist>/_unheard/<album>
            unheard_path.mkdir(parents=True, exist_ok=True)
            album_file = unheard_path / safe_album
            with open(album_file, "a", encoding="utf-8") as af:
                af.write(full_row + "\n")

print("Done processing albums.")
