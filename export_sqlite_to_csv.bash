#!/usr/bin/env bash

# $ sqlite3 playlister.db
# SQLite version 3.42.0 2023-05-16 12:36:15
# Enter ".help" for usage hints.
# sqlite> select name from sqlite_schema where type='table' order by name;
# Album
# AlbumArtist
# Artist
# Playlist
# PlaylistTrack
# Track
# TrackArtist
# VersionInfo
sqlite3 -header -csv "$HOME"/playlister.db "select * from Album;" > export/Album.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from AlbumArtist;" > export/AlbumArtist.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from Artist;" > export/Artist.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from Playlist;" > export/Playlist.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from PlaylistTrack;" > export/PlaylistTrack.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from Track;" > export/Track.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from TrackArtist;" > export/TrackArtist.csv
sqlite3 -header -csv "$HOME"/playlister.db "select * from VersionInfo;" > export/VersionInfo.csv
