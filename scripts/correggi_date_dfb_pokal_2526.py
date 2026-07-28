"""Rimuove 8 righe-duplicato con data sbagliata del secondo turno (Achtelfinale)
del DFB-Pokal 2025-26 in data/club_fixtures_bundesliga.csv, e ricalcola le
colonne di congestione derivate sullo snapshot Bundesliga (Fase 104).

PERCHE' ESISTE. openfootball data le 8 righe (4 partite x 2 squadre) del
secondo turno DFB-Pokal 2025-26 che coinvolgono Bochum, Stuttgart, Freiburg,
Darmstadt, Hamburg, Holstein Kiel, Bayern Munich, Union Berlin al 2025-12-02,
insieme alle altre 8 righe del turno che SONO davvero il 2025-12-02. Le prime
4 partite si sono giocate invece il 2025-12-03: il turno era su due giorni, e
openfootball le ha etichettate tutte con la prima data. Trovato e verificato
la prima volta alla Fase 100 (docs/audit_5_leghe/numeri/caccia_calendari.md
§6, confutazione contro openligadb.de: 0/114 righe recuperate non
confermate), ri-verificato in modo indipendente alla Fase 104 con una query
LIVE all'API pubblica openligadb.de (getmatchdata/dfb/2025/3, turno
"Achtelfinale") che conferma cella per cella: Bochum-Stuttgart,
Freiburg-Darmstadt, Hamburg-Kiel e Union Berlin-Bayern Monaco sono tutte
2025-12-03; le altre 4 partite del turno (Gladbach-St Pauli,
Hertha-Kaiserslautern, Dortmund-Leverkusen, Leipzig-Magdeburg) sono
2025-12-02 -- e openfootball le data correttamente, quindi non si toccano. Due
fonti indipendenti (openligadb.de, Wikipedia de: "Achtelfinale: 2./3. Dezember
2025") concordano contro openfootball: la correzione e' a senso unico.

IL RECUPERO WIKIPEDIA (Fase 103) HA GIA' AGGIUNTO LA RIGA GIUSTA. Il merge di
data/ricerca_esterna/fixtures_bundesliga_dfb_pokal.csv in
club_fixtures_bundesliga.csv dedup su (season, team, date, competition,
opponent): siccome la data differisce (12-02 vs 12-03), il merge non ha
sostituito la riga sbagliata, l'ha AFFIANCATA -- ogni squadra coinvolta ha ora
DUE righe per la stessa partita, una per data. Innocuo per rest_days_full
delle partite SUCCESSIVE (la piu' recente delle due date vince sempre nella
ricerca "ultima partita prima di d"), ma e' comunque un duplicato di una
partita che non e' mai stata giocata due volte: va tolto, non "corretto".

Uso:
    python scripts/correggi_date_dfb_pokal_2526.py            # applica
    python scripts/correggi_date_dfb_pokal_2526.py --check     # solo verifica
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import database, fixtures, sources

FX_PATH = fixtures.club_fixtures_path("bundesliga")

# (team, opponent) come compaiono in data/club_fixtures_bundesliga.csv --
# ognuna delle 4 partite genera 2 righe (una per squadra), quindi 8 righe.
# Fonte: query live 2026-07-28 a https://api.openligadb.de/getmatchdata/dfb/2025/3
# (turno "Achtelfinale"), concorde con Wikipedia de (pagina "DFB-Pokal 2025/26",
# sezione Achtelfinale) e con la ri-verifica gia' fatta alla Fase 100 contro la
# stessa API (0/114 righe non confermate).
WRONG_DATE = "2025-12-02"
RIGHT_DATE = "2025-12-03"
ROWS = [
    ("Bochum", "Stuttgart"), ("Stuttgart", "Bochum"),
    ("Freiburg", "Darmstadt"), ("Darmstadt", "Freiburg"),
    ("Hamburg", "Holstein Kiel"), ("Holstein Kiel", "Hamburg"),
    ("Bayern Munich", "Union Berlin"), ("Union Berlin", "Bayern Munich"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="solo verifica, non scrive nulla")
    args = parser.parse_args()

    fx = fixtures.read_club_fixtures(FX_PATH)
    to_drop = []
    for team, opp in ROWS:
        base = (
            (fx.team == team) & (fx.opponent == opp)
            & (fx.competition == "DFB-Pokal") & (fx.season == "2526")
        )
        dates = sorted(fx.loc[base, "date"].dt.strftime("%Y-%m-%d"))
        expected = sorted([WRONG_DATE, RIGHT_DATE])
        if dates != expected:
            raise SystemExit(
                f"{team} vs {opp}: date trovate {dates}, attese {expected} (una "
                "riga corretta gia' dal recupero Wikipedia + una riga sbagliata "
                "di openfootball) -- controllare data/club_fixtures_bundesliga.csv "
                "prima di continuare"
            )
        wrong_idx = fx.index[base & (fx.date == WRONG_DATE)]
        assert len(wrong_idx) == 1
        to_drop.append(wrong_idx[0])

    if len(to_drop) != len(ROWS):
        raise SystemExit(f"{len(to_drop)} righe da togliere, attese {len(ROWS)}")

    print(f"{len(to_drop)} righe duplicate ({WRONG_DATE}, openfootball) da togliere; "
          f"la riga {RIGHT_DATE} (Wikipedia, Fase 103) resta.")

    if args.check:
        print("--check: nessun file scritto.")
        return

    fx = fx.drop(index=to_drop).reset_index(drop=True)
    fixtures.write_club_fixtures(fx, FX_PATH)
    print(f"scritto {FX_PATH} ({len(fx)} righe)")

    snap_path = database.snapshot_path("bundesliga")
    snap = database.read_snapshot(snap_path)
    before = snap
    after = fixtures.add_rest_days_full(
        snap, fx, own_competition=sources.own_league_competition("bundesliga")
    )
    diff = before[fixtures.REST_FULL_COLUMNS].compare(after[fixtures.REST_FULL_COLUMNS])
    print(f"ricalcolo congestione: {len(diff)} partite con almeno una colonna cambiata")
    if len(diff):
        print(diff)
    database.write_snapshot(after, snap_path)
    print(f"scritto {snap_path}")


if __name__ == "__main__":
    main()
