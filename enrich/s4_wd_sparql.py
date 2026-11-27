"""Étape 4 : Wikidata ciblé via SPARQL (budget, recettes, durée, équipe, prix, IDs)."""
import csv, json, time, requests, os
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)', 'Accept': 'application/sparql-results+json'}
S = requests.Session(); S.headers.update(UA)
rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
tt = [r['tconst'] for r in rows]
def q(query):
    for a in range(5):
        try:
            r = S.post('https://query.wikidata.org/sparql', data={'query': query}, timeout=120)
            if r.status_code == 200: return r.json()['results']['bindings']
            time.sleep(10 * (a + 1))
        except Exception: time.sleep(10)
    return []
PROPS = {'P58': 'scen', 'P86': 'comp', 'P344': 'photo', 'P1040': 'mont', 'P272': 'prod', 'P57': 'real'}
out = {}
def add(t, k, v):
    out.setdefault(t, {}).setdefault(k, [])
    if v not in out[t][k]: out[t][k].append(v)
for i in range(0, len(tt), 150):
    vals = ' '.join('"%s"' % x for x in tt[i:i+150])
    base = 'VALUES ?imdb { %s } ?f wdt:P345 ?imdb . ' % vals
    for b in q('SELECT ?imdb ?f ?allo ?dur ?bud ?budu ?box ?boxu ?boxp WHERE { %s OPTIONAL{?f wdt:P1265 ?allo} OPTIONAL{?f wdt:P2047 ?dur} OPTIONAL{?f p:P2130 ?bs . ?bs psv:P2130 [wikibase:quantityAmount ?bud; wikibase:quantityUnit ?budu]} OPTIONAL{?f p:P2142 ?xs . ?xs psv:P2142 [wikibase:quantityAmount ?box; wikibase:quantityUnit ?boxu] . OPTIONAL{?xs pq:P3005 ?boxp}} }' % base):
        t = b['imdb']['value']
        add(t, 'qid', b['f']['value'].rsplit('/', 1)[1])
        for k in ('allo', 'dur'):
            if k in b: add(t, k, b[k]['value'])
        if 'bud' in b: add(t, 'budget', [b['bud']['value'], b['budu']['value'].rsplit('/', 1)[1]])
        if 'box' in b: add(t, 'box', [b['box']['value'], b['boxu']['value'].rsplit('/', 1)[1], b.get('boxp', {}).get('value', '').rsplit('/', 1)[-1]])
    for p, k in PROPS.items():
        for b in q('SELECT ?imdb ?pl ?g WHERE { %s ?f wdt:%s ?p . OPTIONAL{?p wdt:P21 ?g} ?p rdfs:label ?pl . FILTER(lang(?pl) IN ("fr","en","mul")) }' % (base, p)):
            add(b['imdb']['value'], k, [b['pl']['value'], b['pl'].get('xml:lang'), b.get('g', {}).get('value', '').rsplit('/', 1)[-1]])
    for p, k in (('P166', 'prix'), ('P1411', 'nomin')):
        for b in q('SELECT ?imdb (COUNT(?s) AS ?n) WHERE { %s ?f p:%s ?s } GROUP BY ?imdb' % (base, p)):
            add(b['imdb']['value'], k, b['n']['value'])
    print(i, len(out), flush=True)
    time.sleep(1)
json.dump(out, open('enrich/out/wd_sparql.json', 'w'), ensure_ascii=False)
print('fini', len(out))
