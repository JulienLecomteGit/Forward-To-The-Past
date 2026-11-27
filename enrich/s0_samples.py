"""Échantillons de pages publiques pour écrire les parseurs (AlloCiné, CNC, data.gouv, Wikipedia)."""
import requests, os
UA = {'User-Agent': 'FTTP-enrichissement/1.0 (projet pedagogique; github.com/JulienLecomteGit)', 'Accept-Language': 'fr-FR,fr;q=0.9'}
os.makedirs('enrich/samples', exist_ok=True)
samp = {
    'allo_fiche_27063.html': 'https://www.allocine.fr/film/fichefilm_gen_cfilm=27063.html',
    'allo_casting_27063.html': 'https://www.allocine.fr/film/fichefilm-27063/casting/',
    'allo_fiche_212251.html': 'https://www.allocine.fr/film/fichefilm_gen_cfilm=212251.html',
    'allo_casting_212251.html': 'https://www.allocine.fr/film/fichefilm-212251/casting/',
    'allo_box_21189.html': 'https://www.allocine.fr/film/fichefilm-21189/box-office/',
    'dg_visa.json': 'https://www.data.gouv.fr/api/1/datasets/?q=visa%20exploitation&page_size=20',
    'dg_cnc.json': 'https://www.data.gouv.fr/api/1/datasets/?q=cnc%20films&page_size=30',
    'enwiki.json': 'https://en.wikipedia.org/w/api.php?action=parse&page=Fight_Club&prop=wikitext&section=0&format=json',
    'cnc_visas.html': 'https://www.cnc.fr/professionnels/visas-et-classification',
}
for n, u in samp.items():
    try:
        r = requests.get(u, headers=UA, timeout=40)
        t = 'STATUS %s %s\n' % (r.status_code, r.url) + r.text
    except Exception as e:
        t = 'ERR %s' % e
    open('enrich/samples/' + n, 'w', encoding='utf-8').write(t)
