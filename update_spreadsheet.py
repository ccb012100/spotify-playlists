#!/usr/bin/env python3

from colorama import Fore, Style
from pathlib import Path
from urllib.request import pathname2url
import os
import sqlite3
import sys

# assumes it's hosted in the same repo as this script
spreadsheet = os.path.abspath(os.path.dirname(
    __file__)) + '/' + 'starredmusic.tsv'

sql_db = str(Path.home() / 'playlister.db')

sql_query = '''select art.name, a.name, a.total_tracks, substr(a.release_date, 1, 4), pt.added_at, p.name from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where p.name like 'starred%'
group by pt.added_at, art.id
order by pt.added_at DESC
limit ? OFFSET ?'''

# TODO: use format strings instead of concatenating


def get_last_album_added(spreadsheet):
    """"
    :return: last album added in .tsv format
    """
    with open(spreadsheet, 'rb') as f:

        try:  # catch OSError in case of a one line file
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)

            last_line = f.readline().decode()

            print_info('last album added to ' + spreadsheet + ':\n---\n' + last_line + '\n')

            return last_line.rstrip()  # trim trailing newline
        except OSError:
            f.seek(0)

def create_sqlite_connection(db_file):
    """
    :return: Connection object
    """

    try:
        # open in read-only mode; will fail if db_file doesn't exist
        return sqlite3.connect('file:{}?mode=ro'.format(pathname2url(db_file)), uri=True)
    except sqlite3.Error as e:
        print_error(e)
        sys.exit()


def row_to_tsv(row):
    """
    Returns sql row converted to .tsv format
    """
    tsv = '\t'.join([str(x) for x in row])
    return tsv


def add_albums(spreadsheet, albums):
    if albums:
        print_info('adding to  ' + spreadsheet + ':\n---\n' + '\n'.join(albums) + '\n')
        # TODO: write to file
        print_success('Success: added ' + str(len(albums)) + ' albums!')
    else:
        print_error('Error: entries collection was empty!')
        sys.exit()


def print_error(message):
    print(Fore.RED + Style.BRIGHT + message + Style.RESET_ALL)


def print_success(message):
    print(Fore.GREEN + Style.BRIGHT + message + Style.RESET_ALL)


def print_warning(message):
    print(Fore.YELLOW + Style.BRIGHT + message + Style.RESET_ALL)


def print_info(message):
    print(Fore.BLUE + Style.BRIGHT + message + Style.RESET_ALL)


last_added = get_last_album_added(spreadsheet)

sql_conn = create_sqlite_connection(str(Path.home() / 'playlister.db'))
sql_cur = sql_conn.cursor()

limit = 50
offset = 0

# while True:
sql_cur.execute(sql_query, [limit, offset])
db_row = sql_cur.fetchall()

new_entries = []

# TODO: increment offset and retrieve more entries if no matches are found
for row in db_row:
    album = row_to_tsv(row)

    if album == last_added:
        if new_entries:
            # reverse the list to order them in ASC order
            new_entries.reverse()
            add_albums(spreadsheet, new_entries)
        else:
            print_success(
                'Nothing to add; the spreadsheet is already up to date!')
        sys.exit()
    else:
        new_entries.append(album)

if sql_conn:
    sql_conn.close()
else:
    print_warning('connection was already closed')

print_error('Error: was unable to find the last entry in the database')
