#!/usr/bin/env bash
function sm() {
    rg -i "$1" starredmusic.tsv | \
    awk -F '\t' '{
        printf "%s\t%s\t%3d\t%s\t%s\n",
        $1, $2, $3, substr($4,1,4), substr($5,1,10) }' | \
    column -t -s $'\t'
}
