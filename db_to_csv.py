import os
import db
import time
session = db.Session()
os.remove("db.csv")

spawns = session.query(db.Sighting) \
    .filter(db.Sighting.expire_timestamp < int(time.time())) \
    .all()
with open('db.csv', 'a+') as f:
    for spawn in spawns:
        csv = "{},{},{},{},{},{},{}".format(spawn.id,spawn.pokemon_id,spawn.spawn_id, 
                spawn.expire_timestamp, spawn.normalized_timestamp, spawn.lat, spawn.lon)
        print csv
        f.write(csv+"\n")
session.close()