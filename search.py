#!/usr/bin/env python3
'''
    Search for a term in all TrackArtists and AlbumArtists

    Search term can be multiple words and quotes are not necessary.

    USAGE: ./search.py SEARCH_TERM
'''
from enum import Enum
from pathlib import Path
from typing import Iterator, Literal
from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table, Column
from rich.tree import Tree
from urllib.request import pathname2url
import argparse
from typing import Callable, TypedDict
import operator
import sqlite3
import sys

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

# Types
Sort = Literal['album', 'artist', 'released',
               'added', 'playlist', 'track_artist']
SearchType = Literal['album', 'artist']


class Album(TypedDict):
    album: str
    artist: str
    track_artist: str
    released: str
    added: str
    playlist: str
    tracks: int


class DbAlbum(TypedDict):
    album_id: str
    album: str
    artist: str
    track_artist: str
    released: str
    added: str
    playlist: str
    tracks: int


class SearchInfo:
    type: Literal['album', 'artist']
    term: str
    sort: Literal['album', 'artist', 'released',
                  'added', 'playlist', 'track_artist']
    reverse: bool
    pager: bool
    tree: bool
    no_format: bool

    def __init__(self, *,
                 term: str,
                 type: Literal['album', 'artist'],
                 sort: Literal['album', 'artist', 'released', 'added', 'playlist', 'track_artist'],
                 reverse: bool,
                 pager: bool,
                 tree: bool,
                 no_format: bool
                 ) -> None:
        self.type = type
        self.term = term
        self.sort = sort
        self.reverse = reverse
        self.pager = pager
        self.tree = tree
        self.no_format = no_format


def _print_error(message: str) -> None:
    Console().print(Panel.fit(f'[red]{message}'))


def _get_sqlite_cursor(db_file: str) -> sqlite3.Cursor:
    try:
        # open in read-only mode; will fail if db_file doesn't exist
        connection = sqlite3.connect(
            f'file:{pathname2url((db_file))}?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        return connection.cursor()
    except sqlite3.Error:
        Console().print_exception(show_locals=True)
        sys.exit(1)


def _create_album_dict(db_rows: list) -> dict[str, DbAlbum]:
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

    albartists = {}

    for row in db_rows:
        alb = {k: row[k] for k in row.keys()
               if k not in [ALBUM_ID, PLAYLIST_ID]}

        id = row[ALBUM_ID]

        artist = alb[ARTIST].strip()
        trackartist = alb[TRACK_ARTIST].strip()

        if id not in albums:
            albums[id] = alb
            albartists[id] = {}
            albartists[id][ARTIST] = []
            albartists[id][TRACK_ARTIST] = []

        albartists[id][ARTIST].append(artist)

        if trackartist != artist:
            albartists[id][TRACK_ARTIST].append(trackartist)

    for id in albums:
        albums[id][ARTIST] = set(albartists[id][ARTIST])
        albums[id][TRACK_ARTIST] = set(albartists[id][TRACK_ARTIST])

    return albums


def _search_by_artist(cursor: sqlite3.Cursor, search_term: str) -> dict[str, DbAlbum]:
    return _search_db(cursor,
                      _build_query("WHERE x.artist LIKE FORMAT('%%%s%%', ?) OR y.track_artist LIKE FORMAT('%%%s%%', ?)"), [search_term, search_term])


def _search_by_album(cursor: sqlite3.Cursor, search_term: str) -> dict[str, DbAlbum]:
    return _search_db(cursor, _build_query("WHERE alb.name LIKE FORMAT('%%%s%%', ?)"), [search_term])


def _search_db(cursor: sqlite3.Cursor, query: str, params: list[str]) -> dict[str, DbAlbum]:
    cursor.execute(query, params)
    rows = cursor.fetchall()

    return _create_album_dict(rows)


def _format_albums_for_table(albums: dict[str, DbAlbum], searchinfo: SearchInfo) -> list[Album]:
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

    separator = '; ' if searchinfo.no_format else '\n'

    for id in albums:
        album = albums[id]
        formatted = {k: album[k] for k in album.keys() if k != ALBUM_ID}
        formatted[ARTIST] = separator.join(album[ARTIST])
        formatted[TRACK_ARTIST] = separator.join(album[TRACK_ARTIST])
        merged.append(formatted)

    return sorted(merged, key=operator.itemgetter(*_sort_key(searchinfo.sort)), reverse=(searchinfo.reverse))


def _sort_key(sort: Sort) -> list[str]:
    match sort:
        case 'artist':
            return [ARTIST]
        case 'album':
            return [ALBUM]
        case 'playlist':
            return [PLAYLIST]
        case 'track_artist':
            return [TRACK_ARTIST]
        case 'released' | 'date':
            return [RELEASED]
        case 'added':
            return [ADDED]
        case _:
            _print_error(f'invalid sort type "{sort}"')


def _define_table(albumlist: list[Album]) -> Table:
    count = len(albumlist)

    return Table(Column(header='Artists', justify='left', vertical='middle'),
                 Column(header='Track Artists',
                        justify='left', vertical='middle'),
                 Column(header='Album', justify='left',
                        vertical='middle'),
                 Column(header='# Tracks', justify='right',
                        vertical='middle'),
                 Column(header='Released', justify='center',
                        vertical='middle'),
                 Column(header='Playlist', justify='left',
                        vertical='middle'),
                 Column(header='Added On', justify='center',
                        vertical='middle'),
                 title=f'[green]Search results',
                 show_lines=True,
                 show_edge=False,
                 row_styles=['blue', 'yellow'],
                 box=box.ASCII,
                 caption=f'[purple]{count} {"match" if count == 1 else "matches"}')


def _print_results(albumlist: list[Album], searchinfo: SearchInfo) -> None:
    if not albumlist:
        _print_error("[red]There were 0 matches")
        return

    if searchinfo.no_format:
        _print_tsv(albumlist)
    elif searchinfo.tree:
        _print_tree(albumlist)
    else:
        _print_table(albumlist, searchinfo.pager)


def _print_tsv(albumlist: list[Album]) -> None:
    for a in albumlist:
        Console().print(
            '\t'.join([
                a['artist'], a['track_artist'], a['album'], str(a['tracks']), a['released'], a['playlist'], a['added']]))
    return


def _print_tree(albumlist: list[Album]) -> None:
    # TODO: finish implementing
    '''
        artist
            |_ title
    '''
    albums = iter(albumlist)
    Console().print(tree_iterative(albums), style='purple')
    # Console().print(tree_recursive('', next(albums), next(albums), Tree('Results'), albums))


def tree_iterative(albums: Iterator[Album]) -> Tree:
    a = next(albums)

    root = Tree('Results', style='purple')
    branch = Tree(_artist_leaf(a))

    b = next(albums, None)

    while True:
        # cons.print(branch)
        # please type checker
        branch.add(_album_leaf(a))

        if b is None:
            root.add(branch)
            break

        if a['artist'] != b['artist']:
            root.add(branch)
            branch = Tree(_artist_leaf(a))

        a = b
        b = next(albums, None)

    return root


def tree_recursive(artist: str, a: Album, b: Album | None, tree: Tree, albums: Iterator[Album]) -> Tree:
    if b is None:
        if not artist:
            branch = Tree(_artist_leaf(a))
            branch.add(_album_leaf(a))
            tree.add(branch)
        else:
            tree.add(_album_leaf(a))

        return tree

    if not artist:
        branch = Tree(_artist_leaf(a))
        branch.add(_album_leaf(a))

        return (tree_recursive(b['artist'], b, next(albums, None), branch, albums))

    tree.add(_album_leaf(a))

    if b['artist'] != artist:
        tree.add(_artist_leaf(b))

    return tree_recursive(b['artist'], b, next(albums, None), tree, albums)


def _build_tree(first: Album, second: Album | None, albums: Iterator[Album], tree: Tree) -> Tree:
    if second is None:
        return tree

    tree.add(_album_leaf(first))

    if first['artist'] == second['artist']:
        tree.add(_album_leaf(second))
        return _build_tree(second, next(albums, None), albums, tree)
    else:
        branch = Tree(_artist_leaf(first))
        branch.add(_album_leaf(second))
        return _build_tree(second, next(albums, None), albums, tree)


def _artist_leaf(a: Album) -> Panel:
    return Panel.fit(a['artist'], style='red', border_style='blue')


def _album_leaf(a: Album) -> Panel:
    table = Table(show_header=False, show_edge=False, border_style='yellow')
    [table.add_column(style='green', vertical='middle') for _ in range(6)]
    table.add_row(*[str(a[k]) if k == TRACKS else a[k]
                  for k in a.keys() if k != ARTIST])
    return Panel.fit(table, border_style='yellow')


def _print_table(albumlist: list[Album], use_pager: bool) -> None:
    table = _define_table(albumlist)
    [table.add_row(*_column_values(a)) for a in albumlist]

    def display(): Console().print(Panel.fit(Padding(table, (1), expand=False)))

    if (use_pager):
        with Console().pager():
            display()
    else:
        display()


def _column_values(album: Album) -> list[str]:
    columnorder = [ARTIST, TRACK_ARTIST, ALBUM,
                   TRACKS, RELEASED, PLAYLIST, ADDED]
    return [str(album[col]) if col == TRACKS else album[col] for col in columnorder]


def _build_query(where: str) -> str:
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
{where}
GROUP BY p.id, alb.id, x.artist_id, y.track_artist_id
ORDER BY artist, track_artist, album, playlist
'''


def _parse_input() -> SearchInfo:
    parser = argparse.ArgumentParser(
        prog='search.py',
        description='Search sqlite database containing Spotify playlist data')

    parser.add_argument('searchterm', nargs='+',
                        metavar="SEARCH_TERM", help='the text to search for')

    parser.add_argument(
        '-t', '--type', choices=[ALBUM, ARTIST], default=ARTIST, help='the values to search against')

    parser.add_argument(
        # 'date' is an alias for 'released'
        '-s', '--sort', choices=[ALBUM, ARTIST, PLAYLIST, RELEASED, ADDED, TRACK_ARTIST, 'date'], default=ARTIST,
        help='the value to sort on')

    parser.add_argument('-r', '--reverse',
                        action='store_true', help='sort descending')

    parser.add_argument('-p', '--pager', action='store_true',
                        help='pipe results to pager')

    parser.add_argument('--tree', action='store_true',
                        help='display results as a tree')

    parser.add_argument('--no-format', action='store_true',
                        help='display in TSV format instead of a table')

    args = parser.parse_args()

    searchterm = ' '.join(args.searchterm).strip()

    if len(searchterm) < 3:
        _print_error('Search term must be at least 3 characters')
        sys.exit(1)

    return SearchInfo(term=searchterm, type=args.type, sort=args.sort, reverse=args.reverse, pager=args.pager,
                      tree=args.tree, no_format=args.no_format)


def _search(cursor, searchinfo: SearchInfo) -> dict[str, DbAlbum]:
    Console().print(Panel.fit(
        f'Searching [green]{searchinfo.type}s[/] for "[yellow]{searchinfo.term}[/]" ...'))

    search: Callable[[sqlite3.Cursor, str], dict[str, DbAlbum]]

    match searchinfo.type:
        case 'album':
            search = _search_by_album
        case 'artist':
            search = _search_by_artist
        case _:
            _print_error(f'invalid search type "{searchinfo.type}"')
            sys .exit(1)

    return search(cursor, searchinfo.term)


def main() -> None:
    _sql_db = str(Path.home() / 'playlister.db')

    searchinfo = _parse_input()

    _print_results(
        _format_albums_for_table(
            _search(_get_sqlite_cursor(_sql_db), searchinfo),
            searchinfo),
        searchinfo
    )


if __name__ == "__main__":
    main()
