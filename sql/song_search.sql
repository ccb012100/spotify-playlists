-- search database by artist+album names
-- sqlite3 --readonly "$HOME/playlister.db" ".param set :term $term" ".read song_search.sql"
.headers on
.mode columns

SELECT t.name as track
    , GROUP_CONCAT(art.name, '; ') as track_artists
    , alb.name as album
    , substr(alb.release_date, 1, 4) as released
    , p.name as playlist
    , substr(pt.added_at, 1, 10) as added
FROM Track t
JOIN Album alb on alb.id = t.album_id
JOIN TrackArtist ta on ta.track_id = t.id
JOIN Artist art ON art.id = ta.artist_id
JOIN PlaylistTrack pt ON pt.track_id = t.id
JOIN Playlist p ON p.id = pt.playlist_id
WHERE t.name LIKE FORMAT('%%%s%%', :term)
GROUP BY t.id
ORDER BY t.name COLLATE NOCASE ASC, art.name COLLATE NOCASE ASC;
.headers off