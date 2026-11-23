"""Time Circuits de la DeLorean (88 MPH › Convecteur) : trois rangées d'afficheurs DESTINATION / PRESENT / LAST TIME DEPARTED.

Utilise     : config (affichage)
Utilisé par : vues (machine)
"""
from __future__ import annotations

from html import escape

from config.affichage import MOIS_EN


def moment(annee: int, mois: int, jour: int, heure: int, minute: int) -> dict:
    """Une date au format des Time Circuits : NOV 22 1984 · PM · 08:41."""
    return {"m": MOIS_EN[mois - 1], "j": f"{jour:02d}", "a": f"{annee:04d}", "pm": heure >= 12,
            "h": f"{(heure % 12) or 12:02d}", "n": f"{minute:02d}"}


def _seg(cle: str, valeur: dict, ref: dict, saisie: bool, compteur: list) -> str:
    """Contenu d'un afficheur ; en saisie, chaque caractère s'allume l'un après l'autre (clavier de Doc)."""
    txt = valeur[cle]
    if not saisie:
        return escape(txt)
    out = ""
    for c in txt:
        out += f'<b style="--d:{0.75 + 0.085 * compteur[0]:.2f}s" data-g="{"~" if cle == "m" else "8"}">{escape(c)}</b>'
        compteur[0] += 1
    return out


def _ampm(v: dict) -> str:
    """Voyants AM / PM d'un panneau, celui de l'heure affichée allumé."""
    return (f'<div class="tc-ampm"><span class="tc-lab">AM</span><i class="tc-led{"" if v["pm"] else " on"}"></i>'
            f'<span class="tc-lab">PM</span><i class="tc-led{" on" if v["pm"] else ""}"></i></div>')


def circuits_temps(rangs: list[dict], tape: bool = False) -> str:
    """Les trois rangées des Time Circuits. rang : couleur (r/v/a), plaque, apres (moment), avant (moment, optionnel),
    saisie (la destination se tape caractère par caractère)."""
    html = []
    for r in rangs:
        av, ap, saisie = r.get("avant"), r["apres"], r.get("saisie", False)
        compteur = [0]

        def cellule(cle, lab, fantome):
            """Case d'un afficheur (mois, jour, année, heure, minute) avec son étiquette."""
            if av:
                contenu = f'<span class="tc-av">{escape(av[cle])}</span><span class="tc-ap">{escape(ap[cle])}</span>'
            else:
                contenu = f'<span class="{"tc-saisie" if saisie else ""}">{_seg(cle, ap, ap, saisie, compteur)}</span>'
            seg = "tc-seg tc-14" if cle == "m" else "tc-seg"
            return f'<div class="tc-case"><span class="tc-lab">{lab}</span><div class="{seg}" data-f="{fantome}">{contenu}</div></div>'

        ampm = (f'<div class="tc-pile"><div class="tc-av">{_ampm(av)}</div><div class="tc-ap">{_ampm(ap)}</div></div>' if av else _ampm(ap))
        html.append(f'<div class="tc-rang tc-{r["couleur"]}"><div class="tc-cases">'
                    + cellule("m", "MONTH", "~~~") + cellule("j", "DAY", "88") + cellule("a", "YEAR", "8888") + ampm
                    + cellule("h", "HOUR", "88") + '<div class="tc-dp"><i></i><i></i></div>' + cellule("n", "MIN", "88")
                    + f'</div><div class="tc-plaque">{escape(r["plaque"])}</div></div>')
    return f'<div class="tc{" tape" if tape else ""}">' + "".join(html) + "</div>"
