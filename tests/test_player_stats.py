"""Test del primo dato "Tier B" del progetto (diretta.it, Serie A 2025-26).

Due famiglie di test, con scopi diversi:
1. **guardiani dei dati** — la copertura e le identita' aritmetiche che il
   report di verifica del 31/07/2026 dichiara. Se il file cambia sotto i piedi
   devono rompersi qui, non dentro un backtest;
2. **guardiani della regola R8** — che `team_form()` non guardi mai la partita
   in corso. E' l'errore piu' facile e piu' difficile da vedere di tutto il
   fronte: il numero sarebbe giusto, sbagliato sarebbe il MOMENTO.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import player_stats as ps


@pytest.fixture(scope="module")
def pm() -> pd.DataFrame:
    return ps.load_player_matches()


# --------------------------------------------------------------------------
# 1 · Guardiani dei dati
# --------------------------------------------------------------------------

def test_copertura_attesa(pm):
    assert len(pm) == ps.EXPECTED_ROWS
    assert pm.groupby(["data", "Squadra", "Avversario"]).ngroups == ps.EXPECTED_TEAM_MATCHES
    assert pm["Squadra"].nunique() == 20


def test_load_strict_alza_se_la_copertura_cambia(pm, monkeypatch):
    """La guardia deve essere rumorosa: meglio fallire che restituire meno righe.

    Si simula un file troncato: `strict=True` deve alzare, `strict=False` no.
    """
    troncato = pm.drop(columns=["data"]).head(100)
    monkeypatch.setattr(ps, "_read", lambda path: troncato)

    with pytest.raises(ValueError, match="righe giocatore-partita"):
        ps.load_player_matches(strict=True)

    assert len(ps.load_player_matches(strict=False)) == 100


def test_load_strict_alza_se_mancano_team_partita(pm, monkeypatch):
    """Il conteggio righe può tornare mentre i team-partita no: va visto lo stesso."""
    doppio = pd.concat([pm.drop(columns=["data"]).head(ps.EXPECTED_ROWS // 2)] * 2)
    monkeypatch.setattr(ps, "_read", lambda path: doppio)
    with pytest.raises(ValueError, match="team-partita"):
        ps.load_player_matches(strict=True)


def test_esattamente_undici_titolari(pm):
    """Identita' §1 del report di verifica: 379/379 partite, 11 titolari a testa."""
    t = pm[pm["Titolare/Subentrato"].str.strip().str.lower() == "titolare"]
    per_squadra = t.groupby(["data", "Squadra"]).size()
    assert set(per_squadra.unique()) == {11}


def test_nessuna_riga_duplicata(pm):
    assert not pm.duplicated(subset=["Giornata", "Squadra", "Giocatore"]).any()


def test_valori_dentro_i_range_fisici(pm):
    assert pm["Minuti giocati"].between(1, 120).all()
    for col in [c for c in pm.columns if "(%)" in c]:
        v = pm[col].dropna()
        assert v.between(0, 100).all(), f"{col} fuori da 0-100"


def test_minuti_bassi_solo_con_espulsione(pm):
    """§1 del report: 43 squadra-partita sotto 985', TUTTE con un rosso.

    E' un test di *significato*, non di forma: un totale minuti basso senza
    espulsione sarebbe un dato mancante travestito da dato pieno (regola R6).
    """
    agg = pm.groupby(["data", "Squadra"], as_index=False).agg(
        minuti=("Minuti giocati", "sum"),
        rossi=("Cartellini rossi", "sum"),
        doppi_gialli=("Secondo cartellino giallo", "sum"),
    )
    bassi = agg[agg["minuti"] < 985]
    assert len(bassi) == 43
    assert ((bassi["rossi"] + bassi["doppi_gialli"]) > 0).all()


def test_coerenza_gol_col_nostro_snapshot(pm):
    """Il controllo piu' forte: la fonte regge contro football-data.co.uk.

    `gol dei giocatori + autogol degli avversari == risultato dello snapshot`,
    su ogni squadra-partita. Le due fonti sono indipendenti.
    """
    j = ps.join_to_snapshot(pm)
    per_team = j.groupby(["data", "Squadra", "in_casa"], as_index=False).agg(
        gol=("Gol", "sum"), home_goals=("home_goals", "first"),
        away_goals=("away_goals", "first"),
    )
    autogol = (
        pm.groupby(["data", "Avversario"], as_index=False)["Autogol"].sum()
        .rename(columns={"Avversario": "Squadra", "Autogol": "autogol_avversari"})
    )
    per_team = per_team.merge(autogol, on=["data", "Squadra"], how="left").fillna(
        {"autogol_avversari": 0}
    )
    reali = per_team["home_goals"].where(per_team["in_casa"], per_team["away_goals"])
    assert (per_team["gol"] + per_team["autogol_avversari"] == reali).all()


def test_join_allo_snapshot_e_totale(pm):
    """Un join che perde righe in silenzio e' un bug gia' pagato dal progetto."""
    j = ps.join_to_snapshot(pm)
    assert len(j) == len(pm)
    assert j["home_team"].notna().all()


def test_la_partita_mancante_e_solo_quella_dichiarata(pm):
    """Como e Lecce hanno 37 partite, non 38 — e nessun altro."""
    partite = pm.groupby("Squadra")["data"].nunique()
    assert set(partite[partite == 37].index) == {"Como", "Lecce"}
    assert (partite.drop(["Como", "Lecce"]) == 38).all()


def test_colonne_tier_b_presenti_e_piene(pm):
    """Le righe della checklist §1.9 che il piano dava per irraggiungibili."""
    tier_b = [
        "Palloni toccati", "Passaggi totali", "Passaggi riusciti",
        "Dribbling tentati", "Dribbling riusciti", "Contrasti",
        "Palle intercettate", "Palloni recuperati", "Falli commessi",
        "Falli subiti", "Goal previsti (xG)", "Assist previsti (xA)",
        "Grandi occasioni create",
    ]
    for c in tier_b:
        assert c in pm.columns, f"colonna Tier B assente: {c}"
        assert pm[c].notna().all(), f"colonna Tier B con buchi: {c}"


# --------------------------------------------------------------------------
# 2 · Guardiani della regola R8 (anti look-ahead)
# --------------------------------------------------------------------------

def test_team_form_non_guarda_la_partita_in_corso(pm):
    """IL test che conta. Se `team_form` includesse la partita corrente, il
    numero sarebbe giusto e il modello inservibile.

    Verifica diretta: per una squadra, la media dichiarata alla partita k deve
    coincidere con la media calcolata a mano sulle partite 0..k-1, e NON con
    quella su 0..k.
    """
    col = "Palloni toccati"
    forma = ps.team_form(pm, columns=[col], window=5)
    grezzo = (
        pm.groupby(["data", "Squadra"], as_index=False)[col].sum()
        .sort_values(["Squadra", "data"])
    )
    squadra = "Inter"
    g = grezzo[grezzo["Squadra"] == squadra].reset_index(drop=True)
    f = forma[forma["Squadra"] == squadra].sort_values("data").reset_index(drop=True)
    nome = f"{col} (media 5 prec.)"

    for k in (1, 5, 10, 20):
        atteso = g[col].iloc[max(0, k - 5):k].mean()
        assert f[nome].iloc[k] == pytest.approx(atteso), (
            f"partita {k}: la media non è quella delle sole partite precedenti"
        )
        incluso = g[col].iloc[max(0, k - 4):k + 1].mean()
        if atteso != pytest.approx(incluso):
            assert f[nome].iloc[k] != pytest.approx(incluso), (
                f"partita {k}: LOOK-AHEAD — la media include la partita in corso"
            )


def test_team_form_prima_partita_e_nan(pm):
    """Nessuna squadra ha un 'prima' alla prima giornata: deve uscire NaN,
    non zero. Uno zero qui sarebbe un finto pieno (regola R6)."""
    forma = ps.team_form(pm, columns=["Palloni toccati"], window=5)
    prime = forma.sort_values("data").groupby("Squadra").head(1)
    assert prime["Palloni toccati (media 5 prec.)"].isna().all()


def test_team_form_alza_su_colonna_inesistente(pm):
    with pytest.raises(KeyError):
        ps.team_form(pm, columns=["Colonna Che Non Esiste"])


def test_le_statistiche_sono_tutte_post(pm):
    """Documentale ma vincolante: nessuna colonna `pre` deve finire per errore
    nell'elenco delle statistiche, e viceversa."""
    stats = set(ps.statistic_columns(pm))
    assert not stats & set(ps.PRE_COLUMNS)
    assert not stats & set(ps.STATIC_COLUMNS)
    assert "Palloni toccati" in stats and "Goal previsti (xG)" in stats
