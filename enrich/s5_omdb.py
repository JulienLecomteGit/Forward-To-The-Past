"""Étape 5 : OMDb (quota gratuit 1000/jour) sur les films aux trous non comblés."""
import csv, json, os, time, requests
O = os.environ.get('OMDB_API_KEY', '').strip()
print('cle OMDb presente', bool(O))
rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
prio = ['31', '32', '23', '35', '34', '33', '24', '25', '26', '27', '29', '30']
def score(r):
    m = set(r['manques'].split('|'))
    return min([prio.index(p) for p in prio if p in m] or [99])
cible = sorted([r for r in rows if score(r) < 99], key=score)
om = {}
if O:
    for r in cible[:990]:
        try:
            x = requests.get('https://www.omdbapi.com/', params={'i': r['tconst'], 'apikey': O, 'plot': 'short'}, timeout=30)
            if x.status_code == 200:
                j = x.json(); om[r['tconst']] = j
                if j.get('Error', '').startswith('Request limit'): break
        except Exception: pass
        time.sleep(0.1)
json.dump(om, open('enrich/out/omdb.json', 'w'), ensure_ascii=False)
print('omdb cible', len(cible), 'recu', len(om))
