# PokeminerSpawns
Forked from gist https://gist.github.com/ferazambuja/bb7482ffaefe4c554f2b88165a0a7531

## Setup
1. Setup [Pokeminer](https://github.com/modrzew/pokeminer)
- [Download](https://github.com/Cy4n1d3/PokeminerSpawns/archive/master.zip) this Git
 - Extract all files into `/spawn` subdirectory
 - `spawn_location.py` should be located at `/Pokeminer/spawn/spawn_location.py`
- Run with `python spawn_location.py "LAT, LONG" [FILE_SUFFIX/def. none] [LOCALE/def. en]`
 - `"LAT, LONG"`: location where generated maps should be centered (e.g. `"12.34, 13.45"`)
 - `OPTIONAL_SUFFIX`: suffix which will be appended to generated html files
 - `LOCALE`: which Pokemon JSON locale to use (available right now: `de`, `en`, `fr`, `zh_cn`)
- *Optional*: create `config.json`
 - format: ``` {"maps_api":"YOUR_API_KEY"} ```
 
Note: Pokemon spawn information is extracted from the Pokeminer database.
Currently this script only works with SQLite databases and it's assumed that your Pokeminer database is named `db.sqlite`.
