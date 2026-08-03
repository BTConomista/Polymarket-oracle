#!/usr/bin/env python3
"""Aggancia le raccolte manuali di coppa al resto del database (Fase 139-bis).

TRE PONTI, non uno. La raccolta diretta.it parla per NOMI; il database parla per
identificatori. Finche' non si toccano, «la carriera di questo giocatore» e
«come ha giocato in Coppa Italia» restano due frasi che non si possono dire
insieme.

  squadre    nome diretta.it   -> `club_id`      (registro player-scores)
  partite    `ID partita`      -> `game_id`      (la stessa partita nelle due fonti)
  giocatori  nome diretta.it   -> `player_id`    (l'anagrafica, e quindi le carriere)

⭐ **L'ordine dei tre ponti non e' arbitrario: il terzo si regge sul secondo.**
Agganciata la partita, i candidati per un giocatore non sono piu' «tutti quelli
in campo quel giorno» ma le **18-23 persone di quel club in quella partita**. Su
un insieme cosi' piccolo il confronto per nome diventa quasi sempre univoco.

Misurato, ed e' la ragione per cui questo script non usa
`player_identity.collega_per_eliminazione`: quella funzione aggancia per
`(data, token del nome)` e va benissimo sui CAMPIONATI, dove diretta.it scrive
il nome intero («Garces Facundo»). Nelle **coppe** lo abbrevia («Motta E.»), il
token set e' `{motta}` contro `{emanuele, motta}` e la chiave non combacia mai:
**25,6%** sulla Coppa Italia, **12,0%** sulla Pokal. Passando dal vincolo della
partita: **97,5%** e **98,0%**.

⚠️ Un aggancio ambiguo NON si sceglie a caso: resta vuoto. Attribuire a un
giocatore la carriera di un altro e' peggio di non sapere (nota in testa a
`player_identity`). L'eliminazione scatta **solo** quando resta una sola
possibilita' da entrambe le parti — 46 righe su 4.651.

USO:
    python scripts/aggancia_coppe.py                 # tutte le raccolte trovate
    python scripts/aggancia_coppe.py --coppa "DFB-Pokal"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from src.data.club_matching import Agganciatore  # noqa: E402
from scripts.registra_raccolta_coppa_diretta import (  # noqa: E402
    ALIAS_COPPA,
    FILE_MANIFESTO,
    _stessa_persona as _uguali,
    _token as _tok,
)

USCITA = RADICE / "data" / "coppe_2526"


def _log(m: str) -> None:
    print(m, flush=True)


def _aggancia_giocatori(F: pd.DataFrame, partite: pd.DataFrame, cid) -> pd.DataFrame:
    """`player_id` per ogni riga di formazione, dentro la singola partita.

    Due passate, nell'ordine che conta:
      1. **per nome**, con la stessa regola della porta d'ingresso (sottoinsieme
         dei token + iniziale come prefisso) — cosi' «Motta E.» trova «Emanuele
         Motta» ma «Esposito Sa.» non finisce su «Francesco Esposito»;
      2. **per eliminazione**: se in un (partita, club) resta UN nostro nome
         spaiato e UN candidato libero, sono la stessa persona per esclusione.
         Se ne restano due o piu', **nessuno** viene agganciato: un aggancio
         indovinato attribuisce a un giocatore la carriera di un altro.
    """
    nostre = pd.read_csv(USCITA / "formazioni.csv")
    mappa = dict(zip(partite.id_diretta, partite.game_id))

    F = F.copy()
    F["game_id"] = F["ID partita"].map(mappa)
    F["club_id"] = F.Squadra.map(cid).astype("Int64")
    F["player_id"] = pd.array([pd.NA] * len(F), dtype="Int64")
    F["metodo"] = None

    per_gruppo = {k: v for k, v in nostre.groupby(["game_id", "club_id"])}
    for (gid, club), righe in F.dropna(subset=["game_id"]).groupby(["game_id", "club_id"]):
        cand = per_gruppo.get((gid, club))
        if cand is None:
            continue
        liberi = list(zip(cand.player_id, [_tok(x) for x in cand.giocatore]))
        spaiati = []
        for idx, nome in zip(righe.index, righe.Giocatore):
            t = _tok(nome)
            for i, (pid, tb) in enumerate(liberi):
                if _uguali(t, tb):
                    F.at[idx, "player_id"] = pid
                    F.at[idx, "metodo"] = "nome"
                    liberi.pop(i)
                    break
            else:
                spaiati.append(idx)
        # eliminazione: solo se resta UNA possibilita' da entrambe le parti
        if len(spaiati) == 1 and len(liberi) == 1:
            F.at[spaiati[0], "player_id"] = liberi[0][0]
            F.at[spaiati[0], "metodo"] = "eliminazione"
    return F


def raccolte() -> list[Path]:
    return sorted(d for d in (RADICE / "files").iterdir()
                  if (d / FILE_MANIFESTO).exists())


def aggancia(cartella: Path, appearances=None) -> tuple[dict, dict]:
    manifesto = json.loads((cartella / FILE_MANIFESTO).read_text(encoding="utf-8"))
    coppa = manifesto["coppa"]
    _log(f"\n=== {coppa}  ({cartella.name})")

    P = pd.read_csv(cartella / "partite.csv")
    F = pd.read_csv(cartella / "formazioni_e_cambi.csv")
    N = pd.read_csv(USCITA / "partite.csv")
    N = N[N.competizione == coppa].copy()

    ag = Agganciatore()

    def cid(n):
        return ag.aggancia(ALIAS_COPPA.get(n, n))

    # --- 1. squadre -------------------------------------------------------- #
    nomi = sorted(set(P.Casa) | set(P.Ospite))
    squadre = pd.DataFrame({"competizione": coppa, "nome_diretta": nomi})
    squadre["club_id"] = squadre.nome_diretta.map(cid).astype("Int64")
    _log(f"  squadre:   {squadre.club_id.notna().sum()}/{len(squadre)} agganciate")

    # --- 2. partite -------------------------------------------------------- #
    P = P.copy()
    P["data_iso"] = pd.to_datetime(P.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    P["club_casa"] = P.Casa.map(cid).astype("Int64")
    P["club_ospite"] = P.Ospite.map(cid).astype("Int64")
    N["club_casa"] = N.casa.map(cid).astype("Int64")
    N["club_ospite"] = N.ospite.map(cid).astype("Int64")
    partite = P.merge(
        N[["data", "club_casa", "club_ospite", "game_id", "turno"]],
        left_on=["data_iso", "club_casa", "club_ospite"],
        right_on=["data", "club_casa", "club_ospite"], how="left",
        suffixes=("", "_nostro"))
    partite = partite[["Competizione", "Turno", "data_iso", "Casa", "Ospite",
                       "club_casa", "club_ospite", "ID partita", "game_id",
                       "turno"]].rename(columns={
                           "Competizione": "competizione", "Turno": "turno_diretta",
                           "data_iso": "data", "Casa": "casa", "Ospite": "ospite",
                           "ID partita": "id_diretta", "turno": "turno_nostro"})
    _log(f"  partite:   {partite.game_id.notna().sum()}/{len(partite)} agganciate "
         f"a un `game_id`")

    # --- 3. giocatori ------------------------------------------------------ #
    # ⚠️ NON si usa `player_identity.collega_per_eliminazione`, ed e' una
    # scelta misurata. Quella funzione aggancia per `(data, token del nome)`, e
    # funziona sui CAMPIONATI perche' li' diretta.it scrive il nome intero
    # («Garces Facundo»). Nelle coppe lo **abbrevia** («Motta E.»): il token set
    # e' `{motta}` contro `{emanuele, motta}` e la chiave non combacia mai.
    # Misurato: 25,6% sulla Coppa Italia, 12,0% sulla Pokal.
    #
    # Qui c'e' un vincolo molto piu' forte, e ce l'abbiamo gia': la **partita
    # e' agganciata**. Dentro un singolo (game_id, club_id) i candidati sono le
    # 18-23 persone che hanno giocato QUELLA partita per QUEL club — non tutte
    # quelle in campo quel giorno. Su un insieme cosi' piccolo il confronto per
    # sottoinsieme + iniziale (lo stesso della porta d'ingresso) e' quasi
    # sempre univoco, e cio' che resta si chiude per eliminazione.
    g = _aggancia_giocatori(F, partite, cid)
    g["data_iso"] = pd.to_datetime(g.Data, format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    giocatori = g[["Competizione", "Turno", "data_iso", "Squadra", "club_id",
                   "Giocatore", "player_id", "metodo", "Gruppo", "Numero",
                   "Ruolo", "ID partita", "game_id"]].rename(columns={
                       "Competizione": "competizione", "Turno": "turno",
                       "data_iso": "data", "Squadra": "squadra",
                       "Giocatore": "nome_diretta", "Gruppo": "gruppo",
                       "Numero": "numero", "Ruolo": "ruolo",
                       "ID partita": "id_diretta"})
    tot, agg = len(giocatori), int(giocatori.player_id.notna().sum())
    tit = giocatori[giocatori.gruppo == "Titolare"]
    _log(f"  giocatori: {agg}/{tot} agganciati a un `player_id` ({agg/tot:.1%})"
         f"  ·  titolari {int(tit.player_id.notna().sum())}/{len(tit)} "
         f"({tit.player_id.notna().mean():.1%})")

    quadro = {
        "coppa": coppa,
        "squadre": {"totali": len(squadre),
                    "agganciate": int(squadre.club_id.notna().sum()),
                    "non_agganciate": sorted(
                        squadre.loc[squadre.club_id.isna(), "nome_diretta"])},
        "partite": {"totali": len(partite),
                    "agganciate": int(partite.game_id.notna().sum()),
                    "non_agganciate": [
                        f"{r.data} {r.casa}-{r.ospite}"
                        for _, r in partite[partite.game_id.isna()].iterrows()]},
        "giocatori": {
            "righe": tot, "agganciate": agg,
            "quota": round(agg / tot, 4),
            "titolari": int(len(tit)),
            "titolari_agganciati": int(tit.player_id.notna().sum()),
            "persone_distinte": int(giocatori.player_id.nunique()),
        },
    }
    return {"squadre": squadre, "partite": partite, "giocatori": giocatori}, quadro


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coppa", help="ne aggancia una sola")
    args = ap.parse_args()

    from src.data import careers as C
    _log("carico le presenze player-scores una volta sola…")
    appearances = C._load_appearances()

    tabelle = {"squadre": [], "partite": [], "giocatori": []}
    quadri = []
    for d in raccolte():
        m = json.loads((d / FILE_MANIFESTO).read_text(encoding="utf-8"))
        if args.coppa and m["coppa"] != args.coppa:
            continue
        t, q = aggancia(d, appearances)
        for k, v in t.items():
            tabelle[k].append(v)
        quadri.append(q)

    if not quadri:
        _log("nessuna raccolta trovata")
        return 1

    USCITA.mkdir(parents=True, exist_ok=True)
    for k, pezzi in tabelle.items():
        f = USCITA / f"aggancio_{k}.csv"
        pd.concat(pezzi, ignore_index=True).to_csv(f, index=False)
        _log(f"\n  scritto {f.relative_to(RADICE)}")
    f = USCITA / "aggancio_manifesto.json"
    f.write_text(json.dumps(quadri, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"  scritto {f.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
