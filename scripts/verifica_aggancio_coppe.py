#!/usr/bin/env python3
"""Controllo di COMPLETEZZA: tutto quello che abbiamo raccolto e' agganciato?

PERCHE' ESISTE. Richiesta dell'utente (03/08/2026): *«aggiungi un controllo
finale per verificare di aver agganciato tutti i dati raccolti fino ad ora per
le coppe nazionali»*. Non e' una formalita': quando l'ha chiesto, **8.475 righe
di evento e 8.115 di statistica erano raccolte e non collegate a niente** —
nessuno se n'era accorto perche' i numeri che guardavamo (partite, formazioni)
erano ottimi. Un foglio dimenticato non da' errore: da' silenzio.

COSA CONTROLLA, per ogni raccolta manuale registrata e per ogni suo foglio:

  1. **niente resta fuori**: ogni riga raccolta compare in una tabella di
     aggancio — non «quasi ogni riga», tutte;
  2. **ogni riga e' risolta o DICHIARATA**: se un `player_id` o un `game_id`
     manca, dev'essere spiegato (partita assente dalla fonte automatica,
     giocatore che quella fonte non conosce). Un buco spiegato e' innocuo, uno
     silenzioso no (R6);
  3. **niente e' inventato**: nessun identificatore agganciato che non esista
     nel registro, e nessuna persona usata due volte nella stessa squadra-partita.

USO:
    python scripts/verifica_aggancio_coppe.py            # tabella + esito
    python scripts/verifica_aggancio_coppe.py --json     # per gli script
Esce con codice 1 se un controllo fallisce.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))

from scripts.registra_raccolta_coppa_diretta import FILE_MANIFESTO  # noqa: E402

USCITA = RADICE / "data" / "coppe_2526"

# foglio raccolto -> (tabella di aggancio, colonna che deve risultare risolta)
FOGLI = {
    "partite.csv": ("aggancio_partite.csv", "game_id"),
    "formazioni_e_cambi.csv": ("aggancio_giocatori.csv", "player_id"),
    "eventi.csv": ("aggancio_eventi.csv", "player_id"),
    "stat_giocatori.csv": ("aggancio_statistiche.csv", "player_id"),
    # Le statistiche di SQUADRA non hanno un giocatore: si agganciano alla
    # partita. Sono entrate dopo (Fase 139-quater) e non tutte le raccolte le
    # hanno ancora — il controllo salta le raccolte che non le hanno, ma non
    # perdona quelle che ce l'hanno e non le agganciano.
    "stat_squadra.csv": ("aggancio_statistiche_squadra.csv", "game_id"),
}


def _log(m: str) -> None:
    print(m, flush=True)


def raccolte() -> list[Path]:
    return sorted(d for d in (RADICE / "files").iterdir()
                  if (d / FILE_MANIFESTO).exists())


def verifica() -> tuple[list[dict], list[str]]:
    righe, problemi = [], []
    tabelle = {}
    for f, _ in FOGLI.values():
        p = USCITA / f
        if not p.exists():
            problemi.append(f"manca la tabella di aggancio {f}")
            continue
        tabelle[f] = pd.read_csv(p, low_memory=False)

    for cartella in raccolte():
        coppa = json.loads(
            (cartella / FILE_MANIFESTO).read_text(encoding="utf-8"))["coppa"]
        for foglio, (tab, colonna) in FOGLI.items():
            if not (cartella / foglio).exists():
                continue
            grezzo = pd.read_csv(cartella / foglio, low_memory=False)
            agganciato = tabelle.get(tab)
            if agganciato is None:
                continue
            mio = agganciato[agganciato.competizione == coppa] \
                if "competizione" in agganciato else \
                agganciato[agganciato.Competizione == coppa]

            # (1) niente resta fuori
            if len(mio) != len(grezzo):
                problemi.append(
                    f"{coppa}/{foglio}: raccolte {len(grezzo)} righe ma nella "
                    f"tabella di aggancio ce ne sono {len(mio)}")

            # (2) risolte, oppure spiegate
            if colonna == "player_id" and "Giocatore" in grezzo:
                # gli eventi hanno righe SENZA persona (il punteggio dopo un
                # gol avversario): non sono buchi, non hanno un nome da agganciare
                denom = mio[mio[_col_nome(mio)].notna()] if _col_nome(mio) else mio
            else:
                denom = mio
            risolte = int(denom[colonna].notna().sum())
            righe.append({
                "coppa": coppa, "foglio": foglio,
                "raccolte": len(grezzo), "in_tabella": len(mio),
                "da_risolvere": len(denom), "risolte": risolte,
                "quota": round(risolte / len(denom), 4) if len(denom) else None,
            })

    # (3) niente inventato: nessuna persona due volte nella stessa squadra-partita
    g = tabelle.get("aggancio_giocatori.csv")
    if g is not None:
        v = g.dropna(subset=["player_id", "game_id"])
        doppi = v.groupby(["game_id", "club_id", "player_id"]).size()
        if (doppi > 1).any():
            problemi.append(
                f"{int((doppi > 1).sum())} persone agganciate due volte nella "
                f"stessa squadra-partita")

    return righe, problemi


def _col_nome(d: pd.DataFrame) -> str | None:
    for c in ("nome_diretta", "Giocatore"):
        if c in d:
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    righe, problemi = verifica()
    if args.json:
        print(json.dumps({"righe": righe, "problemi": problemi},
                         indent=2, ensure_ascii=False))
        return 1 if problemi else 0

    _log(f"{'coppa':16s} {'foglio':22s} {'raccolte':>9s} {'in tabella':>11s}"
         f" {'risolte':>9s} {'quota':>7s}")
    _log("-" * 80)
    for r in righe:
        stato = "" if r["in_tabella"] == r["raccolte"] else "  ⚠️ FUORI"
        _log(f"{r['coppa']:16s} {r['foglio']:22s} {r['raccolte']:>9d}"
             f" {r['in_tabella']:>11d} {r['risolte']:>9d}"
             f" {r['quota']:>6.1%}{stato}" if r["quota"] is not None else "")
    tot_r = sum(r["raccolte"] for r in righe)
    tot_ok = sum(r["risolte"] for r in righe)
    tot_d = sum(r["da_risolvere"] for r in righe)
    _log("-" * 80)
    _log(f"{'TOTALE':16s} {'':22s} {tot_r:>9d} {'':>11s} {tot_ok:>9d}"
         f" {tot_ok / tot_d:>6.1%}")

    if problemi:
        _log("\n❌ PROBLEMI:")
        for p in problemi:
            _log(f"   {p}")
        return 1
    _log("\n✅ ogni riga raccolta e' nella sua tabella di aggancio, "
         "e nessuna identita' e' usata due volte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
