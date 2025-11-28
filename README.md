
Parses Dr. Demento HTML playlist files from the Dr. Demento Database, attempting to summarize them a CSV file by title and artist highlighting the first appearance of each song on the show.

[drdementabase.csv](drdementabase.csv) is a first pass at this, but additional work is needed to clean up artist names and song titles to reduce the number of duplicates, make better use of special topic information parsed from the HTML files.

Thanks to Jeff Morris for maintaining these poaylists through the years and of course to Barry, Dr. Demento, Hansen for his long-running show.  Enjoy your retirement, you've earned it,

### Setup

1. Download the HTML playlist files from [Dr. Demento Data Base](https://dmdb.org/playlists/zip_pl.html)
2. unzip the downloaded files into a directory named `drd`
3. `python drdementabase.py`
