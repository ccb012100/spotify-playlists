#!/usr/bin/env bash
set -Eeou pipefail

sm_repo=$(dirname -- "$(readlink -f -- "$0")")

db="$HOME/playlister.db"
playlister="$HOME/bin/playlister/Playlister/"
playlist_util="$HOME/bin/playlist-util"
py_script="$sm_repo/scripts/update_starred_albums_tsv.py"
sql_scripts_dir="$sm_repo"/sql

# set $SM_TSV in the environment to override these
albums_dir="$sm_repo/albums"
all_albums_tsv="$albums_dir/all_albums.tsv"
sorted_tsv="$albums_dir/sorted_albums.tsv"
starred_tsv="$albums_dir/starred_albums.tsv"

# ANSI colors
clearformat='\033[0m' # clear formatting
orange='\033[0;33m'
red='\033[0;31m'

search_term=''

function info() {
    echo >&2 -e "${orange}${*}${clearformat}"
}
function error() {
    echo >&2 -e "${red}${*}${clearformat}"
}
function validate_search_term() {
    if [ ${#1} -eq 0 ]; then
        error -e "Error: must provide search term\n"
        print_usage
    elif [ ${#1} -lt 4 ]; then
        error "Error: search term must be at least 4 chars"
    fi
}
function print_usage() {
    echo -e 'USAGE:\n\tsm SEARCH_TERM'
    echo -e '\tsm sort [date | artist] SEARCH_TERM'
    echo -e '\tsm SEARCH_TERM'
    echo -e '\tsm db SEARCH_TERM'
    echo -e '\tsm last NUMBER'
    echo -e '\tsm sync [db | tsv] SEARCH_TERM'
    echo -e '\nSet SM_TSV to specify the albums tsv to search'
    echo -e '\nSet SM_JSON to output matches as JSON'
    echo -e '\nSet SM_INCLUDE_PLAYLIST to include Playlist names in results'
}
function print_table() {
    if [[ "${SM_JSON:-}" ]]; then
        shopt -s nocasematch
        case $SM_JSON in
        YES | Y | TRUE | T | 1)
            json='--json' # output as JSON
            if [[ "${SM_TSV:-}" || "${SM_INCLUDE_PLAYLIST:-}" ]]; then
                playlist_col='--table-column name=playlist,trunc,json=string'
            else
                playlist_col=
            fi
            # shellcheck disable=SC2086
            column --table $json \
                --table-name="matches for: $search_term" \
                --separator $'\t' --output-separator $'    ' \
                --table-column name=artist,trunc,json=string \
                --table-column name=album,trunc,json=string \
                --table-column name=tracks,json=number \
                --table-column name=released,json=string \
                --table-column name=added,json=string $playlist_col
            exit 0
            ;;
        esac
        shopt -u nocasematch
    fi

    if [[ "${SM_TSV:-}" || "${SM_INCLUDE_PLAYLIST:-}" ]]; then # truncate artists,album,playlist columns
        column --table --separator $'\t' --output-separator $'    ' --table-truncate 1,2,6
    else # no playlist column to truncate
        column --table --separator $'\t' --output-separator $'    ' --table-truncate 1,2
    fi
}

# TODO: use getopts to parse options
case $1 in
# print usage info
-h | --help | help)
    print_usage
    ;;
# search sqlite DB on artist/album name
db)
    shift
    error="$(validate_search_term "${*}")"
    if [[ -n "$error" ]]; then
        error "$error"
        return 1
    else
        [[ -n "${*}" ]]
        search_term="${*}"
        info "Matches for '${*}':"
        sqlite3 --readonly "$db" ".param init" ".param set :term '${*}'" ".read $sql_scripts_dir/sql/search_playlister_db.sql"
    fi
    ;;
# search sqlite DB on song titles
song)
    shift
    error="$(validate_search_term "${*}")"
    if [[ -n "$error" ]]; then
        error "$error"
        return 1
    else
        [[ -n "${*}" ]]
        search_term="${*}"
        info "Tracks matching '${*}':"
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
sync)
    case $2 in
    # sync sqlite db
    db)
        dotnet run --project "$playlister" --configuration Release
        ;;
    # sync tsv files
    tsv)
        # update $starred_tsv
        $playlist_util sync --source "$db" --destination "$starred_tsv"
        # print header line and then sort remaining lines into $sorted_tsv
        LC_ALL=C awk 'NR <2 { print; next } { print | "sort --ignore-case" }' "$starred_tsv" >|"$sorted_tsv"
        sqlite3 --readonly "$db" ".param init" ".output $all_albums_tsv" ".read $sql_scripts_dir/export_playlisterdb_to_tsv.sqlite"
        ;;
    *)
        error "Error: you must use 'sync db' or 'sync tsv'"
        return 1
        ;;
    esac
    ;;
# search tsv file with default search
*)
    info "\t--Search for '${*}'--\n"
    search_term="${*}"
    default_search "${*}"
    ;;
esac
