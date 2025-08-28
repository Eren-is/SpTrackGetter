# SpTrackGetter
Aggregates Spotify song/track data based on song url with audio features data from SoundStats.
Additionally creates a YouTube search url (artist + title as search query).
Requires a dotenv file with keys SPOTIFY_CLIENT and SPOTIFY_SECRET (as well as SOUNDSTAT_KEY for SoundStats API data).

Spotify API data:
- Song title
- Song artists
- Album information
- Duration
- Release date
- Cover art
- Popularity
Additionally:
- YouTube search URL
SoundStat API data:
- Genre
- Acousticness
- Danceability
- Energy
- Instrumentalness
- Valence
- Tempo

SoundStat API might return 201 response with "Track analysis in progress" message.
In such a situation field `audio_features_in_progress` is set to True. User can then call `load_info` to update (analysis can take a very long time).
