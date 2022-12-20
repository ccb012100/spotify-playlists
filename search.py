#!/usr/bin/env python3
'''
    Search for a term in all TrackArtists and AlbumArtists

    Search term can be multiple words and quotes are not necessary.

    USAGE: ./search.py SEARCH_TERM
'''
from copy import deepcopy
from colorama import Fore, Style
from enum import Enum
from pathlib import Path
from tabulate import tabulate
from urllib.request import pathname2url
import os
import sqlite3
import sys

sql_db = str(Path.home() / 'playlister.db')


class Columns:
    added = 'added'
    album = 'album'
    album_id = 'album_id'
    artists = 'artists'
    playlist = 'playlist'
    playlist_id = 'playlist_id'
    released = 'released'
    single_artist = 'artist'
    track_artists = 'track_artists'
    tracks = 'tracks'


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


def print_error(message: str):
    print_message(Message_Level.ERROR, f'ERROR: {message}')


def print_success(message: str):
    print_message(Message_Level.SUCCESS, message)


def print_warning(message: str):
    print_message(Message_Level.WARNING, message)


def print_info(message: str):
    print_message(Message_Level.INFO, message)


def print_message(message_level, message: str):
    message_level_colors = {
        Message_Level.ERROR: Fore.RED + Style.BRIGHT,
        Message_Level.SUCCESS: Fore.GREEN + Style.BRIGHT,
        Message_Level.WARNING: Fore.YELLOW,
        Message_Level.INFO: Fore.BLUE,
    }

    print(f'{message_level_colors.get(message_level, "")}{message}{Style.RESET_ALL}')


def create_album_dict(db_rows: list) -> dict:
    ''' Create dict in the form { album_id: { album } } '''
    albums = {}

    for row in db_rows:
        albums[row[Columns.album_id]] = {k: row[k]
                                         for k in row.keys() if k not in [Columns.album_id, Columns.playlist_id]}

    return albums


def search_by_track_artist(cursor: sqlite3.Cursor, search_term: str) -> dict:
    cursor.execute(track_artist_query, [search_term])

    return create_album_dict(cursor.fetchall())


def search_by_album_artist(cursor: sqlite3.Cursor, search_term: str, trackartist_albums: dict) -> dict:
    query = build_album_artist_query(trackartist_albums)

    params = [search_term]
    params.extend(t for t in trackartist_albums)

    cursor.execute(query, params)

    return create_album_dict(cursor.fetchall())


def merge_album_data(track_matches: dict, albums: dict) -> list:
    ''' Add track artist data from `trackartists_albums` to `albumartist_albums` '''
    merged_albums = []

    for album_id in albums:
        album = deepcopy(albums[album_id])
        artists = [a.strip() for a in album[Columns.artists].split(';')]

        if album_id not in track_matches:
            continue

        t_album = track_matches[album_id]

        track_artists = [t.strip()
                         for t in t_album[Columns.track_artists].split(';')]

        album[Columns.track_artists] = '; '.join(
            [t for t in track_artists if t not in artists])

        merged_albums.append(album)

    return merged_albums


def print_results(albums: list) -> None:
    if not albums:
        print_warning("\n\tThere were 0 matches")
        return

    headers = [
        Columns.artists,
        Columns.track_artists,
        Columns.album,
        Columns.tracks,
        Columns.released,
        Columns.playlist,
        Columns.added
    ]

    print()
    # reorder columns
    # see: https://github.com/astanin/python-tabulate/issues/40#issuecomment-595225936
    print(tabulate([[a.get(k, 0) for k in headers] for a in albums], headers=headers,
          maxcolwidths=[30, 30, 30, 10, 10, 30, 12], tablefmt='simple_grid'))


track_artist_query = f'''SELECT
    {Columns.album_id}
    , GROUP_CONCAT({Columns.single_artist}, ';') AS {Columns.track_artists}
    , {Columns.album}
FROM (SELECT alb.id AS {Columns.album_id}
        , art.name as {Columns.single_artist}
        , alb.name as {Columns.album}
    FROM Track t
    JOIN TrackArtist ta on ta.track_id = t.id
    JOIN Artist art on art.id = ta.artist_id
    JOIN Album alb on alb.id = t.album_id
    WHERE art.name LIKE format('%%%s%%', ?)
    GROUP by art.id, alb.id)
GROUP by album_id
'''


def build_album_artist_query(albums: dict, order_by: str = ''):
    if not order_by:
        order_by = f'{Columns.artists},{Columns.album}'

    return f'''SELECT {Columns.album_id}
    , GROUP_CONCAT(artist, '; ') AS {Columns.artists}
    , {Columns.album}
    , {Columns.tracks}
    , {Columns.released}
    , {Columns.playlist}
    , {Columns.added}
    , {Columns.playlist_id}
FROM (SELECT alb.id AS {Columns.album_id}
        , art.name as {Columns.single_artist}
        , alb.name as {Columns.album}
        , alb.total_tracks as {Columns.tracks}
        , substr(alb.release_date, 1, 4) as {Columns.released}
        , p.name as {Columns.playlist}
        , substr(pt.added_at, 1, 10) as {Columns.added}
        , p.id as {Columns.playlist_id}
    FROM AlbumArtist aa
    JOIN Artist art on art.id = aa.artist_id
    JOIN Album alb on alb.id = aa.album_id
    JOIN Track t on t.album_id = alb.id
    JOIN PlaylistTrack pt on pt.track_id = t.id
    JOIN Playlist p on p.id = pt.playlist_id
    WHERE art.name LIKE format('%%%s%%', ?) OR alb.id in ({','.join(["?" for _ in albums])})
    GROUP by p.id, art.id, alb.id)
GROUP by playlist_id, album_id
ORDER by {order_by};'''


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

    cursor = get_sqlite_cursor(str(Path.home() / 'playlister.db'))

    # TODO: get _all_ track artists for the matching albums, not just the artists that match the search term
    track_matches = search_by_track_artist(cursor, search_term)

    albums = search_by_album_artist(cursor, search_term, track_matches)

    print_results(merge_album_data(track_matches, albums))

    if albums:
        print_info(f'\n\t{len(albums)} match(es)')


if __name__ == "__main__":
    main()
