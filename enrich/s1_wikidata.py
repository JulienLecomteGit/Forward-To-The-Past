"""Étape 1 : collecte Wikidata (entités complètes simplifiées) + échantillons de pages."""
import csv, json, time, requests, os, sys
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)'}
API = 'https://www.wikidata.org/w/api.php'
S = requests.Session(); S.headers.update(UA)
os.makedirs('enrich/out', exist_ok=True)

def get(url, **kw):
    for a in range(6):
        try:
            r = S.get(url, timeout=60, **kw)
            if r.status_code == 200: return r
            if r.status_code in (429, 503, 502, 504): time.sleep(5 * (a + 1)); continue
            return r
        except Exception as e:
            time.sleep(5 * (a + 1))
    return None

def simplify(ent):
    out = {'labels': {k: v['value'] for k, v in ent.get('labels', {}).items() if k in ('fr', 'en')}, 'claims': {}}
    for p, sts in ent.get('claims', {}).items():
        L = []
        for st in sts:
            ms = st.get('mainsnak', {})
            dv = ms.get('datavalue', {}).get('value') if ms.get('snaktype') == 'value' else None
            q = {}
            for qp, qs in st.get('qualifiers', {}).items():
                q[qp] = [x.get('datavalue', {}).get('value') for x in qs if x.get('snaktype') == 'value']
            L.append({'v': dv, 'q': q, 'r': st.get('rank')})
        out['claims'][p] = L
    return out

def fetch_entities(ids, props='labels|claims'):
    res = {}
    ids = list(ids)
    for i in range(0, len(ids), 50):
        r = get(API, params={'action': 'wbgetentities', 'ids': '|'.join(ids[i:i+50]), 'props': props, 'languages': 'fr|en', 'format': 'json'})
        if r is None: continue
        for k, v in r.json().get('entities', {}).items():
            if 'missing' in v: continue
            res[k] = simplify(v)
            if 'redirects' in v: res[k]['redirect_from'] = v['redirects']['from']
        time.sleep(0.3)
    return res

rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
qids = {r['wikidata_id'] for r in rows if r['wikidata_id'].startswith('Q')}
# films sans QID : recherche par IMDb via SPARQL
noq = [r['tconst'] for r in rows if not r['wikidata_id'].startswith('Q')]
imdb2q = {}
for i in range(0, len(noq), 100):
    vals = ' '.join('"%s"' % t for t in noq[i:i+100])
    q = 'SELECT ?f ?i WHERE { VALUES ?i { %s } ?f wdt:P345 ?i }' % vals
    r = get('https://query.wikidata.org/sparql', params={'query': q, 'format': 'json'})
    if r is not None and r.status_code == 200:
        for b in r.json()['results']['bindings']:
            imdb2q[b['i']['value']] = b['f']['value'].rsplit('/', 1)[1]
json.dump(imdb2q, open('enrich/out/imdb2qid.json', 'w'))
qids |= set(imdb2q.values())
films = fetch_entities(sorted(qids))
json.dump(films, open('enrich/out/wd_films.json', 'w'), ensure_ascii=False)
# entités référencées (personnes, sociétés, pays, prix...)
ref = set()
for f in films.values():
    for p, L in f['claims'].items():
        for c in L:
            for v in [c['v']] + [x for xs in c['q'].values() for x in xs]:
                if isinstance(v, dict) and v.get('entity-type') == 'item': ref.add(v['id'])
            if isinstance(c['v'], dict) and 'unit' in c['v'] and 'Q' in c['v']['unit']:
                ref.add(c['v']['unit'].rsplit('/', 1)[1])
ref -= set(films)
refs = fetch_entities(sorted(ref))
# on ne garde que labels + P21 (genre) + P31
small = {k: {'labels': v['labels'], 'P21': [c['v']['id'] for c in v['claims'].get('P21', []) if c['v']], 'P31': [c['v']['id'] for c in v['claims'].get('P31', []) if c['v']]} for k, v in refs.items()}
json.dump(small, open('enrich/out/wd_refs.json', 'w'), ensure_ascii=False)
# échantillons de pages pour écrire les parseurs
samp = {
 'allocine_fiche_27063.html': 'https://www.allocine.fr/film/fichefilm_gen_cfilm=27063.html',
 'allocine_casting_27063.html': 'https://www.allocine.fr/film/fichefilm-27063/casting/',
 'allocine_fiche_212251.html': 'https://www.allocine.fr/film/fichefilm_gen_cfilm=212251.html',
 'allocine_casting_212251.html': 'https://www.allocine.fr/film/fichefilm-212251/casting/',
 'allocine_boxoffice_21189.html': 'https://www.allocine.fr/film/fichefilm-21189/box-office/',
 'datagouv_visa.json': 'https://www.data.gouv.fr/api/1/datasets/?q=visa%20exploitation%20cnc&page_size=20',
 'datagouv_cnc.json': 'https://www.data.gouv.fr/api/1/datasets/?organization=534fff94a3a7292c64a77fc8&page_size=50',
 'enwiki_fightclub.json': 'https://en.wikipedia.org/w/api.php?action=parse&page=Fight_Club&prop=wikitext&section=0&format=json',
 'cnc_search.html': 'https://www.cnc.fr/professionnels/visas-et-classification',
}
os.makedirs('enrich/out/samples', exist_ok=True)
for name, u in samp.items():
    r = get(u)
    with open('enrich/out/samples/' + name, 'w', encoding='utf-8') as fh:
        fh.write('' if r is None else ('STATUS %s\n' % r.status_code) + r.text)
print('films', len(films), 'refs', len(small), 'imdb2q', len(imdb2q))
