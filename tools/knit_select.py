"""HESTIA x Knit Nodes: pick a knit structure for every HESTIA zone.
Inputs:  Knit Nodes behaviour table (Grasshopper loop model)  +  HESTIA joint demands (calc.py, calc.json)
Output:  knit_select.json -> renders (hestia.py KNITMAP) and the site matrix
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
# Knit Nodes: stitches/round, max stretch %, capacity used at the node %, rounds per sleeve
KB = {'stockinette': (16, 84, 105, 68), 'garter': (12, 130, 145, 76), 'rib1': (20, 125, 78, 84), 'rib2': (20, 113, 81, 84),
      'seed': (12, 105, 192, 62), 'cable': (16, 75, 214, 68), 'lace': (12, 152, 126, 50), 'tuck': (12, 91, 152, 64),
      'slip': (16, 55, 182, 68), 'chevron': (16, 84, 105, 68)}
calc = json.load(open(os.path.join(HERE, 'calc.json')))
flex = {f['joint']: f for f in calc['flex']}
LIMIT = 0.85                     # use at most 85 % of a knit's stretch on a moving joint
# zone, demand % (flat sleeve strain), job
Z = [('Hip', flex['Hip']['flat_strain'], 'flex'), ('Knee', flex['Knee']['flat_strain'], 'flex'), ('Ankle', flex['Ankle']['flat_strain'], 'flex'),
     ('Shoulder', flex['Shoulder']['flat_strain'], 'flex'), ('Elbow', flex['Elbow']['flat_strain'], 'flex'),
     ('Waist twist', 40, 'flex'), ('Torso', 15, 'cover'), ('Shin', 10, 'brace'), ('Flank vent', 15, 'open'), ('Forearm grip', 20, 'grip'), ('Sensor band', 5, 'open-fine')]
out = []
for name, d, job in Z:
    util = {k: round(d / v[1] * 100) for k, v in KB.items()}
    if job == 'flex':
        closed = [k for k in KB if k != 'lace' and d / KB[k][1] <= LIMIT]
        pick = max(closed, key=lambda k: (KB[k][3], -util[k])) if closed else None
        note = ''
        if name in flex and flex[name]['pinch_margin_mm'] < 0:
            note = f"Pleat stack needs {flex[name]['stack_mm']} mm but the inside of the bend has {flex[name]['inner_mm']} mm: rib pleats outside, open lace gusset inside."
            pick = pick or 'rib1'; gus = 'lace'
        elif pick is None:
            pick = 'rib1'; gus = None; note = 'No flat knit passes: pleated rib unfolds length first.'
        else:
            gus = None; note = f"Densest closed knit under the 85 % line: {KB[pick][3]} rounds per sleeve."
        if name in flex and pick and util[pick] > LIMIT * 100:
            note = note or 'Flat knit is over the limit: pleats carry the extra length.'
    elif job == 'cover': pick, gus, note = 'stockinette', None, 'Low strain: the smoothest face and lowest bulk win.'
    elif job == 'brace': pick, gus, note = min(KB, key=lambda k: KB[k][1]), None, 'Wants the least stretch: floats lock the fabric so the shin cover holds its shape.'
    elif job == 'open': pick, gus, note = 'lace', None, 'Only the eyelet structure opens holes as it stretches: airflow through the knit.'
    elif job == 'open-fine': pick, gus, note = 'lace', None, 'Lace at double gauge: light and sound pass, the sensor stays hidden.'
    elif job == 'grip': pick, gus, note = 'seed', None, 'Pebbled all over and lies flat with no curl: a surface for silicone dots.'
    out.append(dict(zone=name, demand=d, job=job, util=util, pick=pick, gusset=gus, note=note,
                    pinch=flex.get(name, {}).get('pinch_margin_mm'), pleats=flex.get(name, {}).get('pleats')))
json.dump(dict(limit=LIMIT, knits=KB, zones=out), open(os.path.join(HERE, 'knit_select.json'), 'w'), indent=1)
for o in out: print(f"{o['zone']:13s} {o['demand']:4d}%  {o['pick']:12s} {o['util'][o['pick']]:4d}%  {o['gusset'] or ''}")
