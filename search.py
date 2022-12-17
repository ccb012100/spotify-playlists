#!/usr/bin/env python3
'''
    Search for a term in all TrackArtists and AlbumArtists

    Search term can be multiple words and quotes are not necessary.

    USAGE: ./search.py SEARCH_TERM
'''
from colorama import Fore, Style
from enum import Enum
from pathlib import Path
from tabulate import tabulate
from urllib.request import pathname2url
import os
import sqlite3
import sys

# assumes it's hosted in the same repo as this script
spreadsheet = '{}/{}'.format(os.path.abspath(os.path.dirname(
    __file__)), 'starredmusic.tsv')

sql_db = str(Path.home() / 'playlister.db')


def get_sqlite_cursor(db_file):
    """
    :return: cursor object
    """

    try:
        # open in read-only mode; will fail if db_file doesn't exist
        connection = sqlite3.connect(
            'file:{}?mode=ro'.format(pathname2url(db_file)), uri=True)
        connection.row_factory = sqlite3.Row
        return connection.cursor()
    except sqlite3.Error as e:
        print_error(e)
        sys.exit()


Message_Level = Enum('Message_Level', ['ERROR', 'SUCCESS', 'WARNING', 'INFO'])


def print_error(message):
    print_message(Message_Level.ERROR, message)


def print_success(message):
    print_message(Message_Level.SUCCESS, message)


def print_warning(message):
    print_message(Message_Level.WARNING, message)


def print_info(message):
    print_message(Message_Level.INFO, message)


def print_message(message_level, message):
    message_level_colors = {
        Message_Level.ERROR: Fore.RED + Style.BRIGHT,
        Message_Level.SUCCESS: Fore.GREEN + Style.BRIGHT,
        Message_Level.WARNING: Fore.YELLOW,
        Message_Level.INFO: Fore.BLUE,
    }

    print(message_level_colors.get(message_level, '') + message + Style.RESET_ALL)


def get_albums_by_trackartist(cursor, search_term):
    albums = {}

    cursor.execute(track_artist_query, [search_term])
    track_rows = cursor.fetchall()

    for row in track_rows:
        albums[row['album_id']] = {key: row[key] for key in row.keys()}

    return albums


def get_albums_by_albumartist(cursor, search_term, trackartist_albums):
    albums = {}

    # add placeholders for WHERE IN clause
    query = album_artist_query.format(
        ','.join(["?" for _ in trackartist_albums]))

    params = [search_term]
    params.extend(t for t in trackartist_albums)

    cursor.execute(query, params)
    album_rows = cursor.fetchall()

    for row in album_rows:
        albums[row['album_id']] = {key: row[key] for key in row.keys()}

    return albums


track_artist_query = '''SELECT album_id, GROUP_CONCAT(artist, '; ') AS track_artists, album
FROM (SELECT alb.id AS album_id, art.name as artist, alb.name as album
FROM Track t
JOIN TrackArtist ta on ta.track_id = t.id
JOIN Artist art on art.id = ta.artist_id
JOIN Album alb on alb.id = t.album_id
WHERE art.name LIKE format('%%%s%%', ?)
GROUP by art.id, alb.id)
GROUP by album_id
'''

# TODO: join with Playlist table, add more fields
album_artist_query = '''SELECT album_id, GROUP_CONCAT(artist, '; ') AS artists, album
FROM (SELECT alb.id AS album_id, art.name as artist, alb.name as album
FROM AlbumArtist aa
JOIN Artist art on art.id = aa.artist_id
JOIN Album alb on alb.id = aa.album_id
WHERE art.name LIKE format('%%%s%%', ?) OR alb.id in ({0})
GROUP by art.id, alb.id)
GROUP by album_id;'''


def main():
    print("Hello World!")
    search_term = ' '.join(sys.argv[1:]).strip()

    if not search_term:
        print_error("you must provide a search term")
        exit()

    cursor = get_sqlite_cursor(str(Path.home() / 'playlister.db'))

    trackartist_albums = get_albums_by_trackartist(cursor, search_term)
    # TODO: how to set longer line length? .env file?
    albumartist_albums = get_albums_by_albumartist(cursor,
                                                   search_term, trackartist_albums)
    # TODO: merge data; only show track artists that differ from album artists
    print(tabulate([trackartist_albums[t]
          for t in trackartist_albums], headers="keys"))
    print()
    print(tabulate([albumartist_albums[a]
          for a in albumartist_albums], headers="keys"))


if __name__ == "__main__":
    main()
