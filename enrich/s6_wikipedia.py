"""Étape 6 : infobox Wikipédia FR/EN (budget, recettes, musique, photo, montage, scénario, production)."""
import csv, json, re, time, requests
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)'}
S = requests.Session(); S.headers.update(UA)
rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
W = json.load(open('enrich/out/wd_sparql.json'))
need = [r for r in rows if set(r['manques'].split('|')) & {'23', '24', '25', '26', '27', '29', '30', '31', '32'}]
q2t = {}
for r in need:
    for q in W.get(r['tconst'], {}).get('qid', []): q2t[q] = r['tconst']
def get(url, params):
    for a in range(5):
        try:
            x = S.get(url, params=params, timeout=60)
            if x.status_code == 200: return x.json()
            time.sleep(5 * (a + 1))
        except Exception: time.sleep(5)
    return {}
links = {}
qs = list(q2t)
for i in range(0, len(qs), 50):
    j = get('https://www.wikidata.org/w/api.php', {'action': 'wbgetentities', 'ids': '|'.join(qs[i:i+50]), 'props': 'sitelinks', 'sitefilter': 'frwiki|enwiki', 'format': 'json'})
    for q, e in j.get('entities', {}).items():
        for site, sl in e.get('sitelinks', {}).items(): links.setdefault(site, {})[sl['title']] = q2t[q]
    time.sleep(0.2)
FIELDS = re.compile(r'^\s*\|\s*([^=|]+?)\s*=\s*(.*)$')
def infobox(text):
    d = {}
    for line in text.split('\n'):
        m = FIELDS.match(line)
        if m and m.group(2).strip(): d[m.group(1).strip().lower()] = m.group(2).strip()[:600]
    return d
out = {}
for site, lang in (('frwiki', 'fr'), ('enwiki', 'en')):
    titles = list(links.get(site, {}))
    for i in range(0, len(titles), 40):
        j = get(f'https://{lang}.wikipedia.org/w/api.php', {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main', 'rvsection': '0', 'titles': '|'.join(titles[i:i+40]), 'format': 'json', 'formatversion': '2', 'redirects': '1'})
        norm = {n['to']: n['from'] for n in j.get('query', {}).get('normalized', []) + j.get('query', {}).get('redirects', [])}
        for p in j.get('query', {}).get('pages', []):
            t = p.get('title'); src = norm.get(t, t); src = norm.get(src, src)
            tc = links[site].get(src) or links[site].get(t)
            if not tc or 'revisions' not in p: continue
            txt = p['revisions'][0]['slots']['main']['content']
            out.setdefault(tc, {})[lang] = {'title': t, 'ib': infobox(txt)}
        time.sleep(0.5)
    print(site, len(titles), len(out), flush=True)
json.dump(out, open('enrich/out/wikipedia.json', 'w'), ensure_ascii=False)
print('fini', len(out))
