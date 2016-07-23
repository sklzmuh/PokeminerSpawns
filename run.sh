#!/bin/bash
cd ..
python db_csv_r.py
cd spawn 
python spawn_location.py db.csv "YOUR_LAT, YOUR_LONG"
open spawns_db.csv_simple.html