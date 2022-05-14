# sqlite3 playlister.db ".read export_playlisterdb_to_tsv.sql"

.headers on
.mode tabs
.output starred_music.tsv

select art.name as artists, a.name as album, a.total_tracks as tracks, a.release_date, pt.added_at from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where p.name like 'starred%'
group by a.id
order by art.name, a.name;

.output stdout
.headers off
