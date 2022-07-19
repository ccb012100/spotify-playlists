-- view last $LIMIT tracks, in order of being added to the db
-- call in CLI: `sqlite3 --readonly "$HOME/playlister.db" ".param set :limit $LIMIT" ".read get_last_x_additions.sql"`

.mode tabs

select * from
(select art.name, a.name, a.total_tracks, substr(a.release_date, 1, 4), pt.added_at from Album a
join albumartist aa on aa.album_id = a.id
join artist art on art.id = aa.artist_id
join track t on t.album_id = a.id
join playlisttrack pt on pt.track_id = t.id
join playlist p on p.id = pt.playlist_id
where p.name like 'starred%'
group by pt.added_at
order by pt.added_at DESC
limit CAST(:limit as NUMBER))
order by added_at;

.exit