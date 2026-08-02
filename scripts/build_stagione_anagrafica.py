"""Costruisce l'anagrafica di inizio stagione 2026-27 (Fase 120, passo 0).

COSA FA. Per ognuna delle 96 squadre delle 5 leghe scrive
`data/stagione_2026_2027/club/<PAESE>/<slug>/anagrafica.json`: identità e
alias, stadio, allenatore, e la **rosa con i valori di mercato**.

DA DOVE VENGONO I DATI, e perché da lì.

  - **l'elenco delle iscritte 2026-27** viene dalle partite d'esordio raccolte
    da Smarkets (`data/smarkets_matches/`): la prima giornata contiene ogni
    squadra esattamente una volta, quindi 20+20+20+18+18 = **96**. È l'unica
    fonte in casa che conosce già la stagione che deve cominciare;
  - **gli attributi** (rosa, valori, stadio, allenatore) vengono dal dataset
    **CC0** `davidcariboo/player-scores` — la fonte ufficiale dello
    `squad_value` del progetto dalla Fase 67. **Non** da Transfermarkt
    direttamente: il suo `robots.txt` vieta `ClaudeBot`/`anthropic-ai`
    (misurato alla Fase 119, `docs/MANUALE_SOPRAVVIVENZA.md` §4-bis).

⚠️ DUE LIMITI, scritti nei file prodotti e non solo qui.

  1. **I valori sono PROVVISORI.** Il dataset si ferma al **27/02/2026**: è la
     fotografia di febbraio, non quella di agosto, e non contiene il mercato
     estivo 2026. Ogni valore esce con la sua `data_valore` e con
     `provvisorio: true`. Vanno sostituiti appena esiste il dato di agosto
     (decisione dell'utente, 28/07/2026).
  2. **Il dataset copre solo la PRIMA divisione** di 31 paesi. Le neopromosse
     quindi o sono **assenti**, o hanno un record **fermo** all'ultima stagione
     in massima serie (es. Málaga 2017). Sono proprio le squadre su cui il
     modello applica il prior δ delle neopromosse: il file lo dichiara con
     `copertura` = `completa` | `stantia` | `assente`, mai riempiendo il vuoto.

USO:
    python scripts/build_stagione_anagrafica.py            # scrive i file
    python scripts/build_stagione_anagrafica.py --dry-run  # solo il resoconto
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEST = ROOT / "data" / "stagione_2026_2027"
KAGGLE_DATASET = "davidcariboo/player-scores"

# La stagione più recente coperta dal dataset. Un club il cui `last_season` è
# più vecchio ha un record STANTIO: non è un errore del dataset, è una squadra
# che in massima serie non ci giocava.
ULTIMA_STAGIONE_NOTA = 2025

LEGA_COMP = {"serie_a": "IT1", "premier_league": "GB1", "la_liga": "ES1",
             "bundesliga": "L1", "ligue_1": "FR1"}
LEGA_PAESE = {"serie_a": "ITA", "premier_league": "ENG", "la_liga": "ESP",
              "bundesliga": "DEU", "ligue_1": "FRA"}

# Mappa alias Smarkets -> nome nel dataset. **Verificata a mano, una voce alla
# volta** (Fase 120): il README di `club/` vieta esplicitamente il match
# approssimato, perché un join sbagliato non lo vede nessun test (R6).
# Qui stanno SOLO i casi che la normalizzazione non risolve da sola.
ALIAS = {
    # Serie A
    "AS Roma": "Associazione Sportiva Roma",
    "Inter Milano": "Inter Milan",
    "Juventus Turin": "Juventus FC",
    "Lazio Rome": "Società Sportiva Lazio S.p.A.",
    "Frosinone Calcio": "Frosinone Calcio",
    # Premier League
    "Newcastle": "Newcastle United",
    "Hull City": "Hull City",
    # LaLiga
    "Atletico Madrid": "Atlético de Madrid",
    "Celta Vigo": "Celta de Vigo",
    "Real Betis": "Real Betis Balompié",
    "Malaga CF": "Málaga CF",
    "RC Deportivo De La Coruna": "Deportivo de La Coruña",
    # Bundesliga
    "FSV Mainz": "1.FSV Mainz 05",
    "Köln": "1.FC Köln",
    "Union Berlin": "1.FC Union Berlin",
    "Schalke 04": "FC Schalke 04",
    "SC Paderborn 07": "SC Paderborn 07",
    # Ligue 1
    "Angers": "Angers SCO",
    "Lille OSC": "LOSC Lille",
    "Stade Brest 29": "Stade Brestois 29",
    "ES Troyes AC": "ESTAC Troyes",
}

# Squadre 2026-27 che nel dataset NON esistono affatto: mai in prima divisione
# nel periodo coperto. Elencarle qui è una DICHIARAZIONE, non una rinuncia:
# il file di quel club nasce lo stesso, con `copertura: "assente"` e la rosa
# vuota, così il buco è visibile invece di sembrare una squadra senza
# giocatori (R6 — il finto pieno).
ASSENTI = {"SV 07 Elversberg", "Racing Santander", "Le Mans FC", "Coventry City"}

_PAROLE_VUOTE = (r"\b(fc|ac|as|ss|us|uc|cf|sv|sc|vfl|vfb|tsg|rc|rcd|ud|cd|afc|"
                 r"bc|ogc|losc|sm|ca|ssd|calcio|football|club|1909|1913|1919|"
                 r"1899|1846|04|05|07|29|96|98)\b")


def _norm(s: str) -> str:
    """Chiave di confronto: senza accenti, senza sigle, senza punteggiatura."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(_PAROLE_VUOTE, " ", s)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def slug(nome: str) -> str:
    """Chiave tecnica della cartella: si sceglie una volta e non si tocca più."""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().lower()
    return "-".join(re.sub(r"[^a-z0-9]+", " ", s).split())


# Sotto questa quota di giocatori valutati l'aggregato NON si pubblica. È la
# stessa soglia di `src.data.transfermarkt.MIN_COVERAGE` (0.85), usata dal
# progetto dalla Fase 59/67 per lo stesso identico scopo: non pubblicare un
# valore rosa costruito su una copertura parziale. Riusarla invece di
# sceglierne un'altra evita due nozioni diverse di "rosa" nello stesso repo.
MIN_COPERTURA_VALORI = 0.85


def valore_aggregato(valori: list[int | None], copertura: str,
                     min_quota: float = MIN_COPERTURA_VALORI) -> int | None:
    """La somma dei valori della rosa, **solo** se la rosa regge due prove.

    PERCHE' ESISTE (R6). Sulle squadre `stantia` il filtro per stagione lascia
    un residuo di 1-8 giocatori su una rosa ufficiale di ~30. Sommarli produce
    un numero che *sembra* una misura: il caso trovato in fase di controllo è
    il **Frosinone a 0.8 M€, calcolato su 1 giocatore su 31** — cioè la rosa
    più debole d'Europa di tre ordini di grandezza, se qualcuno lo usasse.
    `None` dichiarato è informazione; un numero plausibile e falso non lo è.

    Le due prove:
      1. la squadra ha copertura `completa` (il record del club non è vecchio);
      2. almeno l'85% dei giocatori in rosa ha un valore — la soglia che il
         progetto già applica in `transfermarkt.team_season_values`.
    """
    if copertura != "completa" or not valori:
        return None
    veri = [v for v in valori if v]
    if len(veri) / len(valori) < min_quota:
        return None
    return sum(veri) if veri else None


def squadre_2026_27() -> dict[str, set[str]]:
    """Le iscritte, dalle partite d'esordio già raccolte da Smarkets."""
    from src.data import smarkets_archive as _arch

    # ⚠️ «l'ultimo listino COMPLETO», non «l'ultimo file»: l'archivio mescola i
    # giri di lungo raggio (tutte le leghe) con quelli di chiusura (finestra 2h,
    # spesso una lega sola). Prendere il piu' recente e basta costruirebbe le
    # anagrafiche su una lega e nessuno se ne accorgerebbe.
    try:
        ultimo = _arch.ultimo_listino_completo()
    except FileNotFoundError as e:
        raise SystemExit(f"{e}\nEsegui prima scripts/fetch_smarkets_matches.py "
                         "--tutte-le-esposte") from None
    out: dict[str, set[str]] = {}
    for r in _arch.leggi(ultimo)["righe"]:
        if " vs " not in (r.get("partita") or ""):
            continue
        casa, ospite = r["partita"].split(" vs ", 1)
        out.setdefault(r["lega"], set()).update([casa.strip(), ospite.strip()])
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra il resoconto senza scrivere file")
    a = ap.parse_args(argv)

    import kagglehub  # import tardivo: serve la rete, non deve pesare sull'import
    import pandas as pd

    base = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    clubs = pd.read_csv(base / "clubs.csv")
    players = pd.read_csv(base / "players.csv")
    print(f"dataset CC0: {len(clubs)} club, {len(players)} giocatori")

    per_nome = {r["name"]: r for _, r in clubs.iterrows()}
    indice: dict[tuple[str, str], list] = {}
    for _, r in clubs.iterrows():
        indice.setdefault((r.domestic_competition_id, _norm(r["name"])), []).append(r)

    oggi = dt.datetime.now(dt.timezone.utc).date().isoformat()
    conti = {"completa": 0, "stantia": 0, "assente": 0}
    scritti = 0

    for lega, squadre in sorted(squadre_2026_27().items()):
        comp, paese = LEGA_COMP[lega], LEGA_PAESE[lega]
        for nome_smarkets in sorted(squadre):
            club = None
            if nome_smarkets in ALIAS:
                club = per_nome.get(ALIAS[nome_smarkets])
            else:
                cand = indice.get((comp, _norm(nome_smarkets)), [])
                club = cand[0] if len(cand) == 1 else None

            if nome_smarkets in ASSENTI or club is None:
                copertura, rosa = "assente", []
                ultima = None
            else:
                ultima = int(club.last_season)
                copertura = "completa" if ultima >= ULTIMA_STAGIONE_NOTA else "stantia"
                # ⚠️ Il filtro sull'ultima stagione DEL GIOCATORE non è un
                # dettaglio: `current_club_id` punta all'ultimo club noto, quindi
                # senza filtro il Genoa risultava di **162** giocatori (fino a
                # gente ferma al 2017). Una "rosa" così non è una rosa: è un
                # finto pieno (R6). Verificato contro `squad_size`, il conteggio
                # ufficiale nella stessa fonte.
                p = players[(players.current_club_id == club.club_id)
                            & (players.last_season >= ULTIMA_STAGIONE_NOTA)]
                rosa = [{
                    "nome": r["name"], "ruolo": r.position, "ruolo_dettaglio": r.sub_position,
                    "nascita": r.date_of_birth, "nazionalita": r.country_of_citizenship,
                    "piede": r.foot, "altezza_cm": r.height_in_cm,
                    "scadenza_contratto": r.contract_expiration_date,
                    "presenze_nazionale": r.international_caps,
                    # ⚠️ PROVVISORIO: fotografia di febbraio 2026, mercato estivo escluso
                    "valore_eur": None if pd.isna(r.market_value_in_eur) else int(r.market_value_in_eur),
                    "valore_massimo_eur": None if pd.isna(r.highest_market_value_in_eur)
                                          else int(r.highest_market_value_in_eur),
                } for _, r in p.iterrows()]

            conti[copertura] += 1
            valori = [g["valore_eur"] for g in rosa if g["valore_eur"]]

            # ⚠️ L'AGGREGATO ESISTE SOLO SE LA ROSA È COMPLETA.
            # Sulle squadre stantie il filtro per stagione lascia un residuo di
            # 1-8 giocatori su una rosa ufficiale di ~30: sommarne i valori
            # produce numeri che SEMBRANO una misura e non lo sono. Il caso
            # limite trovato in fase di controllo: Frosinone, "valore rosa
            # 0.8M€" calcolato su **1 giocatore su 31** — chi lo usasse in un
            # modello lo leggerebbe come la rosa più debole d'Europa. Meglio
            # `null` dichiarato che un numero plausibile e falso (R6).
            uff = None if club is None or pd.isna(club.squad_size) else int(club.squad_size)
            valore_rosa = valore_aggregato(valori, copertura)
            doc = {
                "_avvertenza": (
                    "VALORI PROVVISORI: fotografia del 2026-02-27 (dataset CC0), NON "
                    "di agosto 2026 — il mercato estivo non è incluso. Da sostituire "
                    "appena il dato di agosto è disponibile. Vedi README §3-bis."),
                "stagione": "2026-27",
                "lega": lega,
                "paese": paese,
                "nome_smarkets": nome_smarkets,
                "nome_dataset": None if club is None else club["name"],
                "slug": slug(nome_smarkets),
                "alias": {"smarkets": nome_smarkets,
                          "player_scores": None if club is None else club["name"]},
                "copertura": copertura,
                "ultima_stagione_nel_dataset": ultima,
                "stadio": None if club is None else {
                    "nome": club.stadium_name, "capienza": None if pd.isna(club.stadium_seats)
                    else int(club.stadium_seats)},
                "allenatore_dataset": None if club is None or pd.isna(club.coach_name)
                                      else club.coach_name,
                "rosa": rosa,
                "rosa_n": len(rosa),
                # Il conteggio UFFICIALE della stessa fonte, tenuto accanto al
                # nostro invece che al posto suo. I due non coincidono: il nostro
                # è tipicamente **+7** (mediana sulle 96 squadre), quasi certamente
                # per prestiti in uscita e giovani aggregati. Dichiararlo è la
                # regola R4: un'anomalia si scrive anche quando non è un errore.
                "squad_size_ufficiale": uff,
                "rosa_copertura": None if not uff else round(len(rosa) / uff, 2),
                "nota_rosa": ("`rosa_n` è il nostro conteggio (giocatori col club "
                              "corrente e almeno una stagione recente); "
                              "`squad_size_ufficiale` è quello della fonte. Lo scarto "
                              "mediano è +6: NON usare `rosa_n` come dimensione "
                              "ufficiale della rosa. `valore_rosa_eur` è `null` "
                              "quando la rosa NON è completa: su una rosa parziale "
                              "la somma dei valori è un numero falso, non una stima."),
                "valore_rosa_eur": valore_rosa,
                "data_valore": "2026-02-27",
                "provvisorio": True,
                "fonte": f"kaggle:{KAGGLE_DATASET} (CC0) + smarkets (elenco iscritte)",
                "generato_utc": oggi,
                # Ciò che il dataset NON dà e va raccolto a parte (README §4.1)
                "da_raccogliere": ["obiettivi_dichiarati", "lista_uefa",
                                   "fuori_progetto", "competizioni_2026_27",
                                   "coordinate_stadio"],
            }
            if not a.dry_run:
                d = DEST / "club" / paese / doc["slug"]
                d.mkdir(parents=True, exist_ok=True)
                (d / "anagrafica.json").write_text(
                    json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
                scritti += 1

    tot = sum(conti.values())
    print(f"\nsquadre: {tot}")
    print(f"  copertura completa : {conti['completa']:3d}")
    print(f"  ⚠️ stantia (record vecchio, neopromossa) : {conti['stantia']:3d}")
    print(f"  ⚠️ assente (mai in 1ª divisione nel dataset): {conti['assente']:3d}")
    print("\n--dry-run: nessun file scritto." if a.dry_run
          else f"\nscritti {scritti} file anagrafica.json")


if __name__ == "__main__":
    main()
