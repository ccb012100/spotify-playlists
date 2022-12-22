#!/usr/bin/env python3
'''
    Search for a term in all TrackArtists and AlbumArtists

    Search term can be multiple words and quotes are not necessary.

    USAGE: ./search.py SEARCH_TERM
'''
from enum import Enum
from pathlib import Path
from rich.table import Table, Column
from rich import print
from urllib.request import pathname2url
import sqlite3
import sys

sql_db = str(Path.home() / 'playlister.db')

ADDED = 'added'
ALBUM = 'album'
ALBUM_ID = 'album_id'
ARTIST = 'artist'
PLAYLIST = 'playlist'
PLAYLIST_ID = 'playlist_id'
RELEASED = 'released'
SINGLE_ARTIST = 'artist'
TRACK_ARTIST = 'track_artist'
TRACKS = 'tracks'


def get_sqlite_cursor(db_file: str) -> sqlite3.Cursor:
    try:
        # open in read-only mode; will fail if db_file doesn't exist
        connection = sqlite3.connect(
            f'file:{pathname2url((db_file))}?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row

        return connection.cursor()
    except sqlite3.Error as e:
        print_error(str(e))
        sys.exit()


Message_Level = Enum('Message_Level', ['ERROR', 'SUCCESS', 'WARNING', 'INFO'])


def print_error(message: str) -> None:
    print_message(Message_Level.ERROR, f'ERROR: {message}')


def print_success(message: str) -> None:
    print_message(Message_Level.SUCCESS, message)


def print_warning(message: str) -> None:
    print_message(Message_Level.WARNING, message)


def print_info(message: str) -> None:
    print_message(Message_Level.INFO, message)


def print_message(message_level, message: str) -> None:
    print(message)


def create_album_dict(db_rows: list) -> dict[str, dict[str, object]]:
    ''' Create dict in the form
        ```
        {
            [album_id: str] : {
                album_id: str,
                artist: set(str),
                track_artist: set(str),
                album: str,
                tracks: number,
                released: 'YYYY',
                added: 'YYYY-MM-DD',
                playlist: str,
            }
        }
        ```
    '''
    albums = {}

    alb_artists = {}

    for row in db_rows:
        alb = {k: row[k] for k in row.keys()
               if k not in [ALBUM_ID, PLAYLIST_ID]}

        id = row[ALBUM_ID]

        artist = alb[ARTIST].strip()
        track_artist = alb[TRACK_ARTIST].strip()

        if id not in albums:
            albums[id] = alb
            alb_artists[id] = {}
            alb_artists[id][ARTIST] = []
            alb_artists[id][TRACK_ARTIST] = []

        alb_artists[id][ARTIST].append(artist)

        if track_artist != artist:
            alb_artists[id][TRACK_ARTIST].append(track_artist)

    for id in albums:
        albums[id][ARTIST] = set(alb_artists[id][ARTIST])
        albums[id][TRACK_ARTIST] = set(alb_artists[id][TRACK_ARTIST])

    return albums


def search_by_artist(cursor: sqlite3.Cursor, search_term: str) -> dict:
    cursor.execute(build_query("WHERE x.artist LIKE FORMAT('%%%s%%', ?) OR y.track_artist LIKE FORMAT('%%%s%%', ?)"),
                   [search_term, search_term])

    rows = cursor.fetchall()

    return create_album_dict(rows)


def format_albums_for_table(albums: dict[str, dict]) -> list[dict[str, object]]:
    ''' Format dict to list in format:
        ```
        [
            {
                artist: list[str],
                track_artist: list[str],
                album: str,
                tracks: number,
                released: 'YYYY',
                added: 'YYYY-MM-DD',
                playlist: str
            }
        ]
        ```
    '''
    merged = []

    for id in albums:
        album = albums[id]
        formatted = {k: album[k] for k in album.keys() if k != ALBUM_ID}
        formatted[ARTIST] = '; '.join(album[ARTIST])
        formatted[TRACK_ARTIST] = '; '.join(album[TRACK_ARTIST])
        merged.append(formatted)

    return merged


def print_results(albums: list, search_term: str) -> None:
    if not albums:
        print_warning("\n\tThere were 0 matches")
        return

    table = Table(Column(header='Artists', justify='left', style='blue'),
                  Column(header='Track Artists', justify='left', style='red'),
                  Column(header='Album', justify='left', style='green'),
                  Column(header='# Tracks', justify='right', style='yellow'),
                  Column(header='Released', justify='center', style='white'),
                  Column(header='Playlist', justify='left', style='blue'),
                  Column(header='Added On', justify='center', style='red'),
                  title=f'Matches for "{search_term}"', show_lines=True)

    for a in albums:
        table.add_row(a[ARTIST], a[TRACK_ARTIST], a[ALBUM],
                      str(a[TRACKS]), a[RELEASED], a[PLAYLIST], a[ADDED])

    print(table)


def build_query(where_clause: str) -> str:
    return f'''SELECT
    x.artist
    , y.track_artist
    , alb.name AS album
    , alb.total_tracks AS tracks
    , substr(alb.release_date, 1, 4) as released
    , p.name AS playlist
    , substr(pt.added_at, 1, 10) as added
    , alb.id AS album_id
FROM Album alb
JOIN (
        SELECT aa.album_id AS album_id, art.name AS artist, art.id AS artist_id
        FROM Album a
        JOIN AlbumArtist aa ON aa.album_id = a.id
        JOIN Artist art ON art.id = aa.artist_id
        GROUP BY art.id, a.id
    ) AS x ON x.album_id = alb.id
JOIN (
        SELECT art.name AS track_artist, a.id AS album_id, art.id AS track_artist_id
        FROM Album a
        JOIN Track t ON t.album_id = a.id
        JOIN TrackArtist ta ON ta.track_id = t.id
        JOIN Artist art ON art.id = ta.artist_id
        GROUP BY art.id, a.id
    ) AS y ON y.album_id = alb.id
JOIN Track t ON t.album_id = alb.id
JOIN PlaylistTrack pt ON pt.track_id = t.id
JOIN Playlist p ON p.id = pt.playlist_id
{where_clause}
GROUP BY p.id, alb.id, x.artist_id, y.track_artist_id
'''


def parse_search_term(args: list[str]) -> str:
    search_term = ' '.join(args).strip()

    if not search_term:
        print_error("you must provide a search term")
        exit()

    return search_term


def main():
    search_term = parse_search_term(sys.argv[1:])

    if not search_term:
        print_error("you must provide a search term")
        exit()

    print_info(f'\n\tSearching for "{search_term}":')
    cursor = get_sqlite_cursor(sql_db)
    albums = search_by_artist(cursor, search_term)
    print_results(format_albums_for_table(albums), search_term)

    if albums:
        print_info(f'\n\t{len(albums)} match(es)')


if __name__ == "__main__":
    main()
