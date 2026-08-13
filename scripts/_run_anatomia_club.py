"""Come e' fatto il dataset player-scores, dal punto di vista di UN CLUB.

Domanda dell'utente (13/08/2026): «capitera' sempre piu' spesso di avere nel
dataset squadre che non sono nei nostri campionati... come ci comportiamo in
quei casi? magari cerchiamo di capire bene il funzionamento del dataset per
capire come comportarci».

Questo script misura la risposta invece di ragionarci sopra. La domanda vera
non e' «quanti club mancano» — non ne manca nessuno — ma **quali FATTI esistono
per un club, a seconda di dove gioca**.

E' un'analisi DESCRITTIVA per una decisione di perimetro: non registra nulla in
`runs.jsonl` e non tocca nessun modello.

⚠️ Nota di metodo, gia' pagata in `_run_uefa_fuori_top5.py`: **le coperture si
misurano per COLONNA, non per file.** Un file che «contiene» un club non
garantisce che la colonna che serve sia piena su quella riga. Qui ogni riga di
output e' una colonna, mai un file.

Uso:
    python scripts/_run_anatomia_club.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FILES = Path(__file__).resolve().parents[1] / "files" / "player_scores"

#: I cinque campionati che il progetto modella, coi codici di player-scores.
TOP5 = {"IT1": "Serie A", "GB1": "Premier League", "ES1": "La Liga",
        "L1": "Bundesliga", "FR1": "Ligue 1"}


def _leggi(nome: str, **kw) -> pd.DataFrame:
    return pd.read_csv(FILES / f"{nome}.csv.gz", low_memory=False, **kw)


def anagrafiche() -> tuple[pd.DataFrame, dict[int, str | None]]:
    """Il REGISTRO dei club e la mappa club_id -> campionato domestico.

    `club_names` e' l'unico file che conosca tutti i club_id; la colonna
    `domestic_competition_id` e' pero' piena solo su una minoranza di righe, e
    sono le stesse che stanno in `clubs.csv` (verificato qui sotto).
    """
    reg = _leggi("club_names")
    lega = dict(zip(reg["club_id"], reg["domestic_competition_id"]))
    return reg, lega


def main() -> None:
    reg, lega = anagrafiche()
    ctx = _leggi("clubs")
    comp = _leggi("competitions")

    con_lega = {c for c, l in lega.items() if isinstance(l, str)}

    print("=" * 78)
    print("1 · I DUE FILE CHE PARLANO DI CLUB, e cosa copre ciascuno")
    print("=" * 78)
    print(f"\nclub_names.csv   {len(reg):5d} righe · il REGISTRO (club_id, name, lega)")
    print(f"clubs.csv        {len(ctx):5d} righe · il CONTESTO (rosa, stadio, valore...)")
    print(f"\n  club_id nel registro ................. {reg['club_id'].nunique():5d}")
    print(f"  con NOME ............................. {reg['name'].notna().sum():5d} "
          f"({reg['name'].notna().mean() * 100:.1f}%)")
    print(f"  con CAMPIONATO domestico ............. {len(con_lega):5d} "
          f"({len(con_lega) / len(reg) * 100:.1f}%)")
    stessi = set(ctx["club_id"]) == con_lega
    print(f"  gli stessi che stanno in clubs.csv? .. {'SI' if stessi else 'NO'}")

    dom = comp[comp["type"] == "domestic_league"]
    print(f"\n  campionati domestici nel dataset ..... {len(dom):5d}")
    print(f"  competizioni totali .................. {len(comp):5d}")

    # ---- 2 · l'universo dei club: chi compare DOVE --------------------------
    g = _leggi("games")
    cg = _leggi("club_games")
    app = _leggi("appearances")
    pl = _leggi("players")
    val = _leggi("player_valuations")

    universo = set(g["home_club_id"]) | set(g["away_club_id"])
    print("\n" + "=" * 78)
    print("2 · L'UNIVERSO: quali club_id compaiono in quale file")
    print("=" * 78)
    presenze = {
        "games (una partita giocata)": universo,
        "club_games (la stessa, per lato)": set(cg["club_id"]),
        "appearances (un giocatore sceso in campo)": set(app["player_club_id"].dropna()),
        "players (club ATTUALE di un giocatore)": set(pl["current_club_id"].dropna()),
        "player_valuations (club al momento della stima)": set(val["current_club_id"].dropna()),
        "clubs (contesto)": set(ctx["club_id"]),
    }
    print(f"\n{'file':48s} {'club':>6s} {'di cui con lega':>16s}")
    for nome, ins in presenze.items():
        ins = {int(x) for x in ins}
        print(f"  {nome:46s} {len(ins):6d} {len(ins & con_lega):16d}")

    # ---- 3 · il taglio che conta: dentro / fuori ---------------------------
    print("\n" + "=" * 78)
    print("3 · I TRE CERCHI, e quali FATTI esistono in ciascuno")
    print("=" * 78)

    top5 = {c for c, l in lega.items() if l in TOP5}
    altri = con_lega - top5
    senza = universo - con_lega

    cerchi = [
        ("A · nei nostri 5 campionati", top5 & universo),
        ("B · in uno dei 32 campionati coperti", altri & universo),
        ("C · fuori: nessun campionato domestico", senza),
    ]

    # un fatto = una colonna, misurata sui club del cerchio
    partite_per_club = pd.concat([
        g[["home_club_id"]].rename(columns={"home_club_id": "club_id"}),
        g[["away_club_id"]].rename(columns={"away_club_id": "club_id"}),
    ])["club_id"].value_counts()
    app_per_club = app["player_club_id"].value_counts()
    form_home = g.set_index("home_club_id")["home_club_formation"]
    all_home = g.set_index("home_club_id")["home_club_manager_name"]

    print(f"\n{'cerchio':40s} {'club':>6s} {'partite':>9s} {'formazioni':>11s}")
    for nome, ins in cerchi:
        ins = {int(x) for x in ins}
        part = int(partite_per_club.reindex(list(ins)).fillna(0).sum())
        sub = g[g["home_club_id"].isin(ins) | g["away_club_id"].isin(ins)]
        f_pct = (sub["home_club_formation"].notna().mean() * 100) if len(sub) else 0.0
        print(f"  {nome:38s} {len(ins):6d} {part:9d} {f_pct:10.1f}%")

    print(f"\n{'cerchio':40s} {'presenze giocatore':>19s} {'con anagrafica':>15s}")
    for nome, ins in cerchi:
        ins = {int(x) for x in ins}
        a = int(app_per_club.reindex(list(ins)).fillna(0).sum())
        sub = app[app["player_club_id"].isin(ins)]
        noti = sub["player_id"].isin(set(pl["player_id"])).mean() * 100 if len(sub) else 0.0
        print(f"  {nome:38s} {a:19d} {noti:14.1f}%")

    print(f"\n{'cerchio':40s} {'contesto (clubs.csv)':>21s} {'valori rosa':>13s}")
    for nome, ins in cerchi:
        ins = {int(x) for x in ins}
        c = len(ins & set(ctx["club_id"]))
        v = len(ins & {int(x) for x in val["current_club_id"].dropna()})
        print(f"  {nome:38s} {c:14d}/{len(ins):<6d} {v:8d}/{len(ins):<4d}")

    # ---- 4 · dove GIOCANO i club del cerchio C ----------------------------
    print("\n" + "=" * 78)
    print("4 · DOVE giocano i club del cerchio C (le partite che abbiamo di loro)")
    print("=" * 78)
    sub = g[g["home_club_id"].isin(senza) | g["away_club_id"].isin(senza)]
    per_comp = sub["competition_id"].value_counts()
    nomi = dict(zip(comp["competition_id"], comp["name"]))
    tipi = dict(zip(comp["competition_id"], comp["type"]))
    print(f"\n{'competizione':38s} {'tipo':22s} {'partite':>8s}")
    for cid, n in per_comp.items():
        print(f"  {str(nomi.get(cid, cid))[:36]:36s} {str(tipi.get(cid, '?')):22s} {n:8d}")
    dom_c = sum(n for cid, n in per_comp.items() if tipi.get(cid) == "domestic_league")
    print(f"\n  partite di CAMPIONATO domestico: {dom_c}")
    print("  → se e' 0, la lega dei club del cerchio C non e' deducibile nemmeno")
    print("    dalle partite: il dataset non li vede mai giocare in casa loro.")

    # ---- 5 · il cerchio B, per campionato ---------------------------------
    print("\n" + "=" * 78)
    print("5 · IL CERCHIO B, campionato per campionato (chi sono i 'vicini')")
    print("=" * 78)
    b = pd.DataFrame({"club_id": sorted(altri & universo)})
    b["lega"] = b["club_id"].map(lega)
    tab = b.groupby("lega").size().sort_values(ascending=False)
    paese = dict(zip(comp["domestic_league_code"], comp["country_name"]))
    print(f"\n{'lega':8s} {'paese':24s} {'club':>5s}")
    for l, n in tab.items():
        print(f"  {l:6s} {str(paese.get(l, '?'))[:22]:22s} {n:5d}")

    # ---- 6 · il cerchio C non e' una cosa sola ----------------------------
    print("\n" + "=" * 78)
    print("6 · DENTRO IL CERCHIO C: quattro famiglie, quattro risposte diverse")
    print("=" * 78)
    naz = (set(g[g["competition_type"] == "national_team_competition"]["home_club_id"])
           | set(g[g["competition_type"] == "national_team_competition"]["away_club_id"]))
    orfani = universo - set(reg["club_id"])

    # il paese si deduce da una coppa NAZIONALE: chi gioca la FA Cup e' inglese.
    tipo = dict(zip(comp["competition_id"], comp["type"]))
    paese_comp = dict(zip(comp["competition_id"], comp["country_name"]))
    coppe = {c for c, t in tipo.items() if t == "domestic_cup"}
    #: competizioni presenti in games.csv ma ASSENTI da competitions.csv: il
    #: paese e' letto dal nome, ed e' l'unico punto di questo script dove un
    #: valore non viene dal dato ma dalla lettura di una sigla.
    IGNOTE = {"CGB": "England", "POCP": "Portugal", "UKRS": "Ukraine",
              "COL1": "Colombia"}
    lati = pd.concat([
        g[["competition_id", "home_club_id"]].rename(columns={"home_club_id": "club_id"}),
        g[["competition_id", "away_club_id"]].rename(columns={"away_club_id": "club_id"}),
    ])
    lati = lati[lati["club_id"].isin(senza)].copy()
    lati["paese"] = lati["competition_id"].map(
        lambda c: paese_comp.get(c) if c in coppe else IGNOTE.get(c))
    per_club = (lati.dropna(subset=["paese"]).groupby("club_id")["paese"]
                    .agg(lambda s: sorted(set(s))))
    univoco = {c for c, p in per_club.items() if len(p) == 1}
    ambiguo = {c for c, p in per_club.items() if len(p) > 1}
    resto = senza - set(per_club.index) - naz - orfani

    print(f"\n  cerchio C, totale ........................................ {len(senza):5d}")
    print(f"    · NAZIONALI (non sono club) ........................... {len(senza & naz):5d}")
    print(f"    · ORFANI: nemmeno nel registro, e senza nome in games .. {len(senza & orfani):5d}")
    print(f"    · PAESE deducibile da una coppa nazionale ............. {len(univoco):5d}"
          f"  (ambigui: {len(ambiguo)})")
    print(f"    · restanti: solo coppe UEFA, nessun paese nel dataset .. {len(resto):5d}")
    print("\n  paesi dedotti (primi 12): ",
          pd.Series([per_club[c][0] for c in univoco]).value_counts().head(12).to_dict())

    # ---- 7 · che tipo di dato e' l'etichetta di lega (R8) -----------------
    print("\n" + "=" * 78)
    print("7 · `domestic_competition_id` e' STATICO, e non si contraddice mai")
    print("=" * 78)
    dom_ids = set(dom["competition_id"]) | {"COL1"}
    campionati = lati_dom = pd.concat([
        g[["competition_id", "home_club_id"]].rename(columns={"home_club_id": "club_id"}),
        g[["competition_id", "away_club_id"]].rename(columns={"away_club_id": "club_id"}),
    ])
    campionati = campionati[campionati["competition_id"].isin(dom_ids)]
    per = campionati.groupby("club_id")["competition_id"].nunique()
    incoerenti = sum(1 for c, l in lega.items()
                     if isinstance(l, str) and c in set(campionati["club_id"])
                     and l not in set(campionati[campionati.club_id == c]["competition_id"]))
    print(f"\n  club con partite in PIU' di un campionato domestico: {int((per > 1).sum())} su {len(per)}")
    print(f"  club la cui etichetta contraddice le sue partite ..: {incoerenti}")
    print("  → l'etichetta non e' «la lega di oggi» ne' «la lega di quella stagione»:")
    print("    e' «l'unico dei 32 campionati coperti in cui quel club e' mai apparso».")
    print("    Non mente mai, ma non risponde alla domanda «in che serie era nel 2019».")
    ignote_g = sorted(set(g["competition_id"]) - set(comp["competition_id"]))
    print(f"\n  competition_id presenti in games ma ASSENTI da competitions.csv: {ignote_g}")

    print("\n" + "=" * 78)
    print("La riga da ricordare: nel cerchio C non manca IL CLUB — mancano il suo")
    print("CAMPIONATO e il suo CONTESTO. Le partite, i giocatori e i minuti ci sono.")
    print("=" * 78)


if __name__ == "__main__":
    main()
