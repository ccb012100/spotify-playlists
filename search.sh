#!/usr/bin/env bash

# location of the repository this script is hosted in
# source: https://stackoverflow.com/a/1482133
REPO=$(dirname -- "$(readlink -f -- "$0")")

function __sm_validate_search_term() {
    if [ ${#1} -eq 0 ]; then
        echo "Error: must provide search term"
    elif [ ${#1} -lt 4 ]; then
        echo "Error: search term must be at least 4 chars"
    fi
}

function __sm_print_usage() {
    echo -e 'USAGE:\n\tsm last NUMBER\n\tsm db SEARCH_TERM\n\tsm SEARCH_TERM'
}

function sm() {

    case $1 in
    -h)
        __sm_print_usage
        ;;
    rs)
        shift
        starred_music_rs # binary located in ~/bin/
        ;;
    last)
        shift
        limit=10 # default to 10
        if [[ -n "$1" ]] && [[ "$1" -gt 0 ]]; then
            limit=$1
        fi
        sqlite3 --readonly "$HOME/playlister.db" ".param init" ".param set :limit $limit" ".read get_last_x_additions.sql"
        ;;
    db)
        shift
        ERROR="$(__sm_validate_search_term "${*}")"
        if [[ -n "$ERROR" ]]; then
            echo >&2 "$ERROR"
            return 1
        else
            [[ -n "${*}" ]]
            echo "Matches for '${*}':"
            sqlite3 --readonly "$HOME/playlister.db" ".param init" ".param set :term '${*}'" ".read $REPO/search_playlister_db.sql"
        fi
        ;;
    *)
        # "${*}" will group all the args into a single quoted string, so we
        # don't have to wrap the search in quotes on the command line, e.g. we
        # can enter `sm Allman Brothers`` instead of `sm "Allman Brothers"`
        ERROR="$(__sm_validate_search_term "${*}")"
        if [[ -n "$ERROR" ]]; then
            echo >&2 "$ERROR"
            return 1
        fi
        rg -i "${*}" "$REPO/starredmusic.tsv" |
            awk -F '\t' '{ printf "%s\t%s\t%3d\t%s\t%s\n", $1, $2, $3, substr($4,1,4), substr($5,1,10) } END{print "----\n" NR " matches"}' | sort | column -t -s $'\t'
        ;;
    esac
}
