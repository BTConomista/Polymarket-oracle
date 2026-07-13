"""Iperparametri tarati PER LEGA — l'unico punto di verità (§7 del CLAUDE.md).

Principio (Punto 6 della roadmap post-audit): le **formule** del modello (in
``src/models/``) sono generali e riutilizzabili; i **valori numerici** degli
iperparametri dipendono dai dati della singola lega e vanno **ri-tarati e
ri-motivati** per ognuna. Tenerli qui, in un dizionario per-lega, fa sì che
aggiungere un campionato sia una modifica di **configurazione**, non di codice:
niente costanti sparse negli script.

Ogni valore ha il riferimento alla fase che lo ha stabilito. Per una nuova lega
(es. Premier) si aggiunge una voce e si ri-esegue la taratura (ogni numero con il
suo blocco 📐, §2-bis): NON si copiano i numeri della Serie A. Esempio noto: il
prior neopromosse ``δ = ln(gol_lega / gol_promosse)`` sarà diverso (in Premier le
promosse sono più deboli → δ probabilmente > 0.23).

Il default del *modello* (``DixonColesModel.__init__``) resta volutamente NEUTRO
(nessun decadimento, nessuno shrinkage, solo gol): la lega-specificità vive qui e
negli script, mai incisa nella classe.
"""
from __future__ import annotations

# Config UFFICIALE della Serie A (tarata nelle Fasi 2b/4b/4d/7/8).
SERIE_A: dict = {
    "half_life_days": 365.0,   # Fase 4d (ri-tarata col blend xG; era 730 in Fase 2b)
    "shrinkage": 1.5,          # Fase 2b, confermata Fase 8 (curva piatta 0.75–1.5)
    "shots_blend": 0.75,       # Fase 4b: peso α gol vs xG nel blend
    "blend_signal": "xg",      # Fase 4b: xG reale (non tiri grezzi, Fase 3)
    "promoted_prior": 0.23,    # Fase 7: δ = ln(1.36/1.08) ≈ 0.23 (gol lega/promosse)
}

# Registro delle configurazioni per lega. Nuova lega = nuova voce (ri-tarata).
LEAGUE_CONFIGS: dict[str, dict] = {
    "serie_a": SERIE_A,
}


def league_config(league_key: str) -> dict:
    """Config ufficiale di una lega. Ignota → SERIE_A come fallback esplicito,
    ma va TARATA prima di fidarsi dei numeri su una lega nuova (§7)."""
    return LEAGUE_CONFIGS.get(league_key, SERIE_A)
