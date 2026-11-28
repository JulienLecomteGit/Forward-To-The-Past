"""Étape 8 : recherche du visa CNC par titre + réalisateur dans le registre complet (films sans visa)."""
import csv, json, re, io, unicodedata, requests
REG = 'https://static.data.gouv.fr/resources/liste-des-visas-dexploitations-cinematographiques-delivres-de-1945-a-2025/20251113-091845/liste-des-films-sortis-dans-les-salles-de-cinema-en-france-de-1945-a-2025.csv'
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)'}
def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]', ' ', s).split()
raw = requests.get(REG, headers=UA, timeout=120).content.decode('utf-8-sig', errors='replace')
reg = list(csv.DictReader(io.StringIO(raw), delimiter=';'))
rows = [r for r in csv.DictReader(open('enrich_input.csv', encoding='utf-8')) if '17' in r['manques'].split('|')]
out = {}
for r in rows:
    names = [n.split()[-1] for n in r['Réalisateur(s)'].split('|') if n.strip()]
    nn = {norm(n)[-1] for n in names if norm(n)}
    tit = [set(norm(r['Titre (affiché)'])), set(norm(r['Titre original']))]
    c = []
    for g in reg:
        rn = set(norm(g.get('Réalisation', '')))
        if not (nn & rn): continue
        gt = set(norm(g.get('Titre', '')))
        sc = max(len(t & gt) / max(1, len(t)) for t in tit)
        if sc >= 0.6: c.append([round(sc, 2), g.get('Titre'), g.get('Réalisation'), g.get('Date'), g.get('Nationalité'), g.get('N° de visa'), g.get('Décision'), g.get('Format')])
    out[r['tconst']] = {'titre': r['Titre (affiché)'], 'orig': r['Titre original'], 'annee': r['Année'], 'cand': sorted(c, reverse=True)[:5]}
json.dump(out, open('enrich/out/visa_titre.json', 'w'), ensure_ascii=False, indent=0)
print(len(rows), sum(1 for v in out.values() if v['cand']))
