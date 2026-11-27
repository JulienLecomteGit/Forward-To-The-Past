"""Étape 3 : AlloCiné (fiche + casting) et CNC (registre data.gouv + recherche par visa sur cnc.fr)."""
import csv, json, os, re, time, io, requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)', 'Accept-Language': 'fr-FR,fr;q=0.9'}
os.makedirs('enrich/out', exist_ok=True)
rows = list(csv.DictReader(open('enrich_input.csv', encoding='utf-8')))
S = requests.Session(); S.headers.update(UA)

def get(u, **kw):
    for a in range(4):
        try:
            r = S.get(u, timeout=40, **kw)
            if r.status_code in (429, 503): time.sleep(10 * (a + 1)); continue
            return r
        except Exception:
            time.sleep(5)
    return None

def txt(e):
    return ' '.join(e.get_text(' ', strip=True).split())

# ---------- AlloCiné ----------
def allo(r):
    aid = r['allocine_id']
    if not aid: return r['tconst'], None
    res = {'id': aid}
    f = get(f'https://www.allocine.fr/film/fichefilm_gen_cfilm={aid}.html')
    if f is None or f.status_code != 200:
        return r['tconst'], {'err': None if f is None else f.status_code}
    s = BeautifulSoup(f.text, 'lxml')
    res['meta'] = [txt(e) for e in s.select('.meta-body-item')]
    c = s.select_one('.certificate'); res['cert'] = txt(c) if c else None
    res['infos'] = {}
    for w in s.select('.what'):
        p = w.find_parent(class_='item')
        if p: res['infos'][txt(w)] = txt(p)[len(txt(w)):].strip()
    res['nat'] = [txt(e) for e in s.select('.nationality')]
    time.sleep(0.4)
    g = get(f'https://www.allocine.fr/film/fichefilm-{aid}/casting/')
    if g is not None and g.status_code == 200:
        s = BeautifulSoup(g.text, 'lxml'); cast = {}
        for h in s.select('h2'):
            sec = txt(h)
            if sec.startswith('Acteurs'): continue
            box = h.find_parent('section') or h.parent.parent
            L = []
            for e in box.select('.md-table-row'):
                L.append([txt(x) for x in e.find_all(recursive=False)])
            for e in box.select('.card'):
                L.append([txt(e)])
            cast[sec] = L
        res['casting'] = cast
    time.sleep(0.4)
    return r['tconst'], res

need_allo = [r for r in rows if r['allocine_id'] and set(r['manques'].split('|')) & {'15', '16', '17', '18', '19', '20', '23', '24', '25', '26', '27', '29', '31', '32', '33', '34', '35'}]
print('allocine a traiter', len(need_allo))
A = {}
with ThreadPoolExecutor(3) as ex:
    for t, v in ex.map(allo, need_allo): A[t] = v
json.dump(A, open('enrich/out/allocine.json', 'w'), ensure_ascii=False)
print('allocine ok', sum(1 for v in A.values() if v and 'err' not in v))

# ---------- CNC : registre data.gouv ----------
REG = 'https://static.data.gouv.fr/resources/liste-des-visas-dexploitations-cinematographiques-delivres-de-1945-a-2025/20251113-091845/liste-des-films-sortis-dans-les-salles-de-cinema-en-france-de-1945-a-2025.csv'
x = get(REG)
if x is not None and x.status_code == 200:
    raw = x.content.decode('utf-8', errors='replace')
    open('enrich/out/cnc_registre_entete.txt', 'w').write(raw[:3000])
    visas = {r['visa_cnc'].strip() for r in rows if r['visa_cnc'].strip()}
    lines = raw.splitlines()
    keep = [lines[0]] + [l for l in lines[1:] if any(re.search(r'(^|[;,"])0*%s([;,"]|$)' % re.escape(v), l) for v in [])]
    # filtrage rapide : on garde les lignes contenant un numéro de visa recherché
    vre = re.compile(r'\b(%s)\b' % '|'.join(sorted(visas, key=len, reverse=True))) if visas else None
    keep = [lines[0]] + [l for l in lines[1:] if vre and vre.search(l)]
    open('enrich/out/cnc_registre_extrait.csv', 'w').write('\n'.join(keep))
    print('registre lignes', len(lines), 'extrait', len(keep))
y = get('https://static.data.gouv.fr/resources/age-conseille-et-visas-cnc-pour-2-664-films/20261026-150541/cinefamille-ages-visas.csv')
if y is not None and y.status_code == 200:
    open('enrich/out/cinefamille.csv', 'w').write(y.content.decode('utf-8', errors='replace'))

# ---------- CNC : recherche par visa sur cnc.fr ----------
P = 'RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2'
base = 'https://www.cnc.fr/professionnels/visas-et-classification'
def cnc(r):
    v = r['visa_cnc'].strip()
    if not v: return r['tconst'], None
    params = {'p_p_id': P, 'p_p_lifecycle': '0', 'p_p_state': 'normal', 'p_p_mode': 'view',
              f'_{P}_executeRechercheParVisa': 'executeRechercheParVisa', f'_{P}_visa': v}
    z = get(base, params=params)
    time.sleep(0.6)
    if z is None or z.status_code != 200: return r['tconst'], {'err': None if z is None else z.status_code}
    s = BeautifulSoup(z.text, 'lxml')
    main = s.select_one('main') or s.body
    t = txt(main) if main else ''
    i = t.find(v)
    return r['tconst'], {'visa': v, 'extrait': t[max(0, i - 1500): i + 2500] if i >= 0 else t[:3000],
                          'tables': [[txt(td) for td in tr.find_all(['td', 'th'])] for tr in s.select('table tr')][:30],
                          'dl': [[txt(dt), txt(dt.find_next_sibling('dd'))] for dt in s.select('dt') if dt.find_next_sibling('dd')][:40]}
need_cnc = [r for r in rows if r['visa_cnc'].strip() and set(r['manques'].split('|')) & {'18', '19', '20'}]
print('cnc a traiter', len(need_cnc))
C = {}
first = True
for r in need_cnc:
    t, v = cnc(r); C[t] = v
    if first:
        z = get(base, params={'p_p_id': P, 'p_p_lifecycle': '0', 'p_p_state': 'normal', 'p_p_mode': 'view', f'_{P}_executeRechercheParVisa': 'executeRechercheParVisa', f'_{P}_visa': r['visa_cnc'].strip()})
        if z is not None: open('enrich/out/cnc_exemple.html', 'w').write(z.text)
        first = False
json.dump(C, open('enrich/out/cnc_site.json', 'w'), ensure_ascii=False)
print('cnc fini', len(C))
