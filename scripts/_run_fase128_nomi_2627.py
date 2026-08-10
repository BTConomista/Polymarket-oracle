"""Passo P1 del test prospettico: la mappa nomi Smarkets -> nostri, e le
neopromosse 2026-27 (Fase 128).

PERCHE' ESISTE. Il test prospettico (Fase 78) ha un collo di bottiglia solo:
le quote e i fixture arrivano da Smarkets, che scrive i nomi a modo suo
(`Inter Milan`, `AC Milan`, `Köln`, `PSG`), e i nostri snapshot usano i nomi
canonici di football-data. Senza il ponte fra i due, **nessuna** delle 48
partite si aggancia -- ne' per il Modello 1 (che deve sapere quali squadre
sono in campo) ne' per il Modello 2 (che deve invertire le quote di QUELLA
partita). E' il bug piu' banale del progetto e quello gia' capitato piu'
volte: «Hellas Verona» -> «Verona» (§5 del CLAUDE.md), `Manchester Utd` che
fermava un join a 544/760 (Fase 122).

COSA FA. Estrae tutti i nomi distinti dall'ultimo file di
`data/smarkets_matches/`, li risolve con `TEAM_ALIASES`, e li classifica in
TRE categorie che vanno tenute distinte perche' hanno conseguenze diverse sul
modello:

  1. **agganciata** -- il nome risolve a una squadra con storia recente
     (presente nella stagione 2025-26). Il DC la stima dai suoi dati.
  2. **neopromossa** -- la squadra NON era in 2025-26. Va nel
     `promoted_teams` del fit, o il modello la tratta come una squadra media
     (§ sotto: e' il punto che conta davvero).
  3. **da mappare** -- il nome non risolve a nulla. E' un ERRORE, non un
     caso da saltare: una partita persa in silenzio e' esattamente il guasto
     della Fase 127.

IL PUNTO CHE CONTA (e che non era ovvio). `scripts/backtest.py::promoted_teams`
deduce le neopromosse confrontando la stagione di test con la precedente --
ma per il 2026-27 la stagione di test **non esiste ancora** nei nostri dati.
Quindi per il test prospettico l'insieme va **dichiarato**, ed e' questo
script a produrlo. Non e' una formalita': senza dichiararlo, una squadra come
il **Malaga** (una sola stagione nei nostri dati, la 2017-18) non finisce nel
prior delle promosse e viene stimata dallo shrinkage verso la **media della
lega** -- cioe' trattata come una squadra normale invece che come una
neopromossa. Con l'emivita di 365 giorni una partita del 2018 pesa
0.5^8 ~ 0.004: la storia c'e' ma non conta nulla, e il modello resta senza
prior. Sono **due difetti opposti** (media contro debole-per-costruzione) e
solo il secondo e' quello giusto.

CONTROLLO DI COERENZA. In ogni lega, |squadre entrate| deve essere uguale a
|squadre uscite|: i campionati non cambiano numero di squadre fra una
stagione e l'altra. Se un nome fosse mappato male, l'uguaglianza si romperebbe
(una squadra vera resterebbe fuori e una fantasma entrerebbe). E' un test
gratuito che usa una proprieta' strutturale, non un occhio umano.

USO:
    python scripts/_run_fase128_nomi_2627.py
    python scripts/_run_fase128_nomi_2627.py --snapshot data/smarkets_matches/....json
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import LEAGUE_CONFIGS  # noqa: E402
from src.data import sources  # noqa: E402

SNAPSHOTS = ROOT / "data" / "smarkets_matches"
OUT = ROOT / "experiments" / "fase128_nomi_2627.json"

# Le ESORDIENTI: squadre che in 9 stagioni non hanno mai giocato nella lega,
# quindi nei nostri snapshot un nome canonico **non esiste**. Non sono nomi da
# mappare (non c'e' nulla a cui mapparle) e non sono errori: sono squadre
# nuove, e il modello le deve trattare col prior delle promosse.
#
# Il nome canonico non e' indovinato: e' quello che lo **stesso provider** usa
# nei file di seconda divisione 2025-26, dove queste squadre giocavano
# (R5: prima si cerca il dato vero). Verificato il 01/08/2026 scaricando
# football-data.co.uk/mmz4281/2526/{E1,D2,SP2,F2}.csv ed enumerandone i nomi.
# La verifica si rifa' in un comando, e va **rifatta** al primo file 2627 vero:
# se il provider cambiasse grafia, il join dei risultati salterebbe in silenzio.
ESORDIENTI = {
    "premier_league": {"Coventry": "E1 2025-26", "Hull": "E1 2025-26"},
    "bundesliga": {"Elversberg": "D2 2025-26"},
    "la_liga": {"Santander": "SP2 2025-26"},
    "ligue_1": {"Le Mans": "F2 2025-26"},
}

# L'ultima stagione presente nei nostri snapshot: il metro con cui si decide
# chi e' neopromossa. Non e' una costante libera -- e' `sources.SEASONS[-1]`.
ULTIMA = int(sources.SEASONS[-1])


def nomi_per_lega(snapshot: Path) -> dict[str, set[str]]:
    """I nomi squadra distinti che Smarkets espone, lega per lega."""
    from src.data import smarkets_archive as _arch

    d = _arch.leggi(snapshot)
    fuori = d.get("leghe_senza_partite_esposte")
    if fuori:
        # Fase 127: un file puo' esistere ed essere incompleto. Meglio
        # fermarsi che costruire una mappa su 4 leghe credendole 5.
        raise SystemExit(
            f"{snapshot.name} dichiara leghe senza partite esposte: {fuori}. "
            "Raccogliere di nuovo prima di costruire la mappa.")
    out: dict[str, set[str]] = collections.defaultdict(set)
    for r in d["righe"]:
        # La mappa dei nomi e' contro gli snapshot delle 5 leghe: un club di
        # Serie B o di UCL non ha una controparte li' dentro, e finirebbe
        # classificato come «nome non agganciato» inquinando il conteggio
        # (Fase 142). Assenza del campo = file pre-142 = campionato.
        if r.get("fascia", "campionato") != "campionato":
            continue
        casa, ospite = r["partita"].split(" vs ")
        out[r["lega"]].update([casa, ospite])
    return dict(out)


def classifica(lega: str, nomi: set[str]) -> dict:
    """Le tre categorie, piu' il controllo di coerenza entrate/uscite."""
    df = pd.read_csv(ROOT / "data" / f"{lega}_matches.csv")
    recenti = set(df[df.season == ULTIMA].home_team) | set(df[df.season == ULTIMA].away_team)
    storiche = set(df.home_team) | set(df.away_team)

    esordienti = ESORDIENTI.get(lega, {})

    agganciate, neopromosse, da_mappare = {}, {}, []
    for n in sorted(nomi):
        c = sources.canonical_team(n)
        if c not in storiche and c not in esordienti:
            da_mappare.append(n)
            continue
        stagioni = sorted(int(s) for s in
                          set(df[(df.home_team == c) | (df.away_team == c)].season))
        voce = {"smarkets": n, "canonico": c, "stagioni_nei_dati": stagioni}
        if c in esordienti:
            voce["nome_verificato_su"] = esordienti[c]
        if c in recenti:
            agganciate[c] = voce
        else:
            neopromosse[c] = voce

    viste = {v["canonico"] for v in
             list(agganciate.values()) + list(neopromosse.values())}
    uscite = sorted(recenti - viste)
    return {
        "squadre_esposte": len(nomi),
        "agganciate": sorted(agganciate),
        "neopromosse": [neopromosse[k] for k in sorted(neopromosse)],
        "da_mappare": da_mappare,
        "uscite_dalla_lega": uscite,
        # Il controllo strutturale: entrate == uscite. Un campionato non cambia
        # numero di squadre fra due stagioni, quindi un nome mappato male
        # romperebbe l'uguaglianza (una squadra vera resterebbe fuori e una
        # fantasma entrerebbe). Non serve un occhio umano per accorgersene.
        "coerente": len(neopromosse) == len(uscite) and not da_mappare,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path, default=None,
                    help="file da leggere (default: l'ultimo raccolto)")
    a = ap.parse_args(argv)

    from src.data import smarkets_archive as _arch
    snap = a.snapshot or _arch.ultimo_listino_completo(SNAPSHOTS)
    nomi = nomi_per_lega(snap)

    mancanti = set(LEAGUE_CONFIGS) - set(nomi)
    if mancanti:
        raise SystemExit(f"{snap.name} non contiene: {sorted(mancanti)}")

    esito = {lega: classifica(lega, nomi[lega]) for lega in sorted(nomi)}

    print(f"snapshot: {snap.relative_to(ROOT)}\n")
    rotte = []
    for lega, e in esito.items():
        segno = "OK " if e["coerente"] else "!! "
        print(f"{segno}{lega:16} {e['squadre_esposte']:2d} squadre | "
              f"agganciate {len(e['agganciate']):2d} | "
              f"neopromosse {len(e['neopromosse'])} | "
              f"uscite {len(e['uscite_dalla_lega'])} | "
              f"da mappare {len(e['da_mappare'])}")
        for v in e["neopromosse"]:
            storia = v["stagioni_nei_dati"] or "nessuna in 9 stagioni"
            print(f"      promossa: {v['canonico']:18} (Smarkets {v['smarkets']!r}) "
                  f"storia: {storia}")
        for n in e["da_mappare"]:
            print(f"      ❌ DA MAPPARE: {n!r} -> aggiungere a TEAM_ALIASES")
        if not e["coerente"]:
            rotte.append(lega)

    tot = sum(len(e["neopromosse"]) for e in esito.values())
    print(f"\nneopromosse 2026-27 da dichiarare in `promoted_teams`: {tot}")

    OUT.write_text(json.dumps({
        "fonte_quote": str(snap.relative_to(ROOT)),
        "ultima_stagione_nei_dati": ULTIMA,
        "avvertenza": ("le neopromosse qui elencate vanno passate a "
                       "DixonColesModel.fit(promoted_teams=...): per il 2026-27 "
                       "backtest.promoted_teams() non puo' dedurle, perche' la "
                       "stagione di test non esiste ancora nei dati."),
        "per_lega": esito,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scritto {OUT.relative_to(ROOT)}")

    if rotte:
        raise SystemExit(
            f"INCOERENTE su {rotte}: entrate != uscite, oppure nomi non mappati. "
            "Non usare questa mappa finche' non torna.")


if __name__ == "__main__":
    main()
