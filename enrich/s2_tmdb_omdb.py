"""Étape 2 : TMDB (tous les films) + OMDb (films ciblés, quota 1000/jour)."""
import csv, json, os, time, requests
from concurrent.futures import ThreadPoolExecutor
K = os.environ.get('TMDB_API_KEY', '').strip(); O = os.environ.get('OMDB_API_KEY', '').strip()
print('cle TMDB presente', bool(K), 'cle OMDb presente', bool(O))
os.makedirs('enrich/out', exist_ok=True)
rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
S = requests.Session()
auth = {}
if K.startswith('eyJ'): S.headers['Authorization'] = 'Bearer ' + K
else: auth = {'api_key': K}

def get(url, params):
    for a in range(6):
        try:
            r = S.get(url, params=params, timeout=40)
            if r.status_code == 429: time.sleep(3 * (a + 1)); continue
            return r
        except Exception: time.sleep(3)
    return None

KEEPJOBS = {'Screenplay', 'Writer', 'Story', 'Novel', 'Author', 'Original Story', 'Book', 'Adaptation', 'Teleplay', 'Characters',
            'Original Music Composer', 'Music', 'Composer', 'Songs', 'Director of Photography', 'Cinematography', 'Editor', 'Director'}
def tmdb(r):
    tid = r['tmdb_id']
    if not tid: return r['tconst'], None
    x = get(f'https://api.themoviedb.org/3/movie/{tid}', dict(auth, language='fr-FR', append_to_response='credits,release_dates,translations,external_ids'))
    if x is None or x.status_code != 200: return r['tconst'], {'err': None if x is None else x.status_code}
    j = x.json()
    tr = {t['iso_639_1'] + '-' + t['iso_3166_1']: t['data'].get('tagline') for t in j.get('translations', {}).get('translations', []) if t['data'].get('tagline')}
    return r['tconst'], {
        'imdb': j.get('imdb_id'), 'title': j.get('title'), 'otitle': j.get('original_title'), 'date': j.get('release_date'),
        'tagline': j.get('tagline'), 'taglines': tr, 'budget': j.get('budget'), 'revenue': j.get('revenue'), 'runtime': j.get('runtime'),
        'companies': [c['name'] for c in j.get('production_companies', [])],
        'countries': [c['iso_3166_1'] for c in j.get('production_countries', [])],
        'crew': [[c['job'], c['name'], c.get('gender')] for c in j.get('credits', {}).get('crew', []) if c['job'] in KEEPJOBS],
        'rel': {d['iso_3166_1']: d['release_dates'] for d in j.get('release_dates', {}).get('results', []) if d['iso_3166_1'] in ('FR', 'US', 'BE', 'CH', 'CA')},
        'wd': j.get('external_ids', {}).get('wikidata_id'),
    }
out = {}
if K:
    with ThreadPoolExecutor(8) as ex:
        for t, v in ex.map(tmdb, rows): out[t] = v
    json.dump(out, open('enrich/out/tmdb.json', 'w'), ensure_ascii=False)
print('tmdb', len(out), 'ok', sum(1 for v in out.values() if v and 'err' not in v))
# OMDb : films avec prix/nominations, durée, scénaristes, année à vérifier
cible = [r['tconst'] for r in rows if any(m in r['manques'].split('|') for m in ('23', '31', '32', '33', '34', '35'))]
om = {}
if O:
    for t in cible[:950]:
        x = get('https://www.omdbapi.com/', {'i': t, 'apikey': O})
        if x is not None and x.status_code == 200: om[t] = x.json()
        time.sleep(0.1)
    json.dump(om, open('enrich/out/omdb.json', 'w'), ensure_ascii=False)
print('omdb cible', len(cible), 'recu', len(om))
