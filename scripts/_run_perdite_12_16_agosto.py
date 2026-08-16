"""Che cosa abbiamo perso davvero fra il 12 e il 16 agosto 2026 (Fase 156-bis).

DOMANDA DELL'UTENTE, alla lettera: «fammi l'elenco dei dati che abbiamo perso
tra il 12 e il 16 agosto e per cosa li avremmo usati (se lo sappiamo)... fallo
per ogni singola partita».

PERCHE' LA DOMANDA E' PIU' INTERESSANTE DELLA RISPOSTA ATTESA. Il buco della
Fase 156 e' degli OUTRIGHT, che non sono un dato per-partita: sono una serie
per lega x mercato x giorno. Chiedere l'elenco «per partita» costringe a
verificare una cosa che nessuno aveva verificato -- se in quei quattro giorni
si sia perso anche qualcosa **a livello di partita**, cioe' se gli altri
collettori abbiano tenuto mentre quello degli outright era morto.

Lo script quindi risponde su DUE piani, e li tiene separati:

  A. OUTRIGHT -- cosa manca, elencato per lega x mercato x giorno mancante.
     Ricostruito dai due estremi del buco (12/08 e 16/08), che dicono quali
     serie esistevano prima e dopo.

  B. PARTITE -- per OGNI partita con calcio d'inizio nella finestra: quanti
     mercati abbiamo raccolto, se c'e' la quota GG/NG, quando l'abbiamo vista
     la prima e l'ultima volta (in ore PRIMA del fischio), e quanto e' fitta
     la copertura in-play. La colonna che conta e' l'ultima: **cosa manca**.

⚠️ UNA DISTINZIONE CHE VA TENUTA (R5, spiegare prima di accusare). «Non
l'abbiamo raccolto» e «non era quotato» e «l'evento non esiste piu'» sono tre
cose diverse che producono lo stesso vuoto. Il caso vero trovato qui:
Celta Vigo-Osasuna del 16/08 sparisce dal listino il 13/08 e ricompare come
evento NUOVO il 27/08 -- e' un rinvio, non una raccolta fallita. Chi contasse
le celle vuote lo segnerebbe come perdita nostra.

Uso:  python scripts/_run_perdite_12_16_agosto.py [--json PATH] [--md PATH]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import smarkets_archive as arch          # noqa: E402

UTC = dt.timezone.utc
DA = dt.datetime(2026, 8, 12, tzinfo=UTC)
A = dt.datetime(2026, 8, 17, tzinfo=UTC)

LIVE = ROOT / "data" / "smarkets_live"
OUTRIGHT = ROOT / "data" / "outright_snapshots"

# I giorni del buco: quelli fra i due estremi che esistono in archivio.
GIORNI_BUCO = ["2026-08-13", "2026-08-14", "2026-08-15"]

# Durata convenzionale di una partita, per la finestra in-play (Fase 152).
MINUTI_PARTITA = 105

# I mercati che il progetto usa davvero, per non annegare nei 190 del listino.
CHIAVE = ["1x2", "ggng", "ou25", "risultato_esatto", "double_chance",
          "asian_handicap_0_5"]


def _quando(p: Path) -> dt.datetime:
    """L'istante di uno snapshot dal suo NOME (il mtime mente: git lo riscrive).

    ⚠️ Il suffisso `-gN` dei file in-play va tolto PRIMA di leggere l'ora,
    altrimenti finisce nei secondi -- e' il difetto della Fase 151, che aveva
    fatto dire al guardiano «copertura 0%» su un archivio pieno.
    """
    n = p.name.replace(".json.gz", "").replace(".json", "").split("-g")[0]
    giorno, ora = n.split("T")
    ora = ora.replace("-", ":")
    if len(ora.split(":")) == 2:
        ora += ":00"
    return dt.datetime.fromisoformat(f"{giorno}T{ora}").replace(tzinfo=UTC)


def raccogli(adesso: dt.datetime | None = None) -> dict:
    adesso = adesso or dt.datetime.now(UTC)
    ev: dict[str, dict] = {}

    def _aggrega(p: Path, righe: list, live: bool) -> None:
        t = _quando(p)
        for r in righe:
            inizio = r.get("inizio")
            if not inizio:
                continue
            k = dt.datetime.fromisoformat(inizio.replace("Z", "+00:00"))
            if not (DA <= k < A):
                continue
            e = ev.setdefault(r["event_id"], {
                "partita": r["partita"], "lega": r["lega"],
                "fascia": r.get("fascia", "?"), "inizio": k,
                "pre": {}, "live_t": set(), "live_mercati": set()})
            if live:
                # ⚠️ L'ISTANTE DELLA LETTURA STA NELLA RIGA, non nel nome del
                # file: una sessione in-play dura CINQUE ORE e il suo nome e'
                # l'avvio. Usare il nome schiaccia tutte le letture sull'ora di
                # partenza e fa risultare «zero letture dentro la partita» su
                # partite seguite per novanta minuti -- misurato: 69 partite su
                # 131, tutte false. E' la Fase 151 al contrario (li' l'istante
                # sbagliato era nel nome, qui e' il nome a essere l'istante
                # sbagliato): un tempo preso dal posto comodo invece che da
                # quello giusto.
                q = r.get("istante_utc")
                e["live_t"].add(dt.datetime.fromisoformat(q) if q else t)
                e["live_mercati"].add(r["mercato"])
            else:
                m = e["pre"].setdefault(r["mercato"], {"n": 0, "primo": t, "ultimo": t})
                m["n"] += 1
                m["primo"] = min(m["primo"], t)
                m["ultimo"] = max(m["ultimo"], t)

    for p in arch.snapshots():
        _aggrega(p, arch.leggi(p).get("righe", []), live=False)
    for p in arch.snapshots(LIVE):
        _aggrega(p, arch.leggi(p).get("righe", []), live=True)

    partite = []
    for eid, e in sorted(ev.items(), key=lambda kv: kv[1]["inizio"]):
        k = e["inizio"]
        ore_prima = lambda t: round((k - t).total_seconds() / 3600, 2)  # noqa: E731
        primo = min((v["primo"] for v in e["pre"].values()), default=None)
        ultimo = max((v["ultimo"] for v in e["pre"].values()), default=None)

        # in-play: solo le letture DENTRO la partita, e il buco come Fase 152
        fine = k + dt.timedelta(minutes=MINUTI_PARTITA)
        dentro = sorted(t for t in e["live_t"] if k <= t <= fine)
        buco = None
        if dentro:
            salti = [(dentro[0] - k).total_seconds() / 60]
            salti += [(b - a).total_seconds() / 60 for a, b in zip(dentro, dentro[1:])]
            buco = round(max(salti), 1)

        partite.append({
            "event_id": eid, "partita": e["partita"], "lega": e["lega"],
            "fascia": e["fascia"], "inizio": k.isoformat(),
            "giocata": k < adesso,
            "n_mercati": len(e["pre"]),
            "primo_h": ore_prima(primo) if primo else None,
            "ultimo_h": ore_prima(ultimo) if ultimo else None,
            "ggng": ({"n": e["pre"]["ggng"]["n"],
                      "primo_h": ore_prima(e["pre"]["ggng"]["primo"]),
                      "ultimo_h": ore_prima(e["pre"]["ggng"]["ultimo"])}
                     if "ggng" in e["pre"] else None),
            "chiave_mancanti": [m for m in CHIAVE if m not in e["pre"]],
            "live_letture": len(dentro),
            "live_buco_max_min": buco,
        })
    return {"generato_utc": adesso.isoformat(), "finestra": [DA.isoformat(), A.isoformat()],
            "partite": partite}


def outright_mancanti() -> dict:
    """Quali SERIE outright hanno il buco, e quanti giorni ciascuna.

    Le serie si leggono dai due estremi: se una (fonte, lega, mercato) c'e' il
    12/08 e il 16/08, allora esisteva anche nei tre giorni in mezzo e quei tre
    punti sono persi. Se c'e' solo da un lato, si dichiara -- non si finge di
    sapere se il mercato fosse quotato.
    """
    def serie(giorno: str) -> set:
        f = OUTRIGHT / f"{giorno}.json"
        if not f.exists():
            return set()
        d = json.loads(f.read_text())
        righe = d["rows"] if isinstance(d, dict) and "rows" in d else d
        if isinstance(righe, dict):
            righe = righe.get("entries", [])
        return {(r.get("source"), r.get("league"), r.get("market")) for r in righe}

    prima, dopo = serie("2026-08-12"), serie("2026-08-16")
    entrambi = sorted(prima & dopo)
    return {
        "giorni_mancanti": GIORNI_BUCO,
        "serie_perse": [{"fonte": f, "lega": l, "mercato": m} for f, l, m in entrambi],
        "solo_prima": sorted(f"{f}/{l}/{m}" for f, l, m in prima - dopo),
        "solo_dopo": sorted(f"{f}/{l}/{m}" for f, l, m in dopo - prima),
        "punti_persi": len(entrambi) * len(GIORNI_BUCO),
    }


NOSTRE = {"serie_a", "premier_league", "la_liga", "bundesliga", "ligue_1"}
COPPE_NOSTRE = {"coppa_italia", "community_shield", "supercoppa_uefa",
                "supercoppa_francia", "supercoppa_italia", "supercoppa_spagna"}
# Una sessione in-play dura fino a 5h e committa alla FINE: prima di allora
# «zero letture» non e' un buco, e' un file non ancora scritto (Fase 144).
ORE_GIUDICABILE = 6


def cerchio(x: dict) -> str:
    """In quale dei cerchi del perimetro sta questa partita.

    Serve perche' «manca l'in-play» pesa in modo diverso a seconda del cerchio:
    su un campionato nostro e' una perdita, su una partita del perimetro di
    PROVA (Fase 148) e' il funzionamento previsto — quelle riempiono il carico
    quando c'e' posto e restano fuori quando non ce n'e'.
    """
    if x["lega"] in NOSTRE:
        return "campionato nostro"
    if x["lega"] in COPPE_NOSTRE:
        return "coppa nostra"
    if x["fascia"] == "amichevole":
        return "amichevole"
    if x["lega"] in {"uecl_qual", "uel_qual", "ucl_qual"}:
        return "qual. UEFA"
    return "prova (2a div.)"


def manca(x: dict, adesso: dt.datetime) -> str:
    k = dt.datetime.fromisoformat(x["inizio"])
    if not x["giocata"]:
        return "— (deve ancora giocarsi)"
    buchi = []
    if x["ultimo_h"] is None or x["ultimo_h"] > 3:
        buchi.append("chiusura")
    if x["chiave_mancanti"]:
        buchi.append("mercati: " + ", ".join(x["chiave_mancanti"]))
    if not x["live_letture"]:
        buchi.append("in-play" if (adesso - k).total_seconds() / 3600 > ORE_GIUDICABILE
                     else "in-play (sessione non ancora committata)")
    return "niente" if not buchi else " + ".join(buchi)


def scrivi_md(dati: dict, path: str) -> None:
    adesso = dt.datetime.fromisoformat(dati["generato_utc"])
    p = dati["partite"]
    r = ["| calcio d'inizio (UTC) | cerchio | competizione | partita | mercati "
         "| GG/NG (letture) | prima vista | ultima vista | in-play (letture) "
         "| buco max | cosa manca |",
         "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for x in sorted(p, key=lambda y: y["inizio"]):
        g = x["ggng"]
        prima = f"T−{x['primo_h']:.0f}h" if x["primo_h"] is not None else "—"
        ult = (f"T−{x['ultimo_h']*60:.0f}min" if x["ultimo_h"] is not None
               and abs(x["ultimo_h"]) < 3 else
               (f"T−{x['ultimo_h']:.1f}h" if x["ultimo_h"] is not None else "—"))
        buco = f"{x['live_buco_max_min']:.1f}'" if x["live_buco_max_min"] else "—"
        r.append(f"| {x['inizio'][5:16].replace('T', ' ')} | {cerchio(x)} | "
                 f"{x['lega']} | {x['partita']} | {x['n_mercati']} | "
                 f"{g['n'] if g else 0} | {prima} | {ult} | {x['live_letture']} | "
                 f"{buco} | {manca(x, adesso)} |")
    Path(path).write_text("\n".join(r) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default="experiments/perdite_12_16_agosto.json")
    ap.add_argument("--md", default="experiments/perdite_12_16_agosto_tabella.md",
                    help="la TABELLA per-partita (il documento ragionato la include)")
    a = ap.parse_args(argv)

    dati = raccogli()
    dati["outright"] = outright_mancanti()

    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(dati, ensure_ascii=False, indent=1))
    scrivi_md(dati, a.md)

    p = dati["partite"]
    giocate = [x for x in p if x["giocata"]]
    print(f"partite con calcio d'inizio 12->16/08: {len(p)} ({len(giocate)} gia' giocate)")
    print(f"senza quota GG/NG raccolta:            {sum(1 for x in p if not x['ggng'])}")
    print(f"senza in-play (fra le giocate):        "
          f"{sum(1 for x in giocate if not x['live_letture'])}")
    tardi = [x for x in giocate if x["ultimo_h"] is not None and x["ultimo_h"] > 3]
    print(f"senza un prezzo entro 3h dal via:      {len(tardi)}")
    for x in tardi:
        print(f"   {x['inizio'][:16]}  {x['partita']}  ultimo T-{x['ultimo_h']}h")
    o = dati["outright"]
    print(f"\noutright: {len(o['serie_perse'])} serie x {len(o['giorni_mancanti'])} giorni "
          f"= {o['punti_persi']} punti persi")
    print(f"file scritto: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
