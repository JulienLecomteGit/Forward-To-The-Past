"""Étape 7 : CNC (par visa) puis AlloCiné, limités aux films encore incomplets, avec budget-temps et sauvegardes."""
import json, time, re, sys, os, csv
sys.argv = ['x']
START = time.time(); BUDGET = 130 * 60
src = open('enrich/s3_allocine_cnc.py', encoding='utf-8').read()
head = src.split('need_allo =')[0]           # imports + get/txt/allo
exec(head)
cnc_src = src[src.index("P = 'Recherche"):src.index('need_cnc =')]
exec(cnc_src)
cible = json.load(open('enrich/cible_s7.json'))
byt = {r['tconst']: r for r in rows}
C = {}
for t, v in cible['cnc']:
    r = dict(byt[t]); 
    if not r['visa_cnc'].strip() and v and v.isdigit(): r['visa_cnc'] = v
    if not r['visa_cnc'].strip(): continue
    k, val = cnc(r); C[k] = val
json.dump(C, open('enrich/out/cnc_site2.json', 'w'), ensure_ascii=False)
print('cnc', len(C), round((time.time() - START) / 60), 'min', flush=True)
A = {}; n429 = 0
for i, t in enumerate(cible['allo']):
    if time.time() - START > BUDGET: break
    k, val = allo(byt[t]); A[k] = val
    if val and val.get('err') == 429: n429 += 1; time.sleep(30)
    if i % 200 == 0:
        json.dump(A, open('enrich/out/allocine2.json', 'w'), ensure_ascii=False); print(i, n429, flush=True)
json.dump(A, open('enrich/out/allocine2.json', 'w'), ensure_ascii=False)
# recherche d'ID AlloCiné manquants
miss = [r for r in rows if '21' in r['manques'].split('|')]
ids = {}
for r in miss:
    if time.time() - START > BUDGET + 10 * 60: break
    q = r['Titre (affiché)'] or r['Titre original']
    x = get('https://www.allocine.fr/rechercher/movie/', params={'q': q})
    if x is not None and x.status_code == 200:
        ids[r['tconst']] = {'q': q, 'annee': r['Année'], 'hits': re.findall(r'fichefilm_gen_cfilm=(\d+)\.html[^>]*>\s*([^<]{1,120})', x.text)[:8],
                            'raw': [m for m in re.findall(r'cfilm=(\d+)', x.text)][:8], 'years': re.findall(r'(\d{4})', x.text[x.text.find('fichefilm'):][:20000])[:20]}
    time.sleep(1)
json.dump(ids, open('enrich/out/allocine_ids.json', 'w'), ensure_ascii=False)
print('allo', len(A), 'ok', sum(1 for v in A.values() if v and 'err' not in v), '429', n429, 'ids', len(ids))
