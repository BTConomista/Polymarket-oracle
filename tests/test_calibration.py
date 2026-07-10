"""Test della ricalibrazione post-hoc (temperature scaling)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation import calibration, metrics


def test_apply_temperature_identity_and_normalization():
    p = np.array([[0.5, 0.3, 0.2], [0.6, 0.1, 0.3]])
    out = calibration.apply_temperature(p, 1.0)
    assert np.allclose(out, p)
    # Somma a 1 su ogni riga per qualunque T.
    for t in (0.5, 1.0, 2.0):
        assert np.allclose(calibration.apply_temperature(p, t).sum(axis=1), 1.0)


def test_temperature_direction():
    """T>1 raffredda (max piu' basso), T<1 scalda (max piu' alto)."""
    p = np.array([[0.7, 0.2, 0.1]])
    hotter = calibration.apply_temperature(p, 0.5).max()
    colder = calibration.apply_temperature(p, 2.0).max()
    assert colder < p.max() < hotter


def test_fit_recovers_known_distortion():
    """Se il "modello" e' distorto da un T0 noto e gli esiti vengono dalla
    distribuzione vera, fit_temperature recupera ~1/T0 (annulla la distorsione)."""
    rng = np.random.default_rng(0)
    true = np.array([0.5, 0.3, 0.2])
    n = 30000
    T0 = 2.0  # modello troppo "morbido"
    distorted = calibration.apply_temperature(true[None, :], T0)[0]
    model = np.repeat(distorted[None, :], n, axis=0)
    draws = rng.choice(3, size=n, p=true)
    outcomes = [["H", "D", "A"][d] for d in draws]

    T = calibration.fit_temperature(model, outcomes)
    assert 1.0 / T0 * 0.75 < T < 1.0 / T0 * 1.25  # recupera ~0.5


def test_fit_improves_or_matches_logloss_in_sample():
    """In-sample, la log-loss dopo la calibrazione non puo' peggiorare
    (T=1 e' sempre ammissibile: il minimo trovato e' <= baseline)."""
    rng = np.random.default_rng(1)
    true = np.array([0.45, 0.30, 0.25])
    n = 5000
    model = calibration.apply_temperature(true[None, :], 1.5).repeat(n, axis=0)
    outcomes = [["H", "D", "A"][d] for d in rng.choice(3, size=n, p=true)]

    base = metrics.log_loss_1x2(model, outcomes)
    T = calibration.fit_temperature(model, outcomes)
    cal = metrics.log_loss_1x2(calibration.apply_temperature(model, T), outcomes)
    assert cal <= base + 1e-9
