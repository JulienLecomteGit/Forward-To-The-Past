"""Étape 9 : équipes techniques depuis les fichiers publics IMDb (title.principals + name.basics)."""
import gzip, io, json, requests
cible = set(json.load(open('enrich/cible_s9.json')))
CAT = {'composer': 'compositeurs', 'cinematographer': 'dir_photo', 'editor': 'monteurs', 'writer': 'scenaristes', 'director': 'realisateurs'}
def flux(url):
    r = requests.get(url, stream=True, timeout=600, headers={'User-Agent': 'FTTP-enrichissement/1.0'})
    r.raise_for_status()
    return io.TextIOWrapper(gzip.GzipFile(fileobj=r.raw), encoding='utf-8')
film = {}; need = set()
f = flux('https://datasets.imdbws.com/title.principals.tsv.gz'); next(f)
for ln in f:
    p = ln.rstrip('\n').split('\t')
    if p[0] in cible and p[3] in CAT:
        film.setdefault(p[0], []).append((int(p[1]), p[2], p[3])); need.add(p[2])
print('films avec equipe', len(film), 'personnes', len(need))
noms = {}
f = flux('https://datasets.imdbws.com/name.basics.tsv.gz'); next(f)
for ln in f:
    p = ln.split('\t', 2)
    if p[0] in need: noms[p[0]] = p[1]
out = {}
for t, l in film.items():
    d = {}
    for o, n, c in sorted(l):
        if n in noms and noms[n] not in d.setdefault(CAT[c], []): d[CAT[c]].append(noms[n])
    out[t] = d
json.dump(out, open('enrich/out/imdb_equipe.json', 'w'), ensure_ascii=False)
print('ecrit', len(out))
