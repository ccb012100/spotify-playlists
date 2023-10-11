#!/usr/bin/env bash
set -euo pipefail

# location of the repository this script is hosted in
# source: https://stackoverflow.com/a/1482133
sm_repo=$(dirname -- "$(readlink -f -- "$0")")
db="$sm_repo/playlister.db"
playlister="$HOME/src/playlister/Playlister/"
py_script="$sm_repo/update_starred_albums_tsv.py"
sorted_tsv="$sm_repo/sorted-albums.tsv"
sql_scripts_dir=$"SM_REPO"/sql
starred_tsv="$sm_repo/starred_albums.tsv"

function __sm_validate_search_term() {
    if [ ${#1} -eq 0 ]; then
        echo -e "Error: must provide search term\n"
        __sm_print_usage
    elif [ ${#1} -lt 4 ]; then
        echo "Error: search term must be at least 4 chars"
    fi
}
function __sm_print_usage() {
    echo -e 'USAGE:\n\tsm SEARCH_TERM'
    echo -e '\tsm sort [date | artist] SEARCH_TERM'
    echo -e '\tsm SEARCH_TERM'
    echo -e '\tsm db SEARCH_TERM'
    echo -e '\tsm last NUMBER'
    echo -e '\tsm sync [db | tsv] SEARCH_TERM'
}
function __sm_format_matches() {
    if [ -p /dev/stdin ]; then
        awk -F '\t' '{ printf "%s\t%s\t%3d\t%s\t%s\n", $1, $2, $3, substr($4,1,4), substr($5,1,10) }' |
            column --table --separator $'\t' --output-separator $'\t'
    else
        echo "Error: no input was found on stdin"
    fi
}
function __sm_sort() {
    if [ -p /dev/stdin ]; then
        sort -t $'\t' -k "$1","$1" </dev/stdin |
            awk '{ print } END { print "\n\t" NR " match(es)" }'
    else
        echo "Error: no input was found on stdin"
    fi
}
function __sm_sort_by_release() {
    __sm_sort 4
}
function __sm_sort_by_artist() {
    __sm_sort 1
}
function __sm_sort_by_album() {
    __sm_sort 2
}
function __sm_search() {
    # "${*}" will group all the args into a single quoted string, so we
    # don't have to wrap the search in quotes on the command line, e.g. we
    # can enter `sm Allman Brothers`` instead of `sm "Allman Brothers"`
    error="$(__sm_validate_search_term "${*}")"
    if [[ -n "$error" ]]; then
        echo >&2 "$error"
        return 1
    fi
    rg -i "${*}" "$sorted_tsv"
}
function __sm_default_search() {
    # sort by album title
    __sm_search "${*}" | __sm_format_matches | __sm_sort_by_album
}

# TODO: use getopts to parse options
case $1 in
# print usage info
-h | --help | help)
    __sm_print_usage
    ;;
# pass through all args to default search
verbatim)
    shift
    __sm_default_search "${*}"
    ;;
# search sqlite DB on artist/album name
db)
    shift
    error="$(__sm_validate_search_term "${*}")"
    if [[ -n "$error" ]]; then
        echo >&2 "$error"
        return 1
    else
        [[ -n "${*}" ]]
        echo "Matches for '${*}':"
        sqlite3 --readonly "$db" ".param init" ".param set :term '${*}'" ".read $sql_scripts_dir/sql/search_playlister_db.sql"
    fi
    ;;
# search sqlite DB on song titles
song)
    shift
    error="$(__sm_validate_search_term "${*}")"
    if [[ -n "$error" ]]; then
        echo >&2 "$error"
        return 1
    else
        [[ -n "${*}" ]]
        echo "Tracks matching '${*}':"
        sqlite3 --readonly "$db" ".param init" ".param set :term '${*}'" ".read $sql_scripts_dir/sql/song_search.sqlite"
    fi
    ;;
# get last N albums added to starred Spotify playlists
last)
    limit=10 # default to 10
    if [[ -n "$2" ]] && [[ "$2" -gt 0 ]]; then
        limit=$2
    fi
    sqlite3 --readonly "$db" ".param init" ".param set :limit $limit" ".read $sql_scripts_dir/get_last_x_additions.sqlite"
    ;;
rs)
    starred_music_rs # binary located in ~/bin/
    ;;
sort)
    shift
    echo -e "\t--Search for '" "${@:2}" "'--\n"
    case $1 in
    date)
        shift
        __sm_search "${*}" | __sm_format_matches | __sm_sort_by_release
        ;;
        # search tsv file and sort by artist
    artist)
        shift
        __sm_search "${*}" | __sm_format_matches | __sm_sort_by_release
        ;;
    album)
        shift
        __sm_search "${*}" | __sm_format_matches | __sm_sort_by_album
        ;;
    *)
        echo -e "'sort' must be followed by [date | artist]\n"
        __sm_print_usage
        ;;
    esac
    ;;
sync)
    case $2 in
    # sync sqlite db
    db)
        dotnet run --project "$playlister" --configuration Release
        ;;
    tsv)
        # updates albums.tsv
        "$py_script"
        # print header line and then sort remaining lines into sorted-albums.tsv
        awk 'NR <2 { print; next } { print | "sort --ignore-case" }' "$starred_tsv" >|"$sorted_tsv"
        sqlite3 --readonly "$db" ".param init" ".read $sm_repo/sql/export_playlisterdb_to_tsv.sqlite"
        ;;
    *)
        echo "Error: you must use 'sync db' or 'sync tsv'"
        return 1
        ;;
    esac
    ;;
# search tsv file with default search
*)
    echo -e "\t--Search for '${*}'--\n"
    __sm_default_search "${*}"
    ;;
esac
