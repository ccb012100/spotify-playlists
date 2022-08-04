#!/usr/bin/env bash
function sm() {
    case $1 in
    rs)
        shift
        starred_music_rs # binary in ~/bin/
        ;;
    last)
        shift
        limit=10 # default to 10
        if [[ -n "$1" ]] && [[ "$1" -gt 0 ]]; then
            limit=$1
        fi
        sqlite3 --readonly "$HOME/playlister.db" ".param init" ".param set :limit $limit" ".read get_last_x_additions.sql"
        ;;
    search-db)
        shift
        if [[ -n "${*}" ]]; then
            echo "Matches for '${*}':"
            sqlite3 --readonly "$HOME/playlister.db" ".param init" ".param set :term '${*}'" ".read search_playlister_db.sql"
        else
            echo >&2 "Error: need to provide a search term"
            return 1
        fi
        ;;
    *)
        # "${*}" will group all the args into a single quoted string, so we
        # don't have to wrap the search in quotes on the command line, e.g. we
        # can enter <sm Allman Brothers> instead of <sm "Allman Brothers">
        rg -i "${*}" ~/ccb012100/starred-music/starredmusic.tsv |
            awk -F '\t' '{ printf "%s\t%s\t%3d\t%s\t%s\n", $1, $2, $3, substr($4,1,4), substr($5,1,10) } END{print "----\n" NR " matches"}' | sort | column -t -s $'\t'
        ;;
    esac
}
