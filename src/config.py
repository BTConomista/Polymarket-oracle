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

# Config Premier League e La Liga (ri-tarate nella Fase 57, §7).
#
# ESITO della ri-taratura: gli iperparametri sono PIATTI su entrambe le leghe,
# esattamente come in Serie A (Fase 8). emivita 365g e shrinkage 1.5 restano
# ottimi (emivita 730 PEGGIORA ovunque, anche in Liga malgrado le rose piu'
# stabili: la EDA sovra-interpretava l'autocorr 0.82). L'UNICA differenza
# strutturale e' il prior neopromosse δ, ricalcolato dai gol di ciascuna lega
# (§2-bis) e adottato per motivazione (guadagno log-loss nel rumore, come il
# δ Serie A alla Fase 7/17 — "probabile, non concluso"):
#   Premier δ=0.33: promosse inglesi molto piu' deboli (segnano il 33% in meno
#                   della media; ln(1.419/1.022)=0.329). Ipotesi §7 confermata.
#   La Liga δ=0.22: promosse in linea con la Serie A (ln(1.291/1.038)=0.218).
# γ (vantaggio-casa, molto piu' forte in Liga) NON e' qui: il DC lo fitta dai dati.
PREMIER_LEAGUE: dict = {
    "half_life_days": 365.0,   # Fase 57 (730 peggiora, +0.0057)
    "shrinkage": 1.5,          # Fase 57 (curva piatta, come Serie A)
    "shots_blend": 0.75,       # xG di qualita' pari alla Serie A (EDA Fase 55)
    "blend_signal": "xg",
    "promoted_prior": 0.33,    # Fase 55/57: δ = ln(1.419/1.022) ≈ 0.33
}

LA_LIGA: dict = {
    "half_life_days": 365.0,   # Fase 57 (730 peggiora, +0.0015)
    "shrinkage": 1.5,          # Fase 57 (shrink 3.0 nel rumore, −0.0001)
    "shots_blend": 0.75,
    "blend_signal": "xg",
    "promoted_prior": 0.22,    # Fase 55/57: δ = ln(1.291/1.038) ≈ 0.22
}

# Registro delle configurazioni per lega. Nuova lega = nuova voce (ri-tarata).
LEAGUE_CONFIGS: dict[str, dict] = {
    "serie_a": SERIE_A,
    "premier_league": PREMIER_LEAGUE,
    "la_liga": LA_LIGA,
}


def league_config(league_key: str) -> dict:
    """Config ufficiale di una lega. Ignota → SERIE_A come fallback esplicito,
    ma va TARATA prima di fidarsi dei numeri su una lega nuova (§7)."""
    return LEAGUE_CONFIGS.get(league_key, SERIE_A)


# --------------------------------------------------------------------------- #
# Costanti del MOTORE market-implied, per lega (audit Fase 92).
#
# Fino alla Fase 92 `predict.py` applicava a TUTTE le leghe le costanti tarate
# sulla chiusura Serie A (θ=1.225, θ_DC=1.138, φ0=0.30, κ=1.5, sharpen_1x2),
# benche' la mappa per-lega fosse gia' stata misurata. Costo verificato in
# Premier: 1X2 0.9665 col router contro 0.9640 del motore liscio (e 0.9639 del
# mercato), pareggio previsto +2.7pp sopra il realizzato — e il danno viene
# dalla φ35, non dal θ.
#
# Regola: qui stanno solo le leve ADOTTATE. Quelle misurate positive ma ancora
# in panchina (PANCHINA.md) restano OFF di default, anche se promettenti.
#   Serie A  — tutto adottato (Fasi 41/44/51/52).
#   Premier  — motore LISCIO: la Fase 81 ha misurato che e' gia' l'ottimo su
#              ogni asse (ρ*=−0.06, θ*≈1, φ*=0); la Fase 79 che la φ35 li'
#              peggiora (il DC sovra-stima gia' i pareggi equilibrati inglesi).
#   La Liga  — motore LISCIO: θ≈1.2 (Fase 81) e φ35-sola sul GG (Fase 80) sono
#              misurate positive ma sono in PANCHINA, non adottate.
# Cambiare uno stato qui = spostare una voce in PANCHINA.md, con la fase.
MARKET_ENGINE: dict[str, dict] = {
    "serie_a": {
        "dp_theta": 1.225,      # Fase 52 (router v3 sul path market-implied)
        "dp_theta_dc": 1.138,   # Fase 52 (router v3 sul path DC)
        "phi0": 0.30,           # Fase 39/44 (φ35 sul market-implied)
        "kappa": 1.5,
        "sharpen_1x2": True,    # Fase 51 (dp_lvl: batte la chiusura in log-loss)
    },
    "premier_league": {
        "dp_theta": None, "dp_theta_dc": None,
        "phi0": 0.0, "kappa": 0.0, "sharpen_1x2": False,
    },
    "la_liga": {
        "dp_theta": None, "dp_theta_dc": None,
        "phi0": 0.0, "kappa": 0.0, "sharpen_1x2": False,
    },
}


def market_engine(league_key: str) -> dict:
    """Costanti del motore market-implied per la lega. Ignota -> motore LISCIO
    (nessuna correzione), che e' la scelta prudente: le correzioni hanno segno
    e livello per-lega e vanno misurate prima di attivarle (§7)."""
    return MARKET_ENGINE.get(league_key, dict(
        dp_theta=None, dp_theta_dc=None, phi0=0.0, kappa=0.0, sharpen_1x2=False))


# --------------------------------------------------------------------------- #
# DERIVA DI FORZA IN-STAGIONE (Fase 94) — per il simulatore di stagione.
#
# La forza di una squadra cambia durante l'anno in modo IMPREVEDIBILE a luglio,
# e un modello a forze fisse la ignora: la classifica simulata esce piu'
# schiacciata di quella vera (la dispersione reale supera la simulata in 21
# stagioni su 24). Misurata su 480 squadre-stagione confrontando il fit di
# inizio e di fine stagione, e NON e' uniforme:
#     neopromosse   sd 0.299     (deriva quasi doppia)
#     tutte le altre sd 0.157
# Un sigma uniforme perturba troppo le forti e troppo poco le deboli.
#
# ADOZIONE PER-MERCATO (§1.8), secondo cio' che l'evidenza sostiene:
#   RETROCESSIONE -> ADOTTATA: log-loss +0.0095 con IC95% [+0.0020,+0.0180]
#     (esclude lo zero), calibrazione delle neopromosse da +6.1pp a +2.8pp,
#     ECE da 0.0479 a 0.0387.
#   CAMPIONE      -> nessun effetto (+0.0017, meglio in 9 stagioni su 24).
#   TOP-4         -> NON adottata: peggiora in 17 stagioni su 24 e l'ECE sale
#     da 0.0140 a 0.0203. Il top-4 era gia' calibrato: aggiungere incertezza a
#     una previsione gia' giusta puo' solo peggiorarla.
DRIFT_SD = {"promoted": 0.30, "other": 0.16}


def drift_sd_map(teams, promoted) -> dict:
    """sigma della deriva per squadra (Fase 94). Da passare a simulate_season
    come ``drift_sd``. Usare per il mercato RETROCESSIONE; per campione e top-4
    l'evidenza non la sostiene."""
    return {t: (DRIFT_SD["promoted"] if t in promoted else DRIFT_SD["other"])
            for t in teams}
