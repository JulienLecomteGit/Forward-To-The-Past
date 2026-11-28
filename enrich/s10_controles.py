"""Étape 10 : (A) texte complet des articles Wikipédia FR pour l'équipe technique manquante ;
(B) équipes IMDb (jeux publics) des films dont l'équipe vient de ChatGPT/Gemini, pour recoupement."""
import gzip, io, json, re, time, requests
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)'}
S = requests.Session(); S.headers.update(UA)
C = json.load(open('enrich/cible_s10.json'))
W = json.load(open('enrich/out/wd_sparql.json'))
def get(url, params):
    for a in range(5):
        try:
            x = S.get(url, params=params, timeout=60)
            if x.status_code == 200: return x.json()
            time.sleep(5 * (a + 1))
        except Exception: time.sleep(5)
    return {}
# ---- A : Wikipédia texte complet
q2t = {}
for t in C['wiki']:
    for q in W.get(t, {}).get('qid', []): q2t[q] = t
links = {'frwiki': {}, 'enwiki': {}}
qs = list(q2t)
for i in range(0, len(qs), 50):
    j = get('https://www.wikidata.org/w/api.php', {'action': 'wbgetentities', 'ids': '|'.join(qs[i:i+50]), 'props': 'sitelinks', 'sitefilter': 'frwiki|enwiki', 'format': 'json'})
    for q, e in j.get('entities', {}).items():
        for site, sl in e.get('sitelinks', {}).items(): links[site][sl['title']] = q2t[q]
    time.sleep(0.2)
KW = re.compile(r'(musique|photograph|directeur de la photo|image|montage|compositeur|cinematograph|music|editor|edited)', re.I)
out = {}
for site, lang in (('frwiki', 'fr'), ('enwiki', 'en')):
    titles = list(links[site])
    for i in range(0, len(titles), 20):
        j = get(f'https://{lang}.wikipedia.org/w/api.php', {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main', 'titles': '|'.join(titles[i:i+20]), 'format': 'json', 'formatversion': '2', 'redirects': '1'})
        norm = {n['to']: n['from'] for n in j.get('query', {}).get('normalized', []) + j.get('query', {}).get('redirects', [])}
        for p in j.get('query', {}).get('pages', []):
            t = p.get('title'); src = norm.get(t, t); src = norm.get(src, src)
            tc = links[site].get(src) or links[site].get(t)
            if not tc or 'revisions' not in p: continue
            txt = p['revisions'][0]['slots']['main']['content']
            lines = [l.strip()[:300] for l in txt.split('\n') if KW.search(l) and (l.lstrip().startswith(('*', '|', ':', ';')) or ' : ' in l or ' by ' in l)]
            out.setdefault(tc, {})[lang] = {'title': t, 'lines': lines[:14]}
        time.sleep(0.5)
    print(site, len(titles), len(out), flush=True)
json.dump(out, open('enrich/out/wiki_plein.json', 'w'), ensure_ascii=False)
# ---- B : IMDb
cible = set(C['imdb'])
CAT = {'composer': 'compositeurs', 'cinematographer': 'dir_photo', 'editor': 'monteurs', 'writer': 'scenaristes'}
def flux(url):
    r = requests.get(url, stream=True, timeout=600, headers=UA); r.raise_for_status()
    return io.TextIOWrapper(gzip.GzipFile(fileobj=r.raw), encoding='utf-8')
film = {}; need = set()
f = flux('https://datasets.imdbws.com/title.principals.tsv.gz'); next(f)
for ln in f:
    p = ln.rstrip('\n').split('\t')
    if p[0] in cible and p[3] in CAT:
        film.setdefault(p[0], []).append((int(p[1]), p[2], p[3])); need.add(p[2])
noms = {}
f = flux('https://datasets.imdbws.com/name.basics.tsv.gz'); next(f)
for ln in f:
    p = ln.split('\t', 2)
    if p[0] in need: noms[p[0]] = p[1]
res = {}
for t, l in film.items():
    d = {}
    for o, n, c in sorted(l):
        if n in noms and noms[n] not in d.setdefault(CAT[c], []): d[CAT[c]].append(noms[n])
    res[t] = d
json.dump(res, open('enrich/out/imdb_valid.json', 'w'), ensure_ascii=False)
print('imdb', len(cible), 'avec equipe', len(res))
