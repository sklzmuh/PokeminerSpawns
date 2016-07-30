import sys
import datetime
import json
import jinja2
import os
import operator
import sqlite3

if len(sys.argv) < 2:
    raise ValueError('Missing arguments. Please supply lat/long like "12.34, 14.56" and optionally a suffix for generated files as second arg')
elif len(sys.argv) > 2:
    suffix = "_{}".format(str(sys.argv[2]))
else:
    suffix = ''

center = sys.argv[1]

print (center, suffix)

pokemon = {}
spawns = {}
# You can load different localizations here
pokemonsJSON = json.load(open('../locales/pokemon.en.json'))

# Read database into memory
conn = sqlite3.connect('../db.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT * FROM sightings')
sqllist = list(cursor.fetchall())
conn.close()


# 29 -> 30
def fix_delta(delta):
    return int(round(delta / 10.0) * 10)


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


# 10,52.4108212665,13.3102412315,1468989590
# 10,52.4108343008,13.3101272484,1468975290
# id	pokemon_id	spawn_id	expire_timestamp	normalized_timestamp	lat	lon
for entry in sqllist:
    poke_id, spawn_id, expire_timestamp, despawn, coord_lat, coord_long = entry[1:]
    poke_id = int(poke_id)
    map_id = "{}_{}_{}".format(poke_id, coord_lat, coord_long)
    loc_id = "{},{}".format(coord_lat, coord_long)
    if loc_id not in spawns:
        spawns[loc_id] = []
    t = datetime.datetime.fromtimestamp(float(despawn))
    t = t - datetime.timedelta(minutes=14)
    spawns[loc_id].append(
        {'lat': coord_lat, 'long': coord_long, 'despawn': despawn, 'id': poke_id, 'time': (t.hour, t.minute, t.day)})
    if poke_id not in pokemon:
        pokemon[poke_id] = {'pokemon': pokemonsJSON[str(poke_id)]}
    if map_id not in pokemon[poke_id]:
        pokemon[poke_id][map_id] = []
    pokemon[poke_id][map_id].append(
        {'lat': coord_lat, 'long': coord_long, 'despawn': despawn, 'id': poke_id, 'time': (t.hour, t.minute, t.day)})

poke_spawns = {}

for poke_id in xrange(0, 152):
    if poke_id not in pokemon:
        continue
    print '\n'
    print "#########################################################"
    print "#{:03} {}".format(poke_id, pokemonsJSON[str(poke_id)])
    print "#########################################################"
    poke_spawns[poke_id] = []
    for map_id in (i for i in pokemon[poke_id] if i not in ['pokemon', 'spawn_at']):
        _, coord_lat, coord_long = map_id.split('_')
        print "\n{},{}".format(coord_lat, coord_long)
        spawn_at = []
        for spawn_entry in pokemon[poke_id][map_id]:
            t = datetime.datetime.fromtimestamp(float(spawn_entry['despawn']))
            t = t - datetime.timedelta(minutes=14)
            spawn_at.append((t.hour, t.minute, t.day, "{:02}:{:02}".format(t.hour, t.minute), spawn_entry['lat'],
                             spawn_entry['long']))
            spawn_entry['time'] = (
            t.hour, t.minute, t.day, "{:02}:{:02}".format(t.hour, t.minute), spawn_entry['lat'], spawn_entry['long'])

        poke_spawns[poke_id] += spawn_at

        last_time = None
        last_day = None
        for t in spawn_at:
            _t = t[0] * 60 + t[1]
            if last_time:
                delta = _t - last_time
                if delta == 1:
                    delta = 0
                elif delta == 29:
                    delta = 30
                elif delta == 31:
                    delta = 30
                if delta != 0:
                    print "> {:02}:{:02} | +{}".format(t[0], t[1], delta)
                elif last_day != t[2]:
                    print "> {:02}:{:02}".format(t[0], t[1])
            else:
                print "> {:02}:{:02}".format(t[0], t[1])
            last_time = _t
            last_day = t[2]
    poke_spawns[poke_id] = list(set(poke_spawns[poke_id]))
    poke_spawns[poke_id] = sorted(poke_spawns[poke_id], key=lambda x: x[0] * 60 + x[1])

loc_spawns = {}

for loc_id in spawns:
    print loc_id
    spawn_at = []
    for spawn_entry in spawns[loc_id]:
        t = datetime.datetime.fromtimestamp(float(spawn_entry['despawn']))
        t = t - datetime.timedelta(minutes=14)
        spawn_at.append((t.hour, t.minute, spawn_entry, t.day))
    spawn_at = sorted(spawn_at, key=lambda x: x[0] * 60 + x[1])
    last_time = None
    last_day = None
    if loc_id not in loc_spawns:
        loc_spawns[loc_id] = {'spawns': [], 'occurence': {}}
    for t in spawn_at:
        _t = t[0] * 60 + t[1]
        poke_id = "#{:03} {}".format(t[2]['id'], pokemonsJSON[str(t[2]['id'])])
        if poke_id not in loc_spawns[loc_id]['occurence']:
            loc_spawns[loc_id]['occurence'][poke_id] = 0
        loc_spawns[loc_id]['occurence'][poke_id] += 1
        if last_time:
            delta = fix_delta(_t - last_time)
            if delta != 0 or last_day != t[2]:
                loc_spawns[loc_id]['spawns'].append(
                    {'id': t[2]['id'], 'pokemon': pokemonsJSON[str(t[2]['id'])], 'delta': delta, 'hours': t[0],
                     'minutes': t[1], 'day': t[3], 'time': "{:02}:{:02}".format(t[0], t[1])})
                print "> {:02}:{:02} - #{:03} {:10} | +{}".format(t[0], t[1], t[2]['id'], pokemonsJSON[str(t[2]['id'])],
                                                                  delta)
        else:
            loc_spawns[loc_id]['spawns'].append(
                {'id': t[2]['id'], 'pokemon': pokemonsJSON[str(t[2]['id'])], 'delta': None, 'hours': t[0],
                 'minutes': t[1], 'day': t[3], 'time': "{:02}:{:02}".format(t[0], t[1])})
            print "> {:02}:{:02} - #{:03} {:10}".format(t[0], t[1], t[2]['id'], pokemonsJSON[str(t[2]['id'])])
        last_time = _t
        last_day = t[2]
    loc_spawns[loc_id]['occurence'] = sorted(loc_spawns[loc_id]['occurence'].items(), key=operator.itemgetter(1))[::-1]

html = render('templates/spawns.html',
              {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'poke_spawns': poke_spawns, 'filename': suffix,
               'center': center})
with open('spawns{}.html'.format(suffix), 'w') as f:
    f.write(html)

html = render('templates/spawns_simple.html',
              {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'poke_spawns': poke_spawns, 'filename': suffix,
               'center': center})
with open('spawns{}_simple.html'.format(suffix), 'w') as f:
    f.write(html)

html = render('templates/maps2.html',
              {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'filename': suffix, 'center': center})
with open('spawns{}_all.html'.format(suffix), 'w') as f:
    f.write(html)

for poke_id in range(0, 152):
    if poke_id in pokemon:
        html = render('templates/maps.html',
                      {'spawns': pokemon[poke_id], 'poke_id': poke_id, 'pokemon': pokemonsJSON[str(poke_id)],
                       'filename': suffix, 'center': center})
        with open('spawns{}_{}.html'.format(suffix, poke_id), 'w') as f:
            f.write(html)
