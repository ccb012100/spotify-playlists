# sqlite3 playlister.db

.headers on

select p.name, art.name as artists, a.name as album, a.total_tracks as tracks, a.release_date, pt.added_at from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where art.name like 'high pulp%'
group by a.id
order by art.name, a.name;

.headers off
