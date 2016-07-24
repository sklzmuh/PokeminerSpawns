import sys
import datetime
import json
import jinja2
import os
import operator
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

lines = []
with open(sys.argv[1]) as f:
    lines = f.read().strip().split('\n')

center = sys.argv[2]

pokemon = {}
spawns = {}
pokemonsJSON = json.load(open('pokemon.json'))

# 29 -> 30
def fix_delta(delta):
    return int(round(delta/10.0)*10)


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

# 10,52.4108212665,13.3102412315,1468989590
# 10,52.4108343008,13.3101272484,1468975290
#id	pokemon_id	spawn_id	expire_timestamp	normalized_timestamp	lat	lon
for line in lines:
    id, poke_id, spawn_id, expire_timestamp, despawn ,coord_lat, coord_long = line.split(',')
    poke_id = int(poke_id)
    id = int(id)
    map_id = "{}_{}_{}".format(poke_id, coord_lat, coord_long)
    loc_id = "{},{}".format(coord_lat, coord_long)
    if loc_id not in spawns:
        spawns[loc_id] = []
    t = datetime.datetime.fromtimestamp(float(despawn))
    t = t-datetime.timedelta(minutes=14)
    spawns[loc_id].append({'lat': coord_lat, 'long': coord_long, 'despawn': despawn, 'id': poke_id, 'time': (t.hour, t.minute, t.day)})
    if poke_id not in pokemon:
        pokemon[poke_id] = {'pokemon': pokemonsJSON[poke_id-1]}
    if map_id not in pokemon[poke_id]:
        pokemon[poke_id][map_id] = []
    pokemon[poke_id][map_id].append({'lat': coord_lat, 'long': coord_long, 'despawn': despawn, 'id': poke_id, 'time': (t.hour, t.minute, t.day)})

poke_spawns = {}

for poke_id in xrange(0,152):
    if poke_id not in pokemon:
        continue
    print '\n'
    print "#########################################################"
    print "#{:03} {}".format(poke_id, pokemonsJSON[poke_id-1]['Name'])
    print "#########################################################"
    poke_spawns[poke_id] = []
    for map_id in (i for i in pokemon[poke_id] if i not in ['pokemon', 'spawn_at']):
        _, coord_lat, coord_long = map_id.split('_')
        print "\n{},{}".format(coord_lat, coord_long)
        spawn_at = []
        for spawn_entry in pokemon[poke_id][map_id]:
            t = datetime.datetime.fromtimestamp(float(spawn_entry['despawn']))
            t = t-datetime.timedelta(minutes=14)
            spawn_at.append((t.hour, t.minute, t.day, "{:02}:{:02}".format(t.hour, t.minute), spawn_entry['lat'], spawn_entry['long']))
            spawn_entry['time'] = (t.hour, t.minute, t.day, "{:02}:{:02}".format(t.hour, t.minute), spawn_entry['lat'], spawn_entry['long'])
        

        poke_spawns[poke_id] += spawn_at

        last_time = None
        last_day = None
        for t in spawn_at:
            _t = t[0]*60+t[1]
            if last_time:
                delta = _t-last_time
                if delta == 1:
                    delta = 0
                elif delta == 29:
                    delta = 30
                elif delta == 31:
                    delta = 30
                if delta != 0:
                    print "> {:02}:{:02} | +{}".format(t[0], t[1], delta)
                elif (last_day != t[2]):
                    print "> {:02}:{:02}".format(t[0], t[1])
            else:
                print "> {:02}:{:02}".format(t[0], t[1])
            last_time = _t
            last_day = t[2]
    poke_spawns[poke_id] = list(set(poke_spawns[poke_id]))
    poke_spawns[poke_id] = sorted(poke_spawns[poke_id], key=lambda x: x[0]*60+x[1])

loc_spawns = {}

for loc_id in spawns:
    print loc_id
    spawn_at = []
    for spawn_entry in spawns[loc_id]:
        t = datetime.datetime.fromtimestamp(float(spawn_entry['despawn']))
        t = t-datetime.timedelta(minutes=14)
        spawn_at.append((t.hour, t.minute, spawn_entry, t.day))
    spawn_at = sorted(spawn_at, key=lambda x: x[0]*60+x[1])
    last_time = None
    last_day = None
    if loc_id not in loc_spawns:
        loc_spawns[loc_id]={'spawns':[], 'occurence':{}}
    for t in spawn_at:
        _t = t[0]*60+t[1]
        poke_id = "#{:03} {}".format(t[2]['id'], pokemonsJSON[t[2]['id']-1]['Name'])
        if poke_id not in loc_spawns[loc_id]['occurence']:
            loc_spawns[loc_id]['occurence'][poke_id] = 0
        loc_spawns[loc_id]['occurence'][poke_id]+=1
        if last_time:
            delta = _t-last_time
            delta = fix_delta(delta)
            if delta != 0 or last_day != t[2]:
                loc_spawns[loc_id]['spawns'].append({'id': t[2]['id'], 'pokemon': pokemonsJSON[t[2]['id']-1], 'delta': delta, 'hours': t[0], 'minutes': t[1], 'day': t[3], 'time': "{:02}:{:02}".format(t[0], t[1])})
                print "> {:02}:{:02} - #{:03} {:10} | +{}".format(t[0], t[1], t[2]['id'], pokemonsJSON[t[2]['id']-1]['Name'], delta)
        else:
            loc_spawns[loc_id]['spawns'].append({'id': t[2]['id'], 'pokemon': pokemonsJSON[t[2]['id']-1], 'delta': None, 'hours': t[0], 'minutes': t[1], 'day': t[3], 'time': "{:02}:{:02}".format(t[0], t[1])})
            print "> {:02}:{:02} - #{:03} {:10}".format(t[0], t[1], t[2]['id'], pokemonsJSON[t[2]['id']-1]['Name'])
        last_time = _t
        last_day = t[2]
    loc_spawns[loc_id]['occurence'] = sorted(loc_spawns[loc_id]['occurence'].items(), key=operator.itemgetter(1))[::-1]

html = render('template_spawns.html', {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'poke_spawns': poke_spawns, 'filename': sys.argv[1], 'center':center})
with open('spawns_{}.html'.format(sys.argv[1]), 'w') as f:
    f.write(html)
    
html = render('template_spawns_simple.html', {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'poke_spawns': poke_spawns, 'filename': sys.argv[1], 'center':center})
with open('spawns_{}_simple.html'.format(sys.argv[1]), 'w') as f:
    f.write(html) 

html = render('template_maps2.html', {'loc_spawns': loc_spawns, 'pokemon': pokemon, 'filename': sys.argv[1], 'center':center})
with open('spawns_{}_all.html'.format(sys.argv[1]), 'w') as f:
    f.write(html)

#GoogleMaps(app, key=GOOGLEMAPS_KEY)

for poke_id in range(0,152):
    if poke_id in pokemon:

        html = render('template_maps.html', {'spawns': pokemon[poke_id], 'poke_id': poke_id, 'pokemon':pokemonsJSON[poke_id-1], 'filename': sys.argv[1], 'center':center})
        with open('spawns_{}_{}.html'.format(sys.argv[1],poke_id), 'w') as f:
            f.write(html)