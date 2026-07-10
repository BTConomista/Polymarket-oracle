"""Modello Dixon-Coles per la distribuzione dei gol nel calcio.

Idea di fondo (Dixon & Coles, 1997, "Modelling Association Football Scores and
Inefficiencies in the Football Betting Market"):

  - ogni squadra ha una forza d'ATTACCO e una di DIFESA;
  - i gol segnati in casa e in trasferta seguono due Poisson i cui tassi attesi
    dipendono da attacco della squadra che segna, difesa dell'avversaria e un
    vantaggio-casa globale:

        lambda (gol attesi casa)     = exp(attacco_casa + difesa_ospite + vantaggio_casa)
        mu     (gol attesi ospite)   = exp(attacco_ospite + difesa_casa)

  - una CORREZIONE (parametro rho) sui punteggi bassi (0-0, 1-0, 0-1, 1-1),
    perche' nella realta' quei risultati sono piu' frequenti di quanto una
    Poisson pura preveda (le squadre "giocano sul risultato");

  - un DECADIMENTO TEMPORALE: le partite recenti pesano piu' di quelle vecchie
    nella stima (le squadre cambiano nel tempo).

Da questo modello si ricava la matrice P(gol_casa = i, gol_ospite = j), e da
quella matrice si derivano TUTTI i mercati (1X2, Over/Under, ecc.) in modo
coerente: un solo modello, nessuna incoerenza tra mercati.

Perche' scritto a mano invece di usare una libreria: vogliamo capire e controllare
ogni riga (e' il cuore del progetto), testarlo, ed estenderlo senza dipendere da
pacchetti di terze parti poco mantenuti.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

# Penalita' che fissa l'unica indeterminazione del modello (vedi nota in fit()).
_IDENTIFIABILITY_PENALTY = 1e4

# Segnali secondari mescolabili col modello-gol (colonne dello schema interno).
_BLEND_SIGNALS: dict[str, tuple[str, str]] = {
    "sot": ("home_sot", "away_sot"),      # tiri in porta (Fase 3)
    "xg": ("home_xg", "away_xg"),         # expected goals reali (Fase 4b)
    "npxg": ("home_npxg", "away_npxg"),   # xG senza rigori
}

# Covariate di partita: forza/contesto ESTERNI ai risultati (Fase 4c). Ogni voce
# definisce le colonne per-squadra e la trasformazione da applicare al valore
# grezzo prima di standardizzarlo. La covariata entra nel tasso atteso della
# squadra che segna come beta * (z_squadra - z_avversaria): un vantaggio relativo
# fa segnare di piu' (o di meno, se beta<0, es. per le assenze).
_COVARIATES: dict[str, tuple[str, str, str]] = {
    "squad_value": ("home_squad_value", "away_squad_value", "log"),
    "absence": ("home_absent_value_est", "away_absent_value_est", "log1p"),
    "rest": ("home_rest_days", "away_rest_days", "identity"),  # riposo/congestione (solo Serie A)
    "rest_full": ("home_rest_days_full", "away_rest_days_full", "identity"),  # riposo/congestione VERA (calendario completo di club, Fase 4e)
}


def _cov_transform(values: np.ndarray, kind: str) -> np.ndarray:
    """Trasforma i valori grezzi di una covariata (log / log1p / identita')."""
    if kind == "log":
        return np.log(np.where(values > 0, values, np.nan))
    if kind == "log1p":
        return np.log1p(np.where(values >= 0, values, np.nan))
    return values.astype(float)


@dataclass
class MatchPrediction:
    """Risultato di una predizione su una singola partita.

    Le probabilita' sono coerenti tra loro perche' derivano tutte dalla stessa
    matrice dei punteggi.
    """

    home_team: str
    away_team: str
    exp_home_goals: float
    exp_away_goals: float
    prob_home_win: float
    prob_draw: float
    prob_away_win: float
    prob_over_2_5: float
    prob_under_2_5: float
    prob_btts_yes: float   # GG: entrambe segnano
    prob_btts_no: float    # NG: almeno una non segna
    score_matrix: np.ndarray = field(repr=False)

    # --- Mercati derivati (dalle stesse probabilita', gratis e coerenti) ---
    @property
    def prob_1x(self) -> float:      # doppia chance: casa o pareggio
        return self.prob_home_win + self.prob_draw

    @property
    def prob_2x(self) -> float:      # doppia chance: ospite o pareggio
        return self.prob_away_win + self.prob_draw

    @property
    def prob_12(self) -> float:      # doppia chance: casa o ospite (no pareggio)
        return self.prob_home_win + self.prob_away_win

    def as_row(self) -> dict:
        """Versione "piatta" (senza la matrice) comoda per tabelle/CSV."""
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "exp_home_goals": round(self.exp_home_goals, 3),
            "exp_away_goals": round(self.exp_away_goals, 3),
            "prob_home_win": round(self.prob_home_win, 4),
            "prob_draw": round(self.prob_draw, 4),
            "prob_away_win": round(self.prob_away_win, 4),
            "prob_over_2_5": round(self.prob_over_2_5, 4),
            "prob_under_2_5": round(self.prob_under_2_5, 4),
            "prob_btts_yes": round(self.prob_btts_yes, 4),
            "prob_1x": round(self.prob_1x, 4),
            "prob_2x": round(self.prob_2x, 4),
            "prob_12": round(self.prob_12, 4),
        }


def _tau(goals_home, goals_away, lam, mu, rho):
    """Correzione Dixon-Coles sui 4 punteggi bassi. Vettorializzata."""
    tau = np.ones_like(lam, dtype=float)
    m00 = (goals_home == 0) & (goals_away == 0)
    m01 = (goals_home == 0) & (goals_away == 1)
    m10 = (goals_home == 1) & (goals_away == 0)
    m11 = (goals_home == 1) & (goals_away == 1)
    tau[m00] = 1.0 - lam[m00] * mu[m00] * rho
    tau[m01] = 1.0 + lam[m01] * rho
    tau[m10] = 1.0 + mu[m10] * rho
    tau[m11] = 1.0 - rho
    return tau


class DixonColesModel:
    """Stima e uso del modello Dixon-Coles.

    Uso tipico:
        model = DixonColesModel(half_life_days=180)
        model.fit(matches_df, as_of_date=pd.Timestamp("2025-08-01"))
        pred = model.predict_match("Inter", "Milan")
    """

    def __init__(
        self,
        half_life_days: float = 180.0,
        max_goals: int = 10,
        shrinkage: float = 0.0,
        shots_blend: float = 1.0,
        blend_signal: str = "sot",
        covariates: tuple[str, ...] = (),
        promoted_prior: tuple[float, float] | None = None,
    ):
        """
        Args:
            half_life_days: dopo quanti giorni il peso di una partita si dimezza
                nella stima (decadimento temporale). Piu' piccolo = piu' reattivo
                ma piu' rumoroso. None/inf = nessun decadimento (tutte uguali).
            max_goals: numero massimo di gol per squadra considerato nella matrice
                dei punteggi (troncamento; 10 e' abbondante per il calcio).
            shrinkage: forza della regolarizzazione L2 che tira attacco/difesa
                verso la media della lega (0). Poiche' la penalita' e' fissa mentre
                il contributo dei dati cresce col numero di partite, l'effetto e'
                AUTOMATICAMENTE piu' forte sulle squadre con pochi dati
                (neopromosse, inizio stagione). 0 = nessuna regolarizzazione.
            shots_blend: peso alpha del segnale GOL rispetto al SEGNALE SECONDARIO
                (vedi blend_signal) nella stima dei gol attesi. I gol sono rumorosi
                (fortuna sotto porta); il segnale secondario misura le occasioni con
                meno rumore. Si allena un modello sui gol e uno sul segnale, e si
                mescolano i tassi:
                    gol_attesi = alpha * (dai gol) + (1-alpha) * (dal segnale)
                alpha=1 -> solo gol (modello classico); alpha=0 -> solo segnale;
                valori intermedi -> miscela. Tarabile via scripts/tune.py.
            blend_signal: quale segnale secondario mescolare quando shots_blend < 1:
                "sot" = tiri in porta (Fase 3, non aiuta), "xg" = expected goals
                reali (Fase 4b, qualita' delle occasioni), "npxg" = xG senza rigori.
            covariates: covariate di partita da aggiungere al modello-gol (Fase 4c),
                es. ("squad_value",) o ("squad_value", "absence"). Entrano nel tasso
                atteso come termini beta*(z_squadra - z_avversaria), stimati insieme
                agli altri parametri. Combinarne piu' di una cattura (in fit
                congiunto) il loro contributo reciproco. () = nessuna covariata
                (modello identico a prima).
            promoted_prior: prior di cold-start per le NEOPROMOSSE (Fase 7). Coppia
                ``(delta_att, delta_def)`` in unita' di log-tasso: il bersaglio
                dello shrinkage per le squadre passate a ``fit(promoted_teams=...)``
                diventa attacco ``-delta_att`` e difesa ``+delta_def`` (piu' debole)
                invece di 0 (la media). Storicamente le neopromosse segnano ~20% in
                meno e subiscono ~25% in piu' (delta ~0.23): il modello base, senza
                storico, le sovrastima. Una neopromossa con 0 partite finisce
                esattamente sul prior; man mano che gioca, i dati lo sovrastano
                (stesso meccanismo dello shrinkage). None = disattivato.
        """
        if blend_signal not in _BLEND_SIGNALS:
            raise ValueError(f"blend_signal sconosciuto: {blend_signal!r} "
                             f"(usa uno di {list(_BLEND_SIGNALS)})")
        unknown = [c for c in covariates if c not in _COVARIATES]
        if unknown:
            raise ValueError(f"covariate sconosciute: {unknown} "
                             f"(usa un sottoinsieme di {list(_COVARIATES)})")
        self.half_life_days = half_life_days
        self.max_goals = max_goals
        self.shrinkage = shrinkage
        self.shots_blend = shots_blend
        self.blend_signal = blend_signal
        self.covariates = tuple(covariates)
        self.promoted_prior = promoted_prior

        # Parametri stimati sui GOL (riempiti da fit()).
        self.teams: list[str] = []
        self.attack: dict[str, float] = {}
        self.defense: dict[str, float] = {}
        self.home_advantage: float = 0.0
        self.rho: float = 0.0

        # Parametri stimati sul SEGNALE SECONDARIO (solo se shots_blend < 1).
        self.attack_sig: dict[str, float] = {}
        self.defense_sig: dict[str, float] = {}
        self.home_advantage_sig: float = 0.0
        # Tasso di conversione segnale -> gol (per riportare il segnale su scala gol;
        # per l'xG e' ~1, per i tiri in porta ~0.3).
        self.conv_home: float = 1.0
        self.conv_away: float = 1.0

        # Covariate (Fase 4c): coefficienti beta e parametri di standardizzazione
        # (media/dev.std del valore per-squadra trasformato, sul training).
        self.beta: dict[str, float] = {}
        self.cov_mean: dict[str, float] = {}
        self.cov_std: dict[str, float] = {}

        self.fitted: bool = False

    # ------------------------------------------------------------------ #
    # Covariate (Fase 4c)
    # ------------------------------------------------------------------ #
    def _team_cov_z(self, name: str, home_vals: np.ndarray,
                    away_vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Valori standardizzati (z) per casa/ospite di una covariata, usando
        media/dev.std imparate in fit. Valori mancanti -> 0 (neutro)."""
        home, away, kind = _COVARIATES[name]
        m, s = self.cov_mean[name], self.cov_std[name]
        zh = (_cov_transform(home_vals, kind) - m) / s
        za = (_cov_transform(away_vals, kind) - m) / s
        return np.nan_to_num(zh), np.nan_to_num(za)

    def _cov_lam(self, matches: pd.DataFrame) -> np.ndarray:
        """Matrice [n_partite x n_covariate] del contributo (z_casa - z_ospite)
        al tasso della squadra di CASA. Per l'ospite il segno e' opposto."""
        cols = []
        for name in self.covariates:
            hcol, acol, _ = _COVARIATES[name]
            zh, za = self._team_cov_z(name, matches[hcol].to_numpy(float),
                                      matches[acol].to_numpy(float))
            cols.append(zh - za)
        return np.column_stack(cols) if cols else np.empty((len(matches), 0))

    # ------------------------------------------------------------------ #
    # Stima dei parametri
    # ------------------------------------------------------------------ #
    def _time_weights(self, dates: pd.Series, as_of: pd.Timestamp) -> np.ndarray:
        """Peso di ogni partita in base a quanto e' lontana da ``as_of``."""
        if self.half_life_days is None or math.isinf(self.half_life_days):
            return np.ones(len(dates))
        days_before = (as_of - dates).dt.total_seconds().to_numpy() / 86400.0
        days_before = np.clip(days_before, 0.0, None)
        xi = math.log(2.0) / self.half_life_days
        return np.exp(-xi * days_before)

    def fit(
        self,
        matches: pd.DataFrame,
        as_of_date: pd.Timestamp | None = None,
        promoted_teams: set[str] | None = None,
    ) -> "DixonColesModel":
        """Stima i parametri via massima verosimiglianza pesata.

        Usa SOLO le partite con data < ``as_of_date`` (evita il look-ahead:
        non guarda mai il futuro rispetto al momento della predizione).

        Args:
            matches: DataFrame nello schema interno (vedi data/loader.py).
            as_of_date: momento "presente". Le partite successive sono ignorate
                e il decadimento temporale e' calcolato rispetto a questa data.
                Default: il giorno dopo l'ultima partita disponibile.
            promoted_teams: squadre a cui applicare il ``promoted_prior`` (Fase 7).
                Vengono incluse nel modello anche se non hanno ancora partite nel
                training (inizio stagione), cosi' partono dal prior invece che
                dalla media. Ignorato se ``promoted_prior`` non e' impostato.
        """
        if as_of_date is None:
            as_of_date = matches["date"].max() + pd.Timedelta(days=1)

        train = matches[matches["date"] < as_of_date].copy()
        if train.empty:
            raise ValueError("Nessuna partita disponibile prima di as_of_date.")

        # Le neopromosse col prior entrano nel modello anche a 0 partite: senza
        # dati lo shrinkage le porta esattamente sul prior (cold-start onesto).
        prior_teams = (promoted_teams or set()) if self.promoted_prior else set()
        teams = sorted(set(train["home_team"]) | set(train["away_team"]) | prior_teams)
        idx = {t: k for k, t in enumerate(teams)}
        self.teams = teams

        # Bersaglio dello shrinkage: 0 (media) per tutti, spostato per le promosse.
        attack_prior = np.zeros(len(teams))
        defense_prior = np.zeros(len(teams))
        if self.promoted_prior and prior_teams:
            d_att, d_def = self.promoted_prior
            for t in prior_teams:
                attack_prior[idx[t]] = -d_att   # segna meno
                defense_prior[idx[t]] = d_def   # subisce di piu'

        # --- Covariate (Fase 4c): impara la standardizzazione sul training ---
        for name in self.covariates:
            hcol, acol, kind = _COVARIATES[name]
            pooled = np.concatenate([
                _cov_transform(train[hcol].to_numpy(float), kind),
                _cov_transform(train[acol].to_numpy(float), kind),
            ])
            pooled = pooled[~np.isnan(pooled)]
            self.cov_mean[name] = float(pooled.mean()) if pooled.size else 0.0
            std = float(pooled.std()) if pooled.size else 1.0
            self.cov_std[name] = std if std > 1e-9 else 1.0

        # --- Modello sui GOL (sempre) ---
        home_idx = train["home_team"].map(idx).to_numpy()
        away_idx = train["away_team"].map(idx).to_numpy()
        weights = self._time_weights(train["date"], as_of_date)
        cov_lam = self._cov_lam(train)  # [n x k], k = numero covariate
        attack, defense, home_adv, rho, beta = self._fit_counts(
            len(teams), home_idx, away_idx,
            train["home_goals"].to_numpy().astype(float),
            train["away_goals"].to_numpy().astype(float),
            weights, use_correction=True, cov_lam=cov_lam,
            attack_prior=attack_prior, defense_prior=defense_prior,
        )
        self.attack = {t: attack[idx[t]] for t in teams}
        self.defense = {t: defense[idx[t]] for t in teams}
        self.home_advantage = home_adv
        self.rho = rho
        self.beta = {name: float(beta[i]) for i, name in enumerate(self.covariates)}

        # --- Modello sul SEGNALE SECONDARIO (solo se serve mescolarlo) ---
        if self.shots_blend < 1.0:
            home_col, away_col = _BLEND_SIGNALS[self.blend_signal]
            sig = train.dropna(subset=[home_col, away_col])
            if sig.empty:
                raise ValueError(
                    f"shots_blend < 1 ma mancano i dati del segnale "
                    f"'{self.blend_signal}' ({home_col}/{away_col}).")
            s_home_idx = sig["home_team"].map(idx).to_numpy()
            s_away_idx = sig["away_team"].map(idx).to_numpy()
            s_weights = self._time_weights(sig["date"], as_of_date)
            sig_home = sig[home_col].to_numpy().astype(float)
            sig_away = sig[away_col].to_numpy().astype(float)
            # Segnale ad alto volume / continuo (tiri, xG): niente correzione sui
            # punteggi bassi (serve solo il tasso atteso, che poi convertiamo).
            # Il segnale secondario NON usa covariate (restano solo sul modello-gol).
            a_sig, d_sig, ha_sig, _, _ = self._fit_counts(
                len(teams), s_home_idx, s_away_idx,
                sig_home, sig_away, s_weights, use_correction=False,
                attack_prior=attack_prior, defense_prior=defense_prior,
            )
            self.attack_sig = {t: a_sig[idx[t]] for t in teams}
            self.defense_sig = {t: d_sig[idx[t]] for t in teams}
            self.home_advantage_sig = ha_sig
            # Tasso di conversione segnale -> gol (pesato nel tempo). Porta il
            # segnale su scala gol: ~1 per l'xG, ~0.3 per i tiri in porta.
            self.conv_home = float(np.sum(s_weights * sig["home_goals"].to_numpy())
                                   / np.sum(s_weights * sig_home))
            self.conv_away = float(np.sum(s_weights * sig["away_goals"].to_numpy())
                                   / np.sum(s_weights * sig_away))

        self.fitted = True
        return self

    def _fit_counts(
        self,
        n: int,
        home_idx: np.ndarray,
        away_idx: np.ndarray,
        home_counts: np.ndarray,
        away_counts: np.ndarray,
        weights: np.ndarray,
        use_correction: bool,
        cov_lam: np.ndarray | None = None,
        attack_prior: np.ndarray | None = None,
        defense_prior: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, float, float, np.ndarray]:
        """Stima attacco/difesa/vantaggio-casa/rho (+ beta covariate) via ML
        pesata su generici conteggi (gol o segnale). Ritorna
        (attack, defense, home_adv, rho, beta).

        use_correction: applica la correzione Dixon-Coles sui punteggi bassi
        (adatta ai gol). Per il segnale secondario la disattiviamo (rho=0).
        cov_lam: matrice [n_partite x k] del contributo covariata al tasso di
        CASA (per l'ospite si usa il segno opposto). k=0 -> nessuna covariata.
        attack_prior/defense_prior: bersaglio dello shrinkage per squadra (Fase 7).
        None -> 0 per tutti (comportamento classico: shrinkage verso la media).
        """
        a_prior = np.zeros(n) if attack_prior is None else attack_prior
        d_prior = np.zeros(n) if defense_prior is None else defense_prior
        log_fact = gammaln(home_counts + 1.0) + gammaln(away_counts + 1.0)
        k = 0 if cov_lam is None else cov_lam.shape[1]

        def neg_log_likelihood(params: np.ndarray) -> float:
            attack = params[:n]
            defense = params[n:2 * n]
            home_adv = params[2 * n]
            rho = params[2 * n + 1]
            beta = params[2 * n + 2:]

            cov_h = cov_lam @ beta if k else 0.0
            lam = np.exp(attack[home_idx] + defense[away_idx] + home_adv + cov_h)
            mu = np.exp(attack[away_idx] + defense[home_idx] - cov_h)

            ll = (home_counts * np.log(lam) - lam) \
                + (away_counts * np.log(mu) - mu) - log_fact
            if use_correction:
                tau = _tau(home_counts, away_counts, lam, mu, rho)
                ll = ll + np.log(np.clip(tau, 1e-10, None))

            weighted = np.sum(weights * ll)

            # Indeterminazione: invariante per attack_i += c, defense_i -= c.
            # La fissiamo imponendo media(attacco) = 0.
            penalty = _IDENTIFIABILITY_PENALTY * attack.mean() ** 2
            if self.shrinkage > 0.0:
                penalty += self.shrinkage * (np.sum((attack - a_prior) ** 2)
                                             + np.sum((defense - d_prior) ** 2))
            return -weighted + penalty

        x0 = np.concatenate([
            a_prior, d_prior, np.array([0.25]), np.array([-0.05]),
            np.zeros(k),
        ])
        rho_bounds = (-0.4, 0.4) if use_correction else (0.0, 0.0)
        bounds = (
            [(-3.0, 3.0)] * n + [(-3.0, 3.0)] * n + [(-1.0, 2.0)] + [rho_bounds]
            + [(-1.0, 1.0)] * k   # beta covariate
        )

        result = minimize(
            neg_log_likelihood, x0, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-9},
        )
        p = result.x
        return p[:n], p[n:2 * n], float(p[2 * n]), float(p[2 * n + 1]), p[2 * n + 2:]

    # ------------------------------------------------------------------ #
    # Predizione
    # ------------------------------------------------------------------ #
    def _score_matrix(self, lam: float, mu: float) -> np.ndarray:
        """Matrice P(gol_casa=i, gol_ospite=j) con correzione Dixon-Coles."""
        k = np.arange(self.max_goals + 1)
        # Poisson pmf via logaritmi per stabilita' numerica.
        home_pmf = np.exp(k * math.log(lam) - lam - gammaln(k + 1.0))
        away_pmf = np.exp(k * math.log(mu) - mu - gammaln(k + 1.0))
        matrix = np.outer(home_pmf, away_pmf)

        # Correzione sui 4 punteggi bassi.
        matrix[0, 0] *= 1.0 - lam * mu * self.rho
        matrix[0, 1] *= 1.0 + lam * self.rho
        matrix[1, 0] *= 1.0 + mu * self.rho
        matrix[1, 1] *= 1.0 - self.rho

        # Rinormalizza: la correzione e il troncamento rompono la somma a 1.
        matrix = np.clip(matrix, 0.0, None)
        matrix /= matrix.sum()
        return matrix

    def _cov_term(self, features: dict | None) -> float:
        """Contributo covariata al log-tasso della squadra di CASA:
        somma_k beta_k * (z_casa - z_ospite). Per l'ospite si usa il segno opposto.
        0 se non ci sono covariate o mancano i valori."""
        if not self.covariates or not self.beta or features is None:
            return 0.0
        total = 0.0
        for name in self.covariates:
            hcol, acol, kind = _COVARIATES[name]
            m, s = self.cov_mean[name], self.cov_std[name]
            zh = _cov_transform(np.array([features.get(hcol, np.nan)], float), kind)[0]
            za = _cov_transform(np.array([features.get(acol, np.nan)], float), kind)[0]
            zh = 0.0 if np.isnan(zh) else (zh - m) / s
            za = 0.0 if np.isnan(za) else (za - m) / s
            total += self.beta[name] * (zh - za)
        return total

    def expected_goals(self, home_team: str, away_team: str,
                       features: dict | None = None) -> tuple[float, float]:
        """Gol attesi (lambda, mu). Squadre sconosciute = forza media (0).

        Se shots_blend < 1, mescola il tasso stimato dai gol con quello stimato
        dal segnale secondario (convertito in scala gol):
        lam = a*lam_gol + (1-a)*lam_segnale. Le eventuali covariate (Fase 4c)
        aggiustano il tasso dai GOL usando i valori di partita in ``features``.
        """
        # Tasso dai GOL (con eventuale aggiustamento delle covariate).
        cov = self._cov_term(features)
        lam_g = math.exp(self.attack.get(home_team, 0.0)
                         + self.defense.get(away_team, 0.0) + self.home_advantage + cov)
        mu_g = math.exp(self.attack.get(away_team, 0.0)
                        + self.defense.get(home_team, 0.0) - cov)

        a = self.shots_blend
        if a >= 1.0 or not self.attack_sig:
            return lam_g, mu_g

        # Tasso dal SEGNALE SECONDARIO, riportato su scala gol con la conversione.
        lam_s = math.exp(self.attack_sig.get(home_team, 0.0)
                         + self.defense_sig.get(away_team, 0.0)
                         + self.home_advantage_sig) * self.conv_home
        mu_s = math.exp(self.attack_sig.get(away_team, 0.0)
                        + self.defense_sig.get(home_team, 0.0)) * self.conv_away

        lam = a * lam_g + (1.0 - a) * lam_s
        mu = a * mu_g + (1.0 - a) * mu_s
        return lam, mu

    def predict_match(self, home_team: str, away_team: str,
                      features: dict | None = None) -> MatchPrediction:
        """Predice tutti i mercati per una partita.

        Le squadre non viste in allenamento (es. neopromosse senza storico nella
        finestra dati) ricevono forza d'attacco/difesa media (0): una stima
        prudente finche' non accumulano partite reali.

        features: valori grezzi della partita per le covariate (es.
        {"home_squad_value": ..., "away_squad_value": ...}); necessari solo se il
        modello usa covariate. Assenti/NaN -> covariata neutra per quella partita.
        """
        if not self.fitted:
            raise RuntimeError("Il modello non e' ancora stato allenato (fit).")

        lam, mu = self.expected_goals(home_team, away_team, features)
        matrix = self._score_matrix(lam, mu)

        # Somme sui triangoli / diagonale della matrice dei punteggi.
        prob_home = float(np.tril(matrix, -1).sum())   # gol_casa > gol_ospite
        prob_draw = float(np.trace(matrix))            # gol_casa == gol_ospite
        prob_away = float(np.triu(matrix, 1).sum())    # gol_casa < gol_ospite

        # Over/Under 2.5: somma sulle celle dove i+j >= 3.
        i = np.arange(self.max_goals + 1).reshape(-1, 1)
        j = np.arange(self.max_goals + 1).reshape(1, -1)
        over_mask = (i + j) >= 3
        prob_over = float(matrix[over_mask].sum())
        prob_under = 1.0 - prob_over

        # GG (both teams to score): entrambe segnano almeno 1 -> celle i>=1, j>=1.
        prob_btts_yes = float(matrix[1:, 1:].sum())

        return MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            exp_home_goals=lam,
            exp_away_goals=mu,
            prob_home_win=prob_home,
            prob_draw=prob_draw,
            prob_away_win=prob_away,
            prob_over_2_5=prob_over,
            prob_under_2_5=prob_under,
            prob_btts_yes=prob_btts_yes,
            prob_btts_no=1.0 - prob_btts_yes,
            score_matrix=matrix,
        )

    # ------------------------------------------------------------------ #
    # Serializzazione (per salvare/ricaricare i parametri stimati)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "half_life_days": self.half_life_days,
            "max_goals": self.max_goals,
            "shrinkage": self.shrinkage,
            "shots_blend": self.shots_blend,
            "blend_signal": self.blend_signal,
            "attack": self.attack,
            "defense": self.defense,
            "home_advantage": self.home_advantage,
            "rho": self.rho,
            "attack_sig": self.attack_sig,
            "defense_sig": self.defense_sig,
            "home_advantage_sig": self.home_advantage_sig,
            "conv_home": self.conv_home,
            "conv_away": self.conv_away,
            "covariates": list(self.covariates),
            "beta": self.beta,
            "cov_mean": self.cov_mean,
            "cov_std": self.cov_std,
            "promoted_prior": list(self.promoted_prior) if self.promoted_prior else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DixonColesModel":
        model = cls(
            half_life_days=data.get("half_life_days", 180.0),
            max_goals=data.get("max_goals", 10),
            shrinkage=data.get("shrinkage", 0.0),
            shots_blend=data.get("shots_blend", 1.0),
            blend_signal=data.get("blend_signal", "sot"),
            covariates=tuple(data.get("covariates", ())),
            promoted_prior=(tuple(data["promoted_prior"])
                            if data.get("promoted_prior") else None),
        )
        model.attack = dict(data["attack"])
        model.defense = dict(data["defense"])
        model.home_advantage = float(data["home_advantage"])
        model.rho = float(data["rho"])
        model.attack_sig = dict(data.get("attack_sig", {}))
        model.defense_sig = dict(data.get("defense_sig", {}))
        model.home_advantage_sig = float(data.get("home_advantage_sig", 0.0))
        model.conv_home = float(data.get("conv_home", 1.0))
        model.conv_away = float(data.get("conv_away", 1.0))
        model.beta = dict(data.get("beta", {}))
        model.cov_mean = dict(data.get("cov_mean", {}))
        model.cov_std = dict(data.get("cov_std", {}))
        model.teams = sorted(model.attack)
        model.fitted = True
        return model
