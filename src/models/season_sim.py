"""Simulazione Monte Carlo di una STAGIONE intera (Fase 89): dal DC al campione.

Perche' serve un modulo nuovo: fino alla Fase 88 il progetto prezzava mercati
della SINGOLA partita (1X2, O/U, GG/NG, esatto, handicap...), tutti derivabili
dalla matrice dei punteggi di quell'incontro. Il mercato "campione di stagione"
(outright winner) e' di natura diversa: dipende da **380 partite congiuntamente**
e da una regola di classifica. Non si ricava da una matrice: va SIMULATO.

Idea:
  1. si fitta il Dixon-Coles a inizio stagione (walk-forward: solo dati passati);
  2. per ognuno dei 380 incontri si ottiene la matrice P(gol_casa=i, gol_ospite=j);
  3. si campionano N stagioni intere da quelle matrici;
  4. in ogni stagione simulata si compila la classifica con le REGOLE UFFICIALI
     della lega e si guarda chi vince;
  5. P(campione) = frazione di stagioni simulate vinte da ciascuna squadra.

DUE PROPRIETA' NON OVVIE, entrambe verificate alla Fase 89:

(a) **L'ordine del calendario e' irrilevante.** Con forze COSTANTI dentro la
    stagione (quello che il DC assume), i punti finali dipendono solo
    dall'INSIEME degli incontri — un girone doppio completo — non dalla loro
    sequenza. Conseguenza pratica: si puo' simulare una stagione FUTURA senza
    conoscerne il calendario (che per il 2026-27 non abbiamo). Se un giorno il
    modello avesse dinamica in-season, questa proprieta' cadrebbe.

(b) **Gli spareggi contano davvero.** Nelle stagioni simulate la parita' di punti
    in testa capita nel ~5% dei casi (molto piu' che nella realta' osservata:
    0 volte su 27 stagioni reali). E le regole DIFFERISCONO per lega: Serie A e
    La Liga usano la CLASSIFICA AVULSA fra le squadre a pari punti, la Premier
    la DIFFERENZA RETI. Non e' pedanteria: nel 2025-26 la Liga ha chiuso con
    Levante, Osasuna e Mallorca TUTTE E TRE a 42 punti, e l'avulsa fra le tre
    (Levante 7 - Osasuna 5 - Mallorca 3) le ha ordinate 16a/17a/18a facendo
    retrocedere Mallorca; con la sola differenza reti generale (-6/-10/-14)
    sarebbe retrocesso Levante. Cambia la composizione della lega 2026-27.

Limite dichiarato (Fase 89): le forze delle squadre sono stimate a inizio
stagione e tenute FISSE per 10 mesi. Il simulatore cattura quindi solo
l'aleatorieta' dei risultati, NON l'incertezza sui parametri ne' la loro
evoluzione (mercato estivo, infortuni, cambi allenatore). Risultato misurato:
le probabilita' sul favorito escono SOVRASTIMATE (60.1% dichiarato contro 41.7%
realizzato sulle 24 stagioni di backtest).
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

# Ordine dei criteri di spareggio per lega, dopo i punti.
#   "h2h"  = classifica avulsa: punti negli scontri diretti fra le squadre a pari
#            punti, poi differenza reti negli scontri diretti;
#   "gd"   = differenza reti generale; "gf" = gol fatti.
# Serie A e La Liga: scontri diretti PRIMA della differenza reti generale.
# Premier League: differenza reti, poi gol fatti (gli scontri diretti NON sono
# un criterio di classifica; a parita' totale e' previsto uno spareggio).
TIEBREAK_RULES: dict[str, tuple[str, ...]] = {
    "serie_a": ("h2h", "gd", "gf"),
    "la_liga": ("h2h", "gd", "gf"),
    "premier_league": ("gd", "gf"),
}
DEFAULT_TIEBREAK = ("gd", "gf")


def league_tiebreak(league_key: str) -> tuple[str, ...]:
    """Criteri di spareggio della lega (dopo i punti). Ignota -> differenza reti."""
    return TIEBREAK_RULES.get(league_key, DEFAULT_TIEBREAK)


# --------------------------------------------------------------------------- #
# Classifica REALE (verita' di riferimento)                                    #
# --------------------------------------------------------------------------- #
def final_table(matches: pd.DataFrame, league_key: str = "serie_a") -> pd.DataFrame:
    """Classifica finale da risultati reali, con gli spareggi ufficiali della lega.

    3 punti a vittoria, 1 a pareggio. Ritorna un DataFrame ordinato (1o in cima)
    con punti, gol fatti/subiti, differenza reti e il criterio che ha risolto
    eventuali parita'.

    ATTENZIONE (limite dichiarato): le PENALIZZAZIONI di punti non sono nei dati
    (gli snapshot contengono solo risultati), quindi questa classifica puo'
    differire da quella ufficiale nelle stagioni con penalizzazioni. Sul
    CAMPIONE non cambia nulla nelle 27 stagioni del progetto (verificato alla
    Fase 89: nessuna penalizzazione ha mai coinvolto la vetta), ma sulle
    posizioni di meta'/bassa classifica si'.
    """
    teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
    rec = {t: dict(pts=0, gf=0, ga=0, w=0, d=0, l=0) for t in teams}
    for r in matches.itertuples():
        h, a = r.home_team, r.away_team
        hg, ag = int(r.home_goals), int(r.away_goals)
        rec[h]["gf"] += hg; rec[h]["ga"] += ag
        rec[a]["gf"] += ag; rec[a]["ga"] += hg
        if hg > ag:
            rec[h]["pts"] += 3; rec[h]["w"] += 1; rec[a]["l"] += 1
        elif hg < ag:
            rec[a]["pts"] += 3; rec[a]["w"] += 1; rec[h]["l"] += 1
        else:
            rec[h]["pts"] += 1; rec[a]["pts"] += 1
            rec[h]["d"] += 1; rec[a]["d"] += 1
    table = pd.DataFrame(rec).T
    table["gd"] = table["gf"] - table["ga"]

    rules = league_tiebreak(league_key)
    # Chiave di ordinamento: punti, poi i criteri della lega. Gli scontri diretti
    # dipendono dal GRUPPO di squadre a pari punti, quindi si risolvono a gruppi.
    order: list[str] = []
    for pts_val in sorted(table["pts"].unique(), reverse=True):
        group = table[table["pts"] == pts_val]
        if len(group) == 1:
            order.extend(group.index.tolist())
            continue
        order.extend(_break_tie(group.index.tolist(), matches, table, rules))
    return table.loc[order]


def _break_tie(tied: list[str], matches: pd.DataFrame, table: pd.DataFrame,
               rules: tuple[str, ...]) -> list[str]:
    """Ordina un gruppo di squadre a pari punti secondo i criteri della lega."""
    stats: dict[str, list[float]] = {}
    if "h2h" in rules:
        sub = matches[matches["home_team"].isin(tied) & matches["away_team"].isin(tied)]
        h2h_pts = dict.fromkeys(tied, 0.0)
        h2h_gd = dict.fromkeys(tied, 0.0)
        for r in sub.itertuples():
            h, a = r.home_team, r.away_team
            hg, ag = int(r.home_goals), int(r.away_goals)
            h2h_gd[h] += hg - ag; h2h_gd[a] += ag - hg
            if hg > ag:
                h2h_pts[h] += 3
            elif hg < ag:
                h2h_pts[a] += 3
            else:
                h2h_pts[h] += 1; h2h_pts[a] += 1
    for t in tied:
        key: list[float] = []
        for rule in rules:
            if rule == "h2h":
                key += [h2h_pts[t], h2h_gd[t]]
            elif rule == "gd":
                key.append(float(table.loc[t, "gd"]))
            elif rule == "gf":
                key.append(float(table.loc[t, "gf"]))
        stats[t] = key
    # ordine decrescente su tutti i criteri; parita' totale -> ordine alfabetico
    # (stabile e riproducibile; nella realta' sarebbe sorteggio o spareggio)
    return sorted(tied, key=lambda t: (*[-v for v in stats[t]], t))


# --------------------------------------------------------------------------- #
# Simulazione                                                                  #
# --------------------------------------------------------------------------- #
def round_robin(teams: list[str]) -> list[tuple[str, str]]:
    """Girone doppio completo: ogni coppia si affronta in casa e in trasferta.

    Usato per le stagioni FUTURE, di cui non conosciamo il calendario. Legittimo
    perche' con forze costanti l'ordine non conta (vedi nota (a) nel modulo)."""
    return [(h, a) for h, a in itertools.permutations(teams, 2)]


def simulate_season(
    model,
    fixtures: list[tuple[str, str]],
    teams: list[str],
    league_key: str = "serie_a",
    n_sims: int = 20000,
    seed: int = 0,
    chunk: int = 2000,
    features=None,
    drift_sd: float | dict = 0.0,
    n_drift_draws: int = 200,
) -> dict:
    """Campiona ``n_sims`` stagioni intere e ritorna le statistiche finali.

    Args:
        model: DixonColesModel gia' fittato (as_of_date = inizio stagione!).
        fixtures: lista di (casa, ospite). Per una stagione futura: round_robin().
        teams: squadre della lega in quella stagione.
        league_key: per le regole di spareggio (vedi TIEBREAK_RULES).
        n_sims: numero di stagioni simulate. L'errore Monte Carlo su una
            probabilita' p e' sqrt(p(1-p)/n): con n=20000 e p=0.5 vale 0.35
            punti percentuali, trascurabile rispetto agli scarti che misuriamo.
        features: opzionale, ``f(casa, ospite) -> dict`` con i valori di partita
            per le covariate del DC (Fase 4c). Serve per confrontare varianti
            CON e SENZA covariata usando lo STESSO simulatore: reimplementare il
            ciclo fuori di qui fa divergere le due braccia (audit Fase 90: il
            test su squad_value confrontava due regole di spareggio diverse e
            ~9% del suo delta era artefatto).
        drift_sd: DERIVA DI FORZA IN-STAGIONE (Fase 94). Scalare (uguale per
            tutte) oppure dict {squadra: sigma} — la deriva NON e' uniforme:
            misurata su 480 squadre-stagione vale 0.299 per le neopromosse e
            0.157 per tutte le altre (1.9x). Con forze fisse il
            simulatore produce classifiche piu' SCHIACCIATE del vero: la
            dispersione reale supera la simulata in 21 stagioni su 24
            (percentile medio 83%, dovrebbe essere 50%). Il motivo non e' che le
            squadre siano piu' diverse di quanto stimiamo, ma che la loro forza
            CAMBIA durante l'anno in modo imprevedibile a luglio — e quella e'
            incertezza, non separazione. Qui si aggiunge alla forza netta di
            ogni squadra una perturbazione ``N(0, drift_sd)`` costante dentro
            una stagione simulata e ri-estratta a ogni "draw". 0 = disattivata.
        n_drift_draws: quante estrazioni della deriva (le simulazioni si
            dividono equamente fra loro). Ogni draw costa il ricalcolo delle
            matrici dei punteggi, quindi il costo scala con questo numero, non
            con n_sims.

    Ritorna un dict con:
        champion_prob : array [n_teams] con P(campione), con gli spareggi di lega
        points        : matrice [n_sims x n_teams] dei punti finali
        rank          : matrice [n_sims x n_teams] delle posizioni (1 = primo).
            ATTENZIONE: dalla 2a posizione in giu' l'ordine e' punti -> differenza
            reti -> gol fatti, NON gli spareggi ufficiali (che sono applicati solo
            alla vetta, l'unica che ci serve). La posizione 1 e' invece sempre
            coerente con ``champion_prob``.
        tie_rate      : frazione di stagioni con parita' di PUNTI in testa
        teams         : la lista delle squadre (ordine delle colonne)
    """
    if not model.fitted:
        raise RuntimeError("Il modello non e' stato fittato.")
    # GUARDIA (Fase 89): una squadra assente dal modello NON solleva errori --
    # expected_goals() usa .get(team, 0.0) e la tratterebbe come "media". Ma solo
    # l'ATTACCO e' centrato a 0 dalla penalita' di identificabilita': la DIFESA
    # media non e' 0 (in Premier 2026-27 vale +0.149), quindi una squadra
    # mancante verrebbe silenziosamente dotata di una difesa MIGLIORE della
    # media. Meglio fallire subito: chi manca va passato a fit(promoted_teams=)
    # per ricevere il prior di cold-start.
    missing = [t for t in teams if t not in model.attack]
    if missing:
        raise ValueError(
            f"squadre assenti dal modello: {missing}. Passale a "
            f"fit(promoted_teams=...) cosi' partono dal prior neopromosse, "
            f"invece di ereditare in silenzio una difesa sopra la media.")
    ti = {t: k for k, t in enumerate(teams)}
    n_t, n_f = len(teams), len(fixtures)

    # CDF cumulata sulle 121 celle della matrice dei punteggi, una per incontro.
    K = model.max_goals + 1

    def build_cdfs(shift: dict | None = None) -> np.ndarray:
        """Matrici dei punteggi -> cumulate, eventualmente con la forza di ogni
        squadra spostata di ``shift[t]`` (deriva in-stagione)."""
        if shift:
            base_a = dict(model.attack)
            base_d = dict(model.defense)
            # la deriva agisce sulla forza NETTA (attacco - difesa): meta' su
            # ciascuna colonna, cosi' il livello dei gol della lega non si sposta
            for t, s in shift.items():
                model.attack[t] = base_a.get(t, 0.0) + s / 2.0
                model.defense[t] = base_d.get(t, 0.0) - s / 2.0
        out = np.empty((n_f, K * K))
        for n, (h, a) in enumerate(fixtures):
            f = features(h, a) if features else None
            out[n] = np.cumsum(model.predict_match(h, a, features=f).score_matrix.ravel())
        if shift:
            model.attack, model.defense = base_a, base_d      # ripristina
        # _score_matrix rinormalizza gia' a 1: questa divisione e' una
        # salvaguardia (sposta massa per ~1e-16), non una correzione necessaria.
        return out / out[:, -1:]

    cdfs = build_cdfs()

    hidx = np.array([ti[h] for h, _ in fixtures])
    aidx = np.array([ti[a] for _, a in fixtures])
    rules = league_tiebreak(league_key)
    # Per gli scontri diretti serve sapere quali incontri legano due squadre.
    need_h2h = "h2h" in rules

    rng = np.random.default_rng(seed)
    points = np.zeros((n_sims, n_t), np.int16)
    gdiff = np.zeros((n_sims, n_t), np.int16)
    gfor = np.zeros((n_sims, n_t), np.int16)
    champion = np.zeros(n_sims, np.int16)
    tied_top = np.zeros(n_sims, bool)

    # Con la deriva attiva, le simulazioni si dividono fra `n_drift_draws`
    # estrazioni: dentro un'estrazione le forze sono fisse (la deriva e' una
    # proprieta' della STAGIONE, non della partita), fra estrazioni cambiano.
    # sigma per-squadra: uno scalare vale per tutte, un dict permette di dare
    # PIU' deriva alle squadre che ne hanno di piu' (misurato: neopromosse 0.299
    # contro 0.157 di tutte le altre, cioe' 1.9x). Un sigma uniforme perturba
    # troppo le forti e troppo poco le deboli.
    sd_of = ({t: float(drift_sd) for t in teams} if np.isscalar(drift_sd)
             else {t: float(drift_sd.get(t, 0.0)) for t in teams})
    drift_active = any(v > 0 for v in sd_of.values())
    if drift_active:
        chunk = max(1, int(np.ceil(n_sims / n_drift_draws)))

    for s0 in range(0, n_sims, chunk):
        s1 = min(s0 + chunk, n_sims)
        if drift_active:
            cdfs = build_cdfs({t: float(rng.normal(0.0, sd_of[t])) for t in teams})
        u = rng.random((s1 - s0, n_f))
        # cella campionata -> (gol casa, gol ospite)
        cell = np.empty((s1 - s0, n_f), np.int16)
        for n in range(n_f):
            cell[:, n] = np.searchsorted(cdfs[n], u[:, n])
        hg = (cell // K).astype(np.int16)
        ag = (cell % K).astype(np.int16)
        hw, aw, dr = hg > ag, hg < ag, hg == ag
        for n in range(n_f):
            points[s0:s1, hidx[n]] += 3 * hw[:, n] + dr[:, n]
            points[s0:s1, aidx[n]] += 3 * aw[:, n] + dr[:, n]
            gdiff[s0:s1, hidx[n]] += hg[:, n] - ag[:, n]
            gdiff[s0:s1, aidx[n]] += ag[:, n] - hg[:, n]
            gfor[s0:s1, hidx[n]] += hg[:, n]
            gfor[s0:s1, aidx[n]] += ag[:, n]

        # --- campione del blocco, con spareggi ---
        p_blk = points[s0:s1]
        top = p_blk.max(axis=1, keepdims=True)
        is_top = p_blk == top
        n_top = is_top.sum(axis=1)
        champ_blk = np.argmax(is_top, axis=1)      # primo indice a pari punti
        multi = np.flatnonzero(n_top > 1)
        tied_top[s0:s1] = n_top > 1
        for s in multi:
            cand = np.flatnonzero(is_top[s])
            champ_blk[s] = _resolve_sim_tie(
                cand, s, s0, gdiff, gfor, rules, hg, ag, hidx, aidx, need_h2h)
        champion[s0:s1] = champ_blk

    # posizione in classifica (1 = primo) con chiave punti -> gd -> gf
    key = (points.astype(np.int64) * 10_000_000
           + (gdiff.astype(np.int64) + 200) * 10_000
           + gfor.astype(np.int64))
    rank = (-key).argsort(axis=1).argsort(axis=1) + 1
    # Coerenza con champion_prob: dove gli spareggi di lega hanno assegnato la
    # vetta a una squadra diversa da quella che vince per differenza reti, si
    # scambiano le due posizioni. Senza questo, `rank` e `champion_prob` si
    # contraddicono nell'~1% delle simulazioni di Serie A/Liga (audit Fase 90).
    wrong = rank[np.arange(n_sims), champion] != 1
    if wrong.any():
        idx = np.flatnonzero(wrong)
        other = rank[idx].argmin(axis=1)          # chi era in testa per gd/gf
        r_ch = rank[idx, champion[idx]]
        rank[idx, other] = r_ch
        rank[idx, champion[idx]] = 1

    counts = np.bincount(champion, minlength=n_t)
    return dict(
        champion_prob=counts / n_sims,
        points=points,
        rank=rank,
        tie_rate=float(tied_top.mean()),
        teams=list(teams),
    )


def _resolve_sim_tie(cand, s, s0, gdiff, gfor, rules, hg, ag, hidx, aidx,
                     need_h2h) -> int:
    """Risolve una parita' di punti in testa DENTRO una stagione simulata."""
    if need_h2h:
        cand_set = set(cand.tolist())
        h2h_p = dict.fromkeys(cand.tolist(), 0)
        h2h_g = dict.fromkeys(cand.tolist(), 0)
        for n in range(len(hidx)):
            h, a = int(hidx[n]), int(aidx[n])
            if h in cand_set and a in cand_set:
                gh, ga = int(hg[s, n]), int(ag[s, n])
                h2h_g[h] += gh - ga; h2h_g[a] += ga - gh
                if gh > ga:
                    h2h_p[h] += 3
                elif gh < ga:
                    h2h_p[a] += 3
                else:
                    h2h_p[h] += 1; h2h_p[a] += 1

    def sort_key(k: int):
        out: list[float] = []
        for rule in rules:
            if rule == "h2h":
                out += [-h2h_p[k], -h2h_g[k]]
            elif rule == "gd":
                out.append(-float(gdiff[s0 + s, k]))
            elif rule == "gf":
                out.append(-float(gfor[s0 + s, k]))
        return (*out, k)

    return int(min(cand.tolist(), key=sort_key))
