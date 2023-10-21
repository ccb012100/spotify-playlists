#!/usr/bin/env python3
"""
    Search for a term in ./albums/*.tsv files

    Search term can be multiple words and quotes are not necessary.

    USAGE: ./tsvsearch.py SEARCH_TERM
"""
from colorama import Fore
from pprint import pprint
from typing import Literal
import argparse
import sys

from scripts.update_starred_albums_tsv import print_info


class SearchInfo:
    json: bool
    pager: bool
    reverse: bool
    sort: Literal["album", "artist", "date"]
    term: str

    def __init__(
        self,
        *,
        json: bool,
        pager: bool,
        reverse: bool,
        sort: Literal["album", "artist", "date"],
        term: str,
    ) -> None:
        self.json = json
        self.pager = pager
        self.reverse = reverse
        self.sort = sort
        self.term = term


def _parse_input() -> SearchInfo:
    parser = argparse.ArgumentParser(
        prog="tsvsearch.py",
        description="Search album tsvs containing Spotify playlist data [assumes ripgrep, column, and awk utilities are installed]",
    )

    parser.add_argument(
        "searchterm", nargs="+", metavar="SEARCH_TERM", help="the text to search for"
    )

    parser.add_argument(
        "-s",
        "--sort",
        choices=["artist", "album", "date"],
        default="artist",
        help="the value to sort on",
    )

    parser.add_argument("-r", "--reverse", action="store_true", help="sort descending")

    parser.add_argument(
        "-p", "--pager", action="store_true", help="pipe results to pager"
    )

    parser.add_argument("--tree", action="store_true", help="display results as a tree")

    parser.add_argument(
        "--json",
        action="store_false",
        help="output in JSON format instead of a table",
    )

    args = parser.parse_args()

    searchterm = " ".join(args.searchterm).strip()

    if len(searchterm) < 3:
        _print_error("Search term must be at least 3 characters")
        sys.exit(1)

    return SearchInfo(
        json=args.json,
        pager=args.pager,
        reverse=args.reverse,
        sort=args.sort,
        term=searchterm,
    )


def _print_info(message: str) -> None:
    print(Fore.BLUE + message)


def _print_error(message: str) -> None:
    print(Fore.RED + f"Error: {message}")


def main() -> None:
    searchinfo = _parse_input()

    print_info(f"called with: {vars(searchinfo)}")


if __name__ == "__main__":
    main()
