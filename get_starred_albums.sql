-- list albums in starred playlists by (playlist_id, album_id) pairing, sorted by album_id, playlist_id
-- sqlite3 --readonly "$HOME/playlister.db" ".read get_starred_albums.sql"

.headers on
.mode csv
.output starred_playlist_albums.csv

select a.id as album_id, art.name as artists, a.name as album, a.total_tracks as tracks, substr(a.release_date, 1, 4) as release_date, substr(pt.added_at, 1, 10) as added_at, p.name as playlist
from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where p.name like 'starred%'
group by p.id, a.id
-- order by art.name COLLATE NOCASE ASC, a.name COLLATE NOCASE ASC, a.release_date, a.total_tracks, a.id, p.name;
order by a.id, p.id;

.output stdout
.headers off
