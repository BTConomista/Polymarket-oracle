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
    score_matrix: np.ndarray = field(repr=False)

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
            shots_blend: peso alpha del segnale GOL rispetto ai TIRI IN PORTA nella
                stima dei gol attesi. I gol sono rumorosi (fortuna sotto porta); i
                tiri in porta misurano le occasioni con meno rumore. Si allena un
                modello sui gol e uno sui tiri in porta, e si mescolano i tassi:
                    gol_attesi = alpha * (dai gol) + (1-alpha) * (dai tiri in porta)
                alpha=1 -> solo gol (modello classico); alpha=0 -> solo tiri in
                porta; valori intermedi -> miscela. Tarabile via scripts/tune.py.
        """
        self.half_life_days = half_life_days
        self.max_goals = max_goals
        self.shrinkage = shrinkage
        self.shots_blend = shots_blend

        # Parametri stimati sui GOL (riempiti da fit()).
        self.teams: list[str] = []
        self.attack: dict[str, float] = {}
        self.defense: dict[str, float] = {}
        self.home_advantage: float = 0.0
        self.rho: float = 0.0

        # Parametri stimati sui TIRI IN PORTA (solo se shots_blend < 1).
        self.attack_sot: dict[str, float] = {}
        self.defense_sot: dict[str, float] = {}
        self.home_advantage_sot: float = 0.0
        # Tasso di conversione tiri-in-porta -> gol (per riportare i tiri su scala gol).
        self.conv_home: float = 1.0
        self.conv_away: float = 1.0

        self.fitted: bool = False

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
    ) -> "DixonColesModel":
        """Stima i parametri via massima verosimiglianza pesata.

        Usa SOLO le partite con data < ``as_of_date`` (evita il look-ahead:
        non guarda mai il futuro rispetto al momento della predizione).

        Args:
            matches: DataFrame nello schema interno (vedi data/loader.py).
            as_of_date: momento "presente". Le partite successive sono ignorate
                e il decadimento temporale e' calcolato rispetto a questa data.
                Default: il giorno dopo l'ultima partita disponibile.
        """
        if as_of_date is None:
            as_of_date = matches["date"].max() + pd.Timedelta(days=1)

        train = matches[matches["date"] < as_of_date].copy()
        if train.empty:
            raise ValueError("Nessuna partita disponibile prima di as_of_date.")

        teams = sorted(set(train["home_team"]) | set(train["away_team"]))
        idx = {t: k for k, t in enumerate(teams)}
        self.teams = teams

        # --- Modello sui GOL (sempre) ---
        home_idx = train["home_team"].map(idx).to_numpy()
        away_idx = train["away_team"].map(idx).to_numpy()
        weights = self._time_weights(train["date"], as_of_date)
        attack, defense, home_adv, rho = self._fit_counts(
            len(teams), home_idx, away_idx,
            train["home_goals"].to_numpy().astype(float),
            train["away_goals"].to_numpy().astype(float),
            weights, use_correction=True,
        )
        self.attack = {t: attack[idx[t]] for t in teams}
        self.defense = {t: defense[idx[t]] for t in teams}
        self.home_advantage = home_adv
        self.rho = rho

        # --- Modello sui TIRI IN PORTA (solo se serve mescolarli) ---
        if self.shots_blend < 1.0:
            sot = train.dropna(subset=["home_sot", "away_sot"])
            if sot.empty:
                raise ValueError("shots_blend < 1 ma mancano i dati sui tiri in porta.")
            s_home_idx = sot["home_team"].map(idx).to_numpy()
            s_away_idx = sot["away_team"].map(idx).to_numpy()
            s_weights = self._time_weights(sot["date"], as_of_date)
            # I tiri in porta sono conteggi ad alto volume: niente correzione sui
            # punteggi bassi (serve solo il tasso atteso, che poi convertiamo).
            a_sot, d_sot, ha_sot, _ = self._fit_counts(
                len(teams), s_home_idx, s_away_idx,
                sot["home_sot"].to_numpy().astype(float),
                sot["away_sot"].to_numpy().astype(float),
                s_weights, use_correction=False,
            )
            self.attack_sot = {t: a_sot[idx[t]] for t in teams}
            self.defense_sot = {t: d_sot[idx[t]] for t in teams}
            self.home_advantage_sot = ha_sot
            # Tasso di conversione: quanti gol per tiro in porta (pesato nel tempo).
            self.conv_home = float(np.sum(s_weights * sot["home_goals"].to_numpy())
                                   / np.sum(s_weights * sot["home_sot"].to_numpy()))
            self.conv_away = float(np.sum(s_weights * sot["away_goals"].to_numpy())
                                   / np.sum(s_weights * sot["away_sot"].to_numpy()))

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
    ) -> tuple[np.ndarray, np.ndarray, float, float]:
        """Stima attacco/difesa/vantaggio-casa/rho via ML pesata su generici
        conteggi (gol o tiri in porta). Ritorna (attack, defense, home_adv, rho).

        use_correction: applica la correzione Dixon-Coles sui punteggi bassi
        (adatta ai gol). Per i tiri in porta la disattiviamo (rho fissato a 0).
        """
        log_fact = gammaln(home_counts + 1.0) + gammaln(away_counts + 1.0)

        def neg_log_likelihood(params: np.ndarray) -> float:
            attack = params[:n]
            defense = params[n:2 * n]
            home_adv = params[2 * n]
            rho = params[2 * n + 1]

            lam = np.exp(attack[home_idx] + defense[away_idx] + home_adv)
            mu = np.exp(attack[away_idx] + defense[home_idx])

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
                penalty += self.shrinkage * (np.sum(attack ** 2) + np.sum(defense ** 2))
            return -weighted + penalty

        x0 = np.concatenate([
            np.zeros(n), np.zeros(n), np.array([0.25]), np.array([-0.05]),
        ])
        rho_bounds = (-0.4, 0.4) if use_correction else (0.0, 0.0)
        bounds = (
            [(-3.0, 3.0)] * n + [(-3.0, 3.0)] * n + [(-1.0, 2.0)] + [rho_bounds]
        )

        result = minimize(
            neg_log_likelihood, x0, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-9},
        )
        params = result.x
        return params[:n], params[n:2 * n], float(params[2 * n]), float(params[2 * n + 1])

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

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        """Gol attesi (lambda, mu). Squadre sconosciute = forza media (0).

        Se shots_blend < 1, mescola il tasso stimato dai gol con quello stimato
        dai tiri in porta (convertito in scala gol): lam = a*lam_gol + (1-a)*lam_tiri.
        """
        # Tasso dai GOL.
        lam_g = math.exp(self.attack.get(home_team, 0.0)
                         + self.defense.get(away_team, 0.0) + self.home_advantage)
        mu_g = math.exp(self.attack.get(away_team, 0.0)
                        + self.defense.get(home_team, 0.0))

        a = self.shots_blend
        if a >= 1.0 or not self.attack_sot:
            return lam_g, mu_g

        # Tasso dai TIRI IN PORTA, riportato su scala gol con il tasso di conversione.
        lam_s = math.exp(self.attack_sot.get(home_team, 0.0)
                         + self.defense_sot.get(away_team, 0.0)
                         + self.home_advantage_sot) * self.conv_home
        mu_s = math.exp(self.attack_sot.get(away_team, 0.0)
                        + self.defense_sot.get(home_team, 0.0)) * self.conv_away

        lam = a * lam_g + (1.0 - a) * lam_s
        mu = a * mu_g + (1.0 - a) * mu_s
        return lam, mu

    def predict_match(self, home_team: str, away_team: str) -> MatchPrediction:
        """Predice tutti i mercati per una partita.

        Le squadre non viste in allenamento (es. neopromosse senza storico nella
        finestra dati) ricevono forza d'attacco/difesa media (0): una stima
        prudente finche' non accumulano partite reali.
        """
        if not self.fitted:
            raise RuntimeError("Il modello non e' ancora stato allenato (fit).")

        lam, mu = self.expected_goals(home_team, away_team)
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
            "attack": self.attack,
            "defense": self.defense,
            "home_advantage": self.home_advantage,
            "rho": self.rho,
            "attack_sot": self.attack_sot,
            "defense_sot": self.defense_sot,
            "home_advantage_sot": self.home_advantage_sot,
            "conv_home": self.conv_home,
            "conv_away": self.conv_away,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DixonColesModel":
        model = cls(
            half_life_days=data.get("half_life_days", 180.0),
            max_goals=data.get("max_goals", 10),
            shrinkage=data.get("shrinkage", 0.0),
            shots_blend=data.get("shots_blend", 1.0),
        )
        model.attack = dict(data["attack"])
        model.defense = dict(data["defense"])
        model.home_advantage = float(data["home_advantage"])
        model.rho = float(data["rho"])
        model.attack_sot = dict(data.get("attack_sot", {}))
        model.defense_sot = dict(data.get("defense_sot", {}))
        model.home_advantage_sot = float(data.get("home_advantage_sot", 0.0))
        model.conv_home = float(data.get("conv_home", 1.0))
        model.conv_away = float(data.get("conv_away", 1.0))
        model.teams = sorted(model.attack)
        model.fitted = True
        return model
