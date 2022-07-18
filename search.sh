#!/usr/bin/env bash
function sm() {
    case $1 in
    rs)
        shift
        starred_music_rs # binary in ~/bin/
        ;;
    *)
        # "${*}" will group all the args into a single quoted string, so we
        # don't have to wrap the search in quotes on the command line, e.g. we
        # can enter <sm Allman Brothers> instead of <sm "Allman Brothers">
        rg -i "${*}" ~/ccb012100/starred-music/starredmusic.tsv |
            awk -F '\t' '{ printf "%s\t%s\t%3d\t%s\t%s\n", $1, $2, $3, substr($4,1,4), substr($5,1,10) } END{print "----\n" NR " matches"}' | column -t -s $'\t'
        ;;
    esac
}
