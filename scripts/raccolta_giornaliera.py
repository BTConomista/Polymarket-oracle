"""Raccolta giornaliera della stagione 2026-27 — lo scheletro (Fase 122).

COS'E'. Il primo giro verticale della raccolta quotidiana descritta in
`data/stagione_2026_2027/README.md`: una fetta sottile ma **completa**, dal
fetch al file su disco, invece di mezza infrastruttura. È il principio §1.1 del
progetto (tracer bullet prima dei moduli).

COSA SCRIVE, ogni giorno, in `giornaliero/AAAA-MM-GG/`:

  raccolta.json  i record del giorno. Ognuno porta `tipo` ("fatto" o
                 "giudizio"), la `fonte` con l'orario, e -- per i giudizi --
                 l'`evidenza` su cui si basano. In questo scheletro ci sono
                 solo FATTI: i giudizi arrivano col livello 5 del piano.
  fonti.json     **ogni** fetch tentato: url, esito, byte, durata. Anche quelli
                 falliti, anche quelli vuoti.

PERCHE' `fonti.json` NON E' UN ACCESSORIO. È ciò che distingue «quel giorno non
è successo niente» da «quel giorno il raccoglitore non ha girato» -- la stessa
ambiguità che alla Fase 118 ha prodotto un workflow verde che non raccoglieva
nulla. Qui il dato mancante **non si recupera**: un giorno di silenzio va visto.

COSA C'E' IN QUESTO SCHELETRO (livello «fatti», nessun LLM):
  - **prossime partite** delle 5 leghe, dal calendario già raccolto da Smarkets;
  - **arbitro designato**: campo presente ma ancora **da riempire** — vale
    quanto il fattore campo sui cartellini (Fase 125) ed è irrecuperabile
    dopo il fischio (`data/stagione_2026_2027/README.md` §4-bis);
  - **meteo previsto** allo stadio di casa (open-meteo: nessuna chiave, e il suo
    `robots.txt` non pone restrizioni);
  - **quote** più recenti per quelle partite, per riferimento incrociato.

⚠️ L'ORIZZONTE DEL METEO E' 16 GIORNI, misurato: al 28/07/2026 le previsioni
arrivavano al 12 agosto, e una richiesta esplicita per il 15 rispondeva **400**.
Quindi «niente meteo» per una partita lontana è un **non-evento legittimo**, e
va scritto come tale (`fuori_orizzonte`) invece di sembrare un guasto.

USO:
    python scripts/raccolta_giornaliera.py             # scrive il giorno
    python scripts/raccolta_giornaliera.py --dry-run   # mostra e non scrive
    python scripts/raccolta_giornaliera.py --entro-giorni 30
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STAGIONE = ROOT / "data" / "stagione_2026_2027"
CLUB = STAGIONE / "club"
GIORNALIERO = STAGIONE / "giornaliero"

METEO_API = "https://api.open-meteo.com/v1/forecast"
METEO_ORE = "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m"

# Misurato il 28/07/2026: l'API espone 16 giorni di previsione. Oltre risponde
# 400, non una previsione vuota. Il numero sta qui e non sparso nel codice.
METEO_ORIZZONTE_GIORNI = 16

UA = {"User-Agent": "Polymarket-oracle/1.0 (ricerca calcistica; "
                    "https://github.com/BTConomista/Polymarket-oracle)"}


class Registro:
    """Tiene il verbale di OGNI fetch: è `fonti.json`.

    Registra anche i fallimenti e le risposte vuote, perché è esattamente la
    differenza fra «non c'era niente» e «non ha girato» (Fase 118).
    """

    def __init__(self) -> None:
        self.voci: list[dict] = []

    def get(self, url: str, *, timeout: int = 25) -> dict | None:
        t0 = time.time()
        voce = {"url": url, "quando_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                grezzo = r.read()
                voce.update(esito="ok", http=r.status, byte=len(grezzo))
                return json.loads(grezzo)
        except urllib.error.HTTPError as e:
            voce.update(esito="http_error", http=e.code, byte=0)
        except Exception as e:                      # rete, timeout, JSON malformato
            voce.update(esito="errore", errore=type(e).__name__, byte=0)
        finally:
            voce["durata_s"] = round(time.time() - t0, 2)
            self.voci.append(voce)
        return None

    @property
    def falliti(self) -> int:
        return sum(1 for v in self.voci if v["esito"] != "ok")


def prossime_partite(entro_giorni: int) -> list[dict]:
    """Le partite in arrivo, dal calendario già raccolto da Smarkets."""
    file = sorted(glob.glob(str(ROOT / "data" / "smarkets_matches" / "*.json")))
    if not file:
        raise SystemExit("nessuno snapshot in data/smarkets_matches/: "
                         "esegui prima scripts/fetch_smarkets_matches.py")
    dati = json.loads(Path(file[-1]).read_text(encoding="utf-8"))
    adesso = dt.datetime.now(dt.timezone.utc)
    limite = adesso + dt.timedelta(days=entro_giorni)
    viste: dict[tuple, dict] = {}
    for r in dati["righe"]:
        if " vs " not in (r.get("partita") or ""):
            continue
        try:
            inizio = dt.datetime.fromisoformat(
                (r["inizio"] or "").replace("Z", "+00:00"))
        except ValueError:
            continue
        if not (adesso <= inizio <= limite):
            continue
        casa, ospite = (x.strip() for x in r["partita"].split(" vs ", 1))
        viste.setdefault((r["lega"], casa, ospite), {
            "lega": r["lega"], "casa": casa, "ospite": ospite,
            "inizio": r["inizio"], "event_id": r["event_id"],
            "quote_da": Path(file[-1]).name,
        })
    return sorted(viste.values(), key=lambda x: x["inizio"])


def _canonico(nome: str) -> str:
    """Il nome squadra sulla convenzione canonica del progetto.

    ⚠️ Serve perche' il nome con cui Smarkets espone una squadra **cambia**:
    fra il 30 e il 31/07/2026 la borsa e' passata dai nomi formali
    ("Deportivo Alaves", "FC Augsburg") a quelli brevi ("Alaves", "Augsburg"),
    e prima ancora aveva rinominato uno slug di lega (Fase 127). Se il join
    poggia sulla stringa grezza, ogni rinominamento lo rompe in silenzio.
    Canonicalizzando **entrambi i lati** con la mappa che il progetto gia' ha,
    la convenzione del giorno diventa irrilevante.
    """
    from src.data.sources import TEAM_ALIASES

    return TEAM_ALIASES.get(nome, nome)


def _schede_club() -> dict[tuple[str, str], dict]:
    """Le 96 anagrafiche, indicizzate una volta sola per (lega, nome CANONICO).

    L'indice era sul `nome_smarkets` grezzo: il 31/07/2026 la borsa ha
    cambiato convenzione e il join e' passato da 96/96 a 32/96 senza che
    niente fallisse. Ora la chiave e' canonica da entrambi i lati.
    """
    out = {}
    for f in CLUB.glob("*/*/anagrafica.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        out[(d["lega"], _canonico(d["nome_smarkets"]))] = d
    return out


def _coordinate_stadi() -> dict[str, dict]:
    """Le coordinate stanno in un file solo (`_anagrafica/stadi.json`), non
    duplicate in 96 anagrafiche: si ri-scaricano senza riscrivere tutto."""
    f = STAGIONE / "_anagrafica" / "stadi.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8")).get("stadi", {})


def meteo_partita(reg: Registro, lat: float, lon: float,
                  inizio: dt.datetime) -> dict:
    """Previsione all'ora del calcio d'inizio, o il motivo per cui non c'è."""
    giorni = (inizio.date() - dt.datetime.now(dt.timezone.utc).date()).days
    if giorni > METEO_ORIZZONTE_GIORNI:
        # NON è un errore: è una previsione che ancora non esiste. Scriverlo
        # così permette di distinguerla da un fetch fallito quando fra un mese
        # qualcuno rileggerà questi file.
        return {"stato": "fuori_orizzonte", "giorni_mancanti": giorni,
                "orizzonte_giorni": METEO_ORIZZONTE_GIORNI}
    url = f"{METEO_API}?" + urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "hourly": METEO_ORE,
        "timezone": "UTC", "forecast_days": METEO_ORIZZONTE_GIORNI})
    d = reg.get(url)
    if not d or "hourly" not in d:
        return {"stato": "non_disponibile"}
    ore = d["hourly"]["time"]
    bersaglio = inizio.strftime("%Y-%m-%dT%H:00")
    if bersaglio not in ore:
        return {"stato": "ora_non_coperta", "cercata": bersaglio}
    i = ore.index(bersaglio)
    return {
        "stato": "ok", "ora_utc": bersaglio,
        "temperatura_c": d["hourly"]["temperature_2m"][i],
        "precipitazioni_mm": d["hourly"]["precipitation"][i],
        "vento_kmh": d["hourly"]["wind_speed_10m"][i],
        "umidita_pct": d["hourly"]["relative_humidity_2m"][i],
    }


def _disciplina_delle_partite(partite: list[dict]) -> list[dict]:
    """Diffidati e squalificati delle squadre coinvolte, per competizione.

    A stagione non ancora iniziata i cartellini sono zero e la lista e' vuota:
    e' corretto, e va scritto invece di essere taciuto. Il conteggio dei
    cartellini della stagione in corso arrivera' dallo stesso archivio che
    alimenta il resto (`appearances`), aggiornato settimanalmente.
    """
    from src.data.disciplina import REGOLE

    fuori = []
    for p in partite:
        if p["lega"] not in REGOLE:
            continue
        # 🎯 ARBITRO — decisione utente 28/07/2026, su evidenza della Fase 125.
        # Vale quanto il fattore campo nel prevedere i cartellini (+0.00368
        # contro +0.00371, IC entrambi conclusivi), e la sua tendenza PERSISTE
        # da una stagione all'altra (corr +0.352). E' 🔴 irrecuperabile: la
        # designazione esce ~2 giorni prima e sparisce, quindi a posteriori si
        # sa CHI ha arbitrato ma non che cosa sapevamo prima del fischio.
        # Il campo nasce vuoto e dichiarato: e' un buco da riempire, non un
        # dato assente per scelta (README §4-bis).
        fuori.append({
            "tipo": "fatto",
            "cosa": "arbitro_designato",
            "partita": f"{p['casa']} vs {p['ospite']}",
            "lega": p["lega"],
            "inizio": p["inizio"],
            "arbitro": None,
            "var": None,
            "designato_il": None,
            "stato_raccolta": "da_implementare",
            "perche_serve": ("vale quanto il fattore campo sui cartellini "
                             "(Fase 125) e la tendenza persiste fra stagioni"),
            "raccolto_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        })
        fuori.append({
            "tipo": "fatto",
            "cosa": "bollettino_disciplinare",
            "partita": f"{p['casa']} vs {p['ospite']}",
            "lega": p["lega"],
            "inizio": p["inizio"],
            "regola": REGOLE[p["lega"]].fonte,
            "soglie": list(REGOLE[p["lega"]].soglie),
            # Vuoti finche' la stagione non produce cartellini. NON e' un buco
            # da riempire: e' lo stato vero del 28/07/2026.
            "diffidati": [],
            "squalificati": [],
            "stato_calcolo": "stagione non iniziata: nessun cartellino",
            "raccolto_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        })
    return fuori


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entro-giorni", type=int, default=21,
                    help="partite entro N giorni (default 21)")
    ap.add_argument("--dry-run", action="store_true", help="non scrive nulla")
    a = ap.parse_args(argv)

    reg = Registro()
    partite = prossime_partite(a.entro_giorni)
    print(f"partite entro {a.entro_giorni} giorni: {len(partite)}")

    schede, stadi = _schede_club(), _coordinate_stadi()

    # ⚠️ GUARDIA SUL JOIN (aggiunta dopo il guasto del 31/07/2026).
    # Il difetto vero non era il rinominamento: era che il giro restava VERDE
    # mentre 64 squadre su 96 non si agganciavano piu' a nessuna anagrafica.
    # E' la stessa lezione della Fase 118 — «nessuna partita» e «l'API non ci
    # parla piu'» avevano lo stesso aspetto — applicata al join invece che al
    # listino. Si misura PRIMA di raccogliere, ma non si solleva qui: come
    # alla Fase 127, prima si scrive il giorno (i dati non si ri-scaricano),
    # poi si esce rossi.
    squadre = {(p["lega"], p["casa"]) for p in partite} | {
        (p["lega"], p["ospite"]) for p in partite}
    orfane = sorted(f"{lega}/{nome}" for lega, nome in squadre
                    if (lega, _canonico(nome)) not in schede)
    if orfane:
        print(f"⚠️ {len(orfane)}/{len(squadre)} squadre del listino senza "
              f"anagrafica: {orfane[:10]}")

    record: list[dict] = []
    for p in partite:
        casa = schede.get((p["lega"], _canonico(p["casa"])))
        nome_stadio = ((casa or {}).get("stadio") or {}).get("nome")
        coord = stadi.get(nome_stadio) if nome_stadio else None
        inizio = dt.datetime.fromisoformat(p["inizio"].replace("Z", "+00:00"))
        if coord:
            m = meteo_partita(reg, coord["lat"], coord["lon"], inizio)
        else:
            # Buco DICHIARATO, non errore di oggi: senza coordinate il meteo
            # non si può nemmeno chiedere. Distinguere i due casi serve a
            # sapere se rifare il fetch o se andare a prendere il dato mancante.
            m = {"stato": "coordinate_mancanti", "stadio": nome_stadio}
        # ⚠️ LO STADIO E' UN DATO PER-PARTITA, NON UNA PROPRIETA' DELLA SQUADRA.
        # Misurato sulle stagioni 2023+: le partite "in casa" giocate altrove
        # sono il 5,0% in campionato, il 10,8% in coppa nazionale e il **12,3%
        # nelle coppe europee** (Atalanta 29/83, Atlético 30/84, Barcellona
        # 25/82 — ristrutturazioni, requisiti UEFA, squalifiche del campo).
        # Finché non è confermato per la singola partita, quello qui sotto è
        # l'impianto ABITUALE: un'ipotesi dichiarata, non un fatto verificato.
        record.append({
            "tipo": "fatto",
            "cosa": "meteo_previsto",
            "partita": f"{p['casa']} vs {p['ospite']}",
            "lega": p["lega"], "inizio": p["inizio"],
            "stadio": nome_stadio,
            "stadio_confermato": False,
            "stadio_nota": ("impianto abituale della squadra di casa, NON "
                            "confermato per questa partita: nelle coppe europee "
                            "il 12,3% delle gare interne si gioca altrove"),
            "valore": m,
            "fonte": "api.open-meteo.com" if m["stato"] == "ok" else None,
            "raccolto_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        })

    # --- bollettino disciplinare: si CALCOLA, non si cerca ----------------
    # Squalifiche e diffide dipendono solo dai cartellini e dal regolamento
    # (src/data/disciplina.py). E' l'unico pezzo del bollettino che non
    # dipende da nessun sito esterno, quindi l'unico immune ai vincoli di
    # robots.txt della Fase 119. Gli INFORTUNI, invece, richiedono per forza
    # una notizia: restano da fare.
    record += _disciplina_delle_partite(partite)

    oggi = dt.datetime.now(dt.timezone.utc)
    stati: dict[str, int] = {}
    for r in record:
        if r["cosa"] != "meteo_previsto":
            continue          # i record disciplinari non hanno uno `stato` meteo
        s = r["valore"]["stato"]
        stati[s] = stati.get(s, 0) + 1
    print("meteo:", stati or "nessuna partita in finestra")
    print("bollettino disciplinare:",
          sum(1 for r in record if r["cosa"] == "bollettino_disciplinare"), "partite")
    da_fare = sum(1 for r in record if r.get("stato_raccolta") == "da_implementare")
    if da_fare:
        # Visibile a ogni giro, apposta: un campo dichiarato "da fare" che
        # nessuno vede resta da fare per sempre.
        print(f"⚠️  campi ancora DA IMPLEMENTARE in questo giro: {da_fare} "
              f"(arbitro designato — README §4-bis)")
    print(f"fetch: {len(reg.voci)} tentati, {reg.falliti} falliti")

    if a.dry_run:
        print("\n--dry-run: nessun file scritto.")
        return

    d = GIORNALIERO / oggi.date().isoformat()
    d.mkdir(parents=True, exist_ok=True)
    (d / "raccolta.json").write_text(json.dumps({
        "giorno": oggi.date().isoformat(),
        "generato_utc": oggi.isoformat(),
        "livello": "fatti",          # i giudizi arrivano col livello 5 del piano
        "partite_in_finestra": len(partite),
        # Dichiarato nel file, non solo stampato: un giro con meta' listino
        # scollegato deve restare RICONOSCIBILE il giorno dopo, altrimenti
        # l'archivio non distingue «anagrafica assente» da «tutto a posto».
        "squadre_senza_anagrafica": orfane,
        "record": record,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "fonti.json").write_text(json.dumps({
        "giorno": oggi.date().isoformat(),
        "nota": ("verbale di OGNI fetch, riusciti e falliti. Un giorno senza "
                 "questo file è un giorno di cui non sappiamo nulla, e va "
                 "trattato come tale in ogni analisi."),
        "tentati": len(reg.voci), "falliti": reg.falliti,
        "voci": reg.voci,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {d.relative_to(ROOT)}/ (raccolta.json + fonti.json)")

    # Il giro esce ROSSO **dopo** aver scritto, mai prima: le quote e il meteo
    # di oggi non si ri-scaricano domani (stessa scelta della Fase 127).
    if orfane:
        raise SystemExit(
            f"❌ {len(orfane)} squadre del listino non hanno un'anagrafica: "
            f"{orfane[:10]}. Il giorno e' stato scritto lo stesso. Causa tipica: "
            "la borsa ha rinominato le squadre -> aggiungere gli alias mancanti "
            "in src/data/sources.py (TEAM_ALIASES)."
        )


if __name__ == "__main__":
    main()
