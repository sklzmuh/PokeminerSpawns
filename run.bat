start cmd
@echo off
cd ..
python db_csv_r.py
cd spawn 
python spawn_location.py db.csv "YOUR_LAT, YOUR_LONG"
pause