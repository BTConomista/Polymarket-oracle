"""Le metriche: valori ESATTI, calcolati a mano, non solo relazioni.

PERCHE' ESISTE QUESTO FILE (Fase 137). `src/evaluation/metrics.py` e' la base di
ogni numero pubblicato dal progetto: `experiment_log.compute_metrics` — la
«fonte di verita' unica» delle metriche (CLAUDE.md §5) — chiama queste funzioni,
e da li' i numeri finiscono in `runs.jsonl`, nel README e nel diario.

Eppure `brier_1x2` non aveva **un solo riferimento** in `tests/`: si poteva
togliere il quadrato dalla formula e l'intera suite restava verde. Anche
`log_loss_1x2` era coperto solo da asserzioni RELAZIONALI («il modello migliore
prende meno del peggiore»), che sopravvivono a una trasformazione monotona
sbagliata — per esempio una base logaritmica diversa, che cambierebbe ogni
log-loss mai pubblicato senza invertire un solo confronto.

Qui i valori sono **inchiodati**: ogni assert riporta il conto a mano che lo
giustifica, cosi' una modifica alla formula si vede subito e si vede DOVE.
Non e' un test di regressione contro noi stessi (che congelerebbe anche un
errore): e' il confronto con la definizione da manuale delle due metriche.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.evaluation import metrics


# --------------------------------------------------------------------- #
# Brier 1X2 — la metrica che non era coperta da nulla
# --------------------------------------------------------------------- #
def test_brier_1x2_valore_esatto_calcolato_a_mano():
    """Brier multiclasse = media della somma dei quadrati degli scarti.

    Riga unica, p = (0.5, 0.3, 0.2), esito H -> y = (1, 0, 0):
        (0.5-1)^2 + (0.3-0)^2 + (0.2-0)^2 = 0.25 + 0.09 + 0.04 = 0.38

    Il valore inchioda il QUADRATO: senza, la stessa riga darebbe
    |0.5-1| + 0.3 + 0.2 = 1.00, e nessuna asserzione relazionale se ne
    accorgerebbe (l'ordinamento fra modelli non cambia).
    """
    assert metrics.brier_1x2(np.array([[0.5, 0.3, 0.2]]), ["H"]) == pytest.approx(0.38)


def test_brier_1x2_estremi_zero_e_due():
    """Il range della definizione multiclasse e' [0, 2], e i due estremi sono
    raggiungibili: previsione certa e giusta -> 0; certa e sbagliata -> 2
    (= 1 sul lato mancato + 1 sul lato dato per certo)."""
    assert metrics.brier_1x2(np.array([[1.0, 0.0, 0.0]]), ["H"]) == pytest.approx(0.0)
    assert metrics.brier_1x2(np.array([[1.0, 0.0, 0.0]]), ["A"]) == pytest.approx(2.0)


def test_brier_1x2_uniforme():
    """p = (1/3, 1/3, 1/3): (2/3)^2 + 2*(1/3)^2 = 4/9 + 2/9 = 6/9 = 0.6667.

    E' il valore di riferimento del «non so nulla»: un Brier 1X2 sopra 0.667
    e' peggio del lancio di un dado a tre facce."""
    p = np.full((4, 3), 1 / 3)
    assert metrics.brier_1x2(p, ["H", "D", "A", "H"]) == pytest.approx(6 / 9)


def test_brier_1x2_ordine_delle_colonne_e_H_D_A():
    """Le colonne sono (casa, pareggio, ospite) IN QUEST'ORDINE.

    Il caso e' volutamente asimmetrico: se casa e ospite fossero scambiate, la
    stessa riga darebbe 0.02 invece di 1.62. E' l'errore piu' facile da
    commettere passando una matrice costruita altrove, e il piu' silenzioso."""
    p = np.array([[0.9, 0.05, 0.05]])
    # esito A: (0.9-0)^2 + 0.05^2 + (0.05-1)^2 = 0.81 + 0.0025 + 0.9025 = 1.715
    assert metrics.brier_1x2(p, ["A"]) == pytest.approx(1.715)
    # esito H: 0.01 + 0.0025 + 0.0025 = 0.015
    assert metrics.brier_1x2(p, ["H"]) == pytest.approx(0.015)


def test_brier_1x2_e_la_media_sulle_righe_non_la_somma():
    """Duplicare il campione non deve cambiare la metrica: e' una MEDIA."""
    p = np.array([[0.5, 0.3, 0.2], [0.2, 0.3, 0.5]])
    uno = metrics.brier_1x2(p, ["H", "A"])
    due = metrics.brier_1x2(np.vstack([p, p]), ["H", "A", "H", "A"])
    assert uno == pytest.approx(due)
    # e il valore e' la media dei due conti a mano: (0.38 + 0.38) / 2
    assert uno == pytest.approx(0.38)


# --------------------------------------------------------------------- #
# Log-loss 1X2 — coperto, ma solo da confronti fra modelli
# --------------------------------------------------------------------- #
def test_log_loss_1x2_valore_esatto():
    """Log-loss = -media(ln(probabilita' assegnata all'esito avvenuto)).

    p = (0.5, 0.3, 0.2), esito H -> -ln(0.5) = 0.6931 (logaritmo NATURALE).
    E' l'assert che distingue ln da log10: in base 10 lo stesso caso darebbe
    0.3010, e ogni confronto fra modelli resterebbe identico."""
    v = metrics.log_loss_1x2(np.array([[0.5, 0.3, 0.2]]), ["H"])
    assert v == pytest.approx(-math.log(0.5))
    assert v == pytest.approx(0.6931471805599453)


def test_log_loss_1x2_uniforme_e_ln3():
    """Il «non so nulla» a tre esiti vale ln(3) = 1.0986: e' la baseline che il
    progetto cita di continuo (un modello sopra 1.0986 e' peggio del caso)."""
    p = np.full((3, 3), 1 / 3)
    assert metrics.log_loss_1x2(p, ["H", "D", "A"]) == pytest.approx(math.log(3))


def test_log_loss_1x2_probabilita_zero_e_tagliata_non_infinita():
    """Una probabilita' 0 sull'esito avvenuto non deve mandare la metrica a
    infinito e contaminare l'intero backtest: il clip a 1e-15 la limita a
    -ln(1e-15) = 34.54. E' una scelta, e va vista se cambia."""
    v = metrics.log_loss_1x2(np.array([[0.0, 0.5, 0.5]]), ["H"])
    assert np.isfinite(v)
    assert v == pytest.approx(-math.log(1e-15))


def test_log_loss_1x2_ordine_delle_colonne():
    """Stessa guardia del Brier: H e' la colonna 0, A la 2."""
    p = np.array([[0.7, 0.2, 0.1]])
    assert metrics.log_loss_1x2(p, ["H"]) == pytest.approx(-math.log(0.7))
    assert metrics.log_loss_1x2(p, ["D"]) == pytest.approx(-math.log(0.2))
    assert metrics.log_loss_1x2(p, ["A"]) == pytest.approx(-math.log(0.1))


# --------------------------------------------------------------------- #
# Metriche binarie (Over/Under, GG/NG, ogni mercato a due esiti)
# --------------------------------------------------------------------- #
def test_brier_binary_valore_esatto():
    """Binario = (p - y)^2, quindi range [0, 1]: NON e' la stessa scala del
    Brier 1X2 (range [0, 2]). Confondere le due scale rende incomparabili due
    numeri che sembrano paragonabili."""
    assert metrics.brier_binary(np.array([0.8]), np.array([1])) == pytest.approx(0.04)
    assert metrics.brier_binary(np.array([0.8]), np.array([0])) == pytest.approx(0.64)
    assert metrics.brier_binary(np.array([0.5, 0.5]),
                                np.array([1, 0])) == pytest.approx(0.25)


def test_log_loss_binary_valore_esatto_ed_e_simmetrico():
    """-[y ln p + (1-y) ln(1-p)]. Con p=0.8: 0.2231 se avviene, 1.6094 se no.
    Il caso p=0.5 vale ln(2) qualunque sia l'esito."""
    assert metrics.log_loss_binary(np.array([0.8]),
                                   np.array([1])) == pytest.approx(-math.log(0.8))
    assert metrics.log_loss_binary(np.array([0.8]),
                                   np.array([0])) == pytest.approx(-math.log(0.2))
    assert metrics.log_loss_binary(np.array([0.5, 0.5]),
                                   np.array([1, 0])) == pytest.approx(math.log(2))


def test_log_loss_binary_estremi_tagliati_da_entrambi_i_lati():
    """Il clip vale su tutti e due i lati: p=0 con esito 1 e p=1 con esito 0
    devono restare finiti."""
    assert np.isfinite(metrics.log_loss_binary(np.array([0.0]), np.array([1])))
    assert np.isfinite(metrics.log_loss_binary(np.array([1.0]), np.array([0])))


# --------------------------------------------------------------------- #
# Devig — la porta d'ingresso di ogni confronto col mercato
# --------------------------------------------------------------------- #
def test_devig_1x2_toglie_il_margine_e_normalizza():
    """Quote 1.90/3.80/3.80: 1/q = 0.5263/0.2632/0.2632, somma 1.0526 (margine
    del 5,26%). Dopo la normalizzazione tornano esattamente 0.50/0.25/0.25 —
    il metodo e' MOLTIPLICATIVO, cioe' spalma il margine in proporzione."""
    p = metrics.devig_1x2(1.90, 3.80, 3.80)
    assert p.sum() == pytest.approx(1.0)
    assert p == pytest.approx([0.5, 0.25, 0.25])


def test_devig_1x2_su_quote_gia_eque_non_cambia_nulla():
    """Quote 2/4/4 hanno somma degli inversi esattamente 1: il devig e'
    l'identita', non un'operazione che sposta comunque qualcosa."""
    assert metrics.devig_1x2(2.0, 4.0, 4.0) == pytest.approx([0.5, 0.25, 0.25])


def test_devig_binary_valore_esatto():
    """1.80/2.00 -> 0.5556/0.5000, somma 1.0556 -> 0.5263/0.4737."""
    over, under = metrics.devig_binary(1.80, 2.00)
    assert over + under == pytest.approx(1.0)
    assert over == pytest.approx((1 / 1.8) / (1 / 1.8 + 1 / 2.0))
    assert over == pytest.approx(0.5263157894736842)


def test_base_rates_1x2_sono_frequenze_empiriche():
    """La baseline «banale» e' la frequenza osservata degli esiti, in ordine
    H,D,A e sommata a 1."""
    b = metrics.base_rates_1x2(["H", "H", "D", "A"])
    assert b == pytest.approx([0.5, 0.25, 0.25])
    assert b.sum() == pytest.approx(1.0)


# --------------------------------------------------------------------- #
# Coerenza fra le due metriche
# --------------------------------------------------------------------- #
def test_entrambe_premiano_la_previsione_migliore():
    """Orientamento: piu' basso = meglio, per tutte e due. E' la proprieta' che
    i test relazionali gia' verificavano; resta, ma non e' piu' l'unica."""
    esiti = ["H"] * 7 + ["D"] * 2 + ["A"]
    buona = np.tile([0.7, 0.2, 0.1], (10, 1))
    scarsa = np.tile([0.1, 0.2, 0.7], (10, 1))
    assert metrics.brier_1x2(buona, esiti) < metrics.brier_1x2(scarsa, esiti)
    assert metrics.log_loss_1x2(buona, esiti) < metrics.log_loss_1x2(scarsa, esiti)


def test_il_minimo_e_nella_frequenza_vera_regola_propria():
    """Entrambe sono regole di scoring PROPRIE: su un campione generato con
    frequenze note, dichiarare quelle frequenze e' il minimo. Dichiararne di
    diverse — in qualunque direzione — costa.

    E' la proprieta' che rende sensato «calibrato»: senza, un modello potrebbe
    guadagnare esagerando la propria confidenza."""
    esiti = ["H"] * 50 + ["D"] * 25 + ["A"] * 25
    vera = np.tile([0.5, 0.25, 0.25], (100, 1))
    for storta in ([0.6, 0.2, 0.2], [0.4, 0.3, 0.3], [0.5, 0.3, 0.2]):
        alt = np.tile(storta, (100, 1))
        assert metrics.brier_1x2(vera, esiti) < metrics.brier_1x2(alt, esiti), storta
        assert metrics.log_loss_1x2(vera, esiti) < metrics.log_loss_1x2(alt, esiti), storta
