-- search database by artist+album names
-- sqlite3 --readonly "$HOME/playlister.db" ".param set :term $term" ".read search_playlister_db.sql"

.mode column

select art.name as artists, a.name as album, a.total_tracks as tracks, substr(a.release_date, 1, 4) as release_date, p.name, substr(pt.added_at, 1, 10) as added_at from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where art.name like format('%%%s%%', :term) or a.name like format('%%%s%%', :term)
group by p.id, a.id
order by art.name COLLATE NOCASE ASC, a.name COLLATE NOCASE ASC;

.headers off
