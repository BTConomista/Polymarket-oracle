"""IL CANE DA GUARDIA: «avrei dovuto raccogliere, l'ho fatto?» (Fase 144).

PERCHE' ESISTE, e perche' e' diverso da tutto il resto.

L'08/08/2026 il progetto ha passato una giornata a irrobustire la raccolta:
ritentativi sui 5xx, buchi dichiarati nel file, budget di tempo, gruppi di
concorrenza separati, tre guardiani sul YAML. Tutte cose che rispondono alla
domanda **«il giro e' andato bene?»**.

Poi il raccoglitore in-play e' stato messo in produzione alle 13:47, GitHub
non ha fatto partire nessun cron, e per mezz'ora non ha raccolto niente
mentre venticinque partite del perimetro erano in corso. Nessun run rosso,
nessuna mail, nessun allarme: **un giro che non parte non produce nulla, e
"nulla" e' esattamente cio' che produce anche una notte tranquilla.**
Se n'e' accorto l'utente. Che se ne accorga l'utente e' il difetto.

Questo script risponde a una domanda diversa e piu' difficile:
**«avrei dovuto raccogliere qualcosa, e l'ho fatto?»** Non guarda i run,
guarda l'ARCHIVIO -- cioe' il risultato -- e cerca il silenzio dove sarebbe
dovuto esserci un dato. E' la regola R6 applicata al processo invece che alla
cella: il buco peggiore non e' il file mancante, e' il file mancante che
somiglia a una notte senza partite.

COSA CONTROLLA (ogni controllo dichiara la sua tolleranza e il suo perche'):

  A. FRESCHEZZA DEL LUNGO RAGGIO -- l'ultimo giro «tutte le esposte» non deve
     avere piu' di 26 ore. E' l'unico giro che vede le partite lontane, e se
     smette nessuno se ne accorge per settimane: le partite continuano a
     essere raccolte dai giri densi quando si avvicinano, solo senza la coda
     di traiettoria che e' il motivo per cui il giro esiste (newseason.md §2).
     26 e non 24: il cron parte con 30-40 minuti di ritardo (misurato), e una
     soglia a 24 suonerebbe per il ritardo invece che per il guasto.

  B. COPERTURA DI CHIUSURA -- ogni partita del perimetro che ha giocato nelle
     ultime 36 ore deve avere almeno un prezzo raccolto entro 3 ore dal calcio
     d'inizio. E' la misura che conta per il test prospettico della Fase 78:
     un prezzo di due settimane prima non e' una chiusura.

  C. COPERTURA IN-PLAY -- ogni partita che ha giocato nelle ultime 36 ore
     dovrebbe avere righe in-play dentro la sua finestra. Qui la tolleranza e'
     esplicita e generosa (si segnala solo se la copertura scende sotto la
     meta' delle partite), perche' il live e' nato oggi e le sessioni possono
     legittimamente non coprire tutto.

  D. BUCHI GIA' DICHIARATI -- `partite_incomplete` e `fuori_perimetro` non
     vuoti nei file recenti. Sono informazioni che i file gia' contengono e
     che nessuno andrebbe mai a leggere.

⚠️ CIO' CHE QUESTO SCRIPT **NON** PUO' FARE. Non puo' garantire di girare: e'
esso stesso un cron, e vale per lui la stessa inaffidabilita' che sorveglia.
E' il problema di chi sorveglia il sorvegliante, e non ha una soluzione dentro
GitHub Actions -- ha solo mitigazioni: gira spesso, e quando trova qualcosa
esce ROSSO, che e' il canale che arriva davvero all'utente (e' cosi' che e'
cominciata la sessione dell'08/08). Se un giorno smettessero di arrivare mail
rosse *e* i dati, non ci sarebbe niente qui dentro ad accorgersene.

USO:
    python scripts/controlla_raccolta.py            # il rapporto
    python scripts/controlla_raccolta.py --ore 72   # finestra piu' larga
    python scripts/controlla_raccolta.py --json F   # rapporto leggibile a macchina
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import smarkets_archive as _archivio   # noqa: E402

LIVE = ROOT / "data" / "smarkets_live"

# Le soglie, tutte qui e tutte motivate nel docstring.
ORE_LUNGO_RAGGIO = 26      # freschezza dell'ultimo giro «tutte le esposte»
ORE_FINESTRA = 36          # quanto indietro si guarda per le partite giocate
ORE_CHIUSURA = 3           # «chiusura» = un prezzo entro N ore dal via
QUOTA_INPLAY_MINIMA = 0.5  # sotto questa frazione di partite coperte, si segnala


def _iso(s):
    try:
        return dt.datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def carica(cartella: Path, da: dt.datetime) -> list[dict]:
    """I file dell'archivio toccati dopo `da`, gia' letti.

    Si filtra sul NOME (che porta l'istante) e non sul mtime: il mtime di un
    file appena clonato da git e' l'istante del clone, non della raccolta --
    su un runner effimero sarebbero tutti "di adesso".
    """
    fuori = []
    for f in _archivio.snapshots(cartella):
        quando = _iso(f.name.split(".")[0].replace("T", "T").replace("-", ":", 0))
        # il nome e' YYYY-MM-DDTHH-MM-SS: si rimettono i due punti nell'ora
        base = f.name.split(".")[0]
        try:
            g, o = base.split("T")
            quando = dt.datetime.fromisoformat(f"{g}T{o.replace('-', ':')}+00:00")
        except ValueError:
            continue
        if quando >= da:
            d = _archivio.leggi(f)
            d["_file"] = f.name
            d["_quando"] = quando
            fuori.append(d)
    return fuori


def partite_giocate(prematch: list[dict], adesso: dt.datetime,
                    ore: int) -> dict[str, dt.datetime]:
    """Le partite del perimetro il cui calcio d'inizio cade nella finestra.

    Si ricavano dal NOSTRO archivio pre-partita, non da una chiamata all'API:
    cosi' il controllo funziona anche se la rete e' giu' -- ed e' proprio
    quando la rete e' giu' che serve. Il limite e' dichiarato: se non abbiamo
    MAI visto una partita, questo controllo non puo' sapere che esisteva.
    """
    fuori: dict[str, dt.datetime] = {}
    for d in prematch:
        for r in d.get("righe") or []:
            k = _iso(r.get("inizio"))
            if k and adesso - dt.timedelta(hours=ore) <= k <= adesso:
                fuori[r["partita"]] = k
    return fuori


def controlla(adesso: dt.datetime | None = None, ore: int = ORE_FINESTRA) -> dict:
    """Il rapporto completo. `problemi` vuoto = tutto a posto."""
    adesso = adesso or dt.datetime.now(dt.timezone.utc)
    da = adesso - dt.timedelta(hours=max(ore, ORE_LUNGO_RAGGIO) + 24)
    prematch = carica(_archivio.ARCHIVIO, da)
    inplay = carica(LIVE, da) if LIVE.exists() else []

    problemi, note = [], []

    # --- A. freschezza del lungo raggio -------------------------------------
    lunghi = [d for d in prematch if d.get("entro_ore") == 0]
    if not lunghi:
        problemi.append(
            f"A) NESSUN giro di lungo raggio negli ultimi {int((adesso-da).total_seconds()//3600)}h: "
            "e' il solo giro che vede le partite lontane, e la sua traiettoria "
            "non si recupera dopo.")
        eta_lungo = None
    else:
        ultimo = max(lunghi, key=lambda d: d["_quando"])
        eta_lungo = (adesso - ultimo["_quando"]).total_seconds() / 3600
        if eta_lungo > ORE_LUNGO_RAGGIO:
            problemi.append(
                f"A) l'ultimo giro di lungo raggio ha {eta_lungo:.1f}h "
                f"(soglia {ORE_LUNGO_RAGGIO}h): {ultimo['_file']}")

    # --- B. copertura di chiusura -------------------------------------------
    giocate = partite_giocate(prematch, adesso, ore)
    senza_chiusura = []
    for partita, kickoff in sorted(giocate.items(), key=lambda kv: kv[1]):
        limite = kickoff - dt.timedelta(hours=ORE_CHIUSURA)
        visto = any(
            limite <= d["_quando"] <= kickoff
            and any(r["partita"] == partita for r in (d.get("righe") or []))
            for d in prematch)
        if not visto:
            senza_chiusura.append((partita, kickoff.isoformat()))
    if senza_chiusura:
        problemi.append(
            f"B) {len(senza_chiusura)}/{len(giocate)} partite giocate nelle "
            f"ultime {ore}h senza un prezzo entro {ORE_CHIUSURA}h dal via: "
            + ", ".join(p for p, _ in senza_chiusura[:6])
            + (" …" if len(senza_chiusura) > 6 else ""))

    # --- C. copertura in-play ------------------------------------------------
    coperte = set()
    for d in inplay:
        coperte.update(d.get("partite") or [])
    quota = len(coperte & set(giocate)) / len(giocate) if giocate else 1.0
    if giocate and quota < QUOTA_INPLAY_MINIMA:
        problemi.append(
            f"C) in-play su {len(coperte & set(giocate))}/{len(giocate)} "
            f"partite giocate ({quota:.0%}, soglia {QUOTA_INPLAY_MINIMA:.0%}): "
            "la sentinella non sta girando, oppure gira quando non serve.")

    # --- D. buchi gia' dichiarati nei file ------------------------------------
    recenti = [d for d in prematch if adesso - d["_quando"] <= dt.timedelta(hours=ore)]
    for d in recenti:
        if d.get("partite_incomplete"):
            note.append(f"D) {d['_file']}: {len(d['partite_incomplete'])} "
                        f"partite incomplete dichiarate")
        if d.get("leghe_senza_partite_esposte"):
            problemi.append(f"D) {d['_file']}: leghe senza partite esposte "
                            f"{d['leghe_senza_partite_esposte']}")
        if d.get("fuori_perimetro"):
            note.append(f"D) {d['_file']}: fuori perimetro "
                        f"{list(d['fuori_perimetro'])[:4]}")

    return {
        "adesso_utc": adesso.isoformat(),
        "finestra_ore": ore,
        "file_prematch": len(prematch),
        "file_inplay": len(inplay),
        "eta_lungo_raggio_ore": round(eta_lungo, 1) if eta_lungo is not None else None,
        "partite_giocate_in_finestra": len(giocate),
        "senza_chiusura": senza_chiusura,
        "copertura_inplay": round(quota, 3),
        "problemi": problemi,
        "note": note,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ore", type=int, default=ORE_FINESTRA)
    ap.add_argument("--json", type=Path, help="scrive il rapporto anche in JSON")
    a = ap.parse_args(argv)

    r = controlla(ore=a.ore)
    print(f"CONTROLLO RACCOLTA — {r['adesso_utc'][:19]}Z (finestra {r['finestra_ore']}h)")
    print(f"  file pre-partita: {r['file_prematch']} | in-play: {r['file_inplay']}")
    print(f"  ultimo lungo raggio: "
          + (f"{r['eta_lungo_raggio_ore']}h fa" if r["eta_lungo_raggio_ore"] is not None else "MAI"))
    print(f"  partite giocate in finestra: {r['partite_giocate_in_finestra']} | "
          f"copertura in-play: {r['copertura_inplay']:.0%}")
    for n in r["note"]:
        print(f"  · {n}")
    if a.json:
        a.json.write_text(json.dumps(r, indent=1, ensure_ascii=False))

    if r["problemi"]:
        # ROSSO, e con dentro il motivo: la mail di GitHub cita la prima riga
        # dell'errore, quindi la prima riga deve dire che cosa manca.
        raise SystemExit("\n⛔ RACCOLTA CON BUCHI:\n" +
                         "\n".join(f"   {p}" for p in r["problemi"]))
    print("\n✅ nessun buco: la raccolta sta facendo il suo lavoro.")


if __name__ == "__main__":
    main()
