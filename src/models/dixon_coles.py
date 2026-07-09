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
        """
        self.half_life_days = half_life_days
        self.max_goals = max_goals
        self.shrinkage = shrinkage

        # Parametri stimati (riempiti da fit()).
        self.teams: list[str] = []
        self.attack: dict[str, float] = {}
        self.defense: dict[str, float] = {}
        self.home_advantage: float = 0.0
        self.rho: float = 0.0
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
        n = len(teams)

        home_idx = train["home_team"].map(idx).to_numpy()
        away_idx = train["away_team"].map(idx).to_numpy()
        hg = train["home_goals"].to_numpy().astype(float)
        ag = train["away_goals"].to_numpy().astype(float)
        weights = self._time_weights(train["date"], as_of_date)

        # Costanti nella log-verosimiglianza (indipendenti dai parametri):
        # -log(x!) = -gammaln(x+1). Le precalcoliamo una volta sola.
        log_fact = gammaln(hg + 1.0) + gammaln(ag + 1.0)

        def neg_log_likelihood(params: np.ndarray) -> float:
            attack = params[:n]
            defense = params[n:2 * n]
            home_adv = params[2 * n]
            rho = params[2 * n + 1]

            lam = np.exp(attack[home_idx] + defense[away_idx] + home_adv)
            mu = np.exp(attack[away_idx] + defense[home_idx])

            # log P(x) + log P(y) sotto le due Poisson.
            ll = (hg * np.log(lam) - lam) + (ag * np.log(mu) - mu) - log_fact
            # Correzione Dixon-Coles (clip per evitare log di numeri <= 0).
            tau = _tau(hg, ag, lam, mu, rho)
            ll = ll + np.log(np.clip(tau, 1e-10, None))

            weighted = np.sum(weights * ll)

            # Indeterminazione: la verosimiglianza e' invariante se si sposta
            # attack_i += c e defense_i -= c per ogni squadra. La fissiamo
            # imponendo media(attacco) = 0 tramite una penalita'.
            penalty = _IDENTIFIABILITY_PENALTY * attack.mean() ** 2
            # Shrinkage: tira attacco/difesa verso la media (0). Non tocca
            # vantaggio-casa e rho (parametri globali, gia' ben stimati).
            if self.shrinkage > 0.0:
                penalty += self.shrinkage * (np.sum(attack ** 2) + np.sum(defense ** 2))
            return -weighted + penalty

        # Punto di partenza: tutto neutro, vantaggio-casa positivo, rho piccolo.
        x0 = np.concatenate([
            np.zeros(n),            # attack
            np.zeros(n),            # defense
            np.array([0.25]),       # home_advantage (log-scala, ~ +28% gol)
            np.array([-0.05]),      # rho
        ])
        bounds = (
            [(-3.0, 3.0)] * n       # attack
            + [(-3.0, 3.0)] * n     # defense
            + [(-1.0, 2.0)]         # home_advantage
            + [(-0.4, 0.4)]         # rho (deve tenere tau > 0)
        )

        result = minimize(
            neg_log_likelihood, x0, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-9},
        )

        params = result.x
        self.teams = teams
        self.attack = {t: float(params[idx[t]]) for t in teams}
        self.defense = {t: float(params[n + idx[t]]) for t in teams}
        self.home_advantage = float(params[2 * n])
        self.rho = float(params[2 * n + 1])
        self.fitted = True
        return self

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
        """Gol attesi (lambda, mu). Squadre sconosciute = forza media (0)."""
        a_h = self.attack.get(home_team, 0.0)
        d_h = self.defense.get(home_team, 0.0)
        a_a = self.attack.get(away_team, 0.0)
        d_a = self.defense.get(away_team, 0.0)
        lam = math.exp(a_h + d_a + self.home_advantage)
        mu = math.exp(a_a + d_h)
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
            "attack": self.attack,
            "defense": self.defense,
            "home_advantage": self.home_advantage,
            "rho": self.rho,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DixonColesModel":
        model = cls(
            half_life_days=data.get("half_life_days", 180.0),
            max_goals=data.get("max_goals", 10),
            shrinkage=data.get("shrinkage", 0.0),
        )
        model.attack = dict(data["attack"])
        model.defense = dict(data["defense"])
        model.home_advantage = float(data["home_advantage"])
        model.rho = float(data["rho"])
        model.teams = sorted(model.attack)
        model.fitted = True
        return model
