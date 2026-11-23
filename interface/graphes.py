"""Thème Plotly commun : lisible d'abord (marges automatiques, textes contrastés, grilles discrètes).

Utilise     : config (affichage)
Utilisé par : vues (machine), vues/admin (onglet_qualite, onglet_vue_ensemble)
"""
import plotly.graph_objects as go

from config.affichage import PALETTE_NEON

NEON = PALETTE_NEON  # couleurs des séries Plotly (même palette que le reste de l'app)
TEXTE = "#EDE4F7"
CONFIG = {"displayModeBar": False, "displaylogo": False}


def theme(fig: go.Figure, hauteur: int | None = None) -> go.Figure:
    """Applique le thème néon commun (fond, police, marges, légende, info-bulles) à un graphique."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.025)", colorway=NEON,
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXTE, size=13),
        title=dict(x=0, xanchor="left", y=0.98, yanchor="top", font=dict(family="Inter, Segoe UI, sans-serif", size=15, color="#FFFFFF")),
        margin=dict(l=8, r=8, t=52, b=8), bargap=0.25,
        legend=dict(orientation="h", x=0, y=-0.12, yanchor="top", bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        hoverlabel=dict(bgcolor="#1C1040", bordercolor="rgba(255,255,255,.25)", font=dict(color="#FFFFFF", size=13)))
    axes = dict(automargin=True, gridcolor="rgba(255,255,255,.07)", zeroline=False, linecolor="rgba(255,255,255,.15)",
                tickfont=dict(size=12, color=TEXTE), title_font=dict(size=12, color="#B9A7D6"))
    fig.update_xaxes(**axes)
    fig.update_yaxes(**axes)
    if hauteur:
        fig.update_layout(height=hauteur)
    return fig
