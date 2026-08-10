"""Il database allenatori, strato 1: TUTTI i numeri della fase (Fase 140).

Ogni cifra citata nel diario e nel README per questo fronte esce da qui. Non e'
un backtest: non c'e' un modello da valutare, e non ce ne sara' uno finche' i
dati non sono descritti onestamente. E' il censimento di che cosa `games.csv`
sa degli allenatori, e soprattutto di che cosa **non** sa.

LE TRE DOMANDE.

1. **Copertura** — quanto e' pieno il campo, sul perimetro degli snapshot
   (5 leghe x 9 stagioni = 16.111 partite) e fuori.
2. **Identita'** — il nome e' una chiave? Si guarda da due lati opposti:
   quante grafie diverse nascondono lo stesso uomo (si uniscono), e quanti
   uomini diversi si nascondono dietro lo stesso nome (non si separano, si
   dichiarano). Il secondo si misura con un test di impossibilita' fisica:
   nessuno allena due club lo stesso giorno.
3. **Mandati** — quanti sono, quanto durano, quanti cambi in corsa; e i due
   modi di contarli male: tagliarli sul solo campionato, e scambiare il vice
   in panchina per una partita con un mandato vero.

USO:
    python scripts/_run_fase140_allenatori.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import allenatori as A          # noqa: E402

DEST = ROOT / "experiments" / "fase140_allenatori.json"


def _riassunto(serie: pd.Series) -> dict:
    return {"n": int(serie.size), "media": round(float(serie.mean()), 2),
            "mediana": float(serie.median()),
            "p10": float(serie.quantile(0.10)),
            "p90": float(serie.quantile(0.90)),
            "max": float(serie.max())}


def main() -> None:
    games = A._leggi_games()
    tutte = A.load_partite(games)
    perim = A.load_partite(games, solo_top5=True, stagioni=A.STAGIONI)

    print("=" * 72)
    print("1 · COPERTURA")
    print("=" * 72)
    cop = A.rapporto_copertura(games)
    for k, v in cop.items():
        print(f"  {k:42s} {v}")

    per_lega = {}
    for lega in A.TOP5:
        g = games[(games.competition_id == lega)
                  & games.season.isin(A.STAGIONI)]
        senza = int(g.home_club_manager_name.isna().sum()
                    + g.away_club_manager_name.isna().sum())
        per_lega[lega] = {"partite": int(len(g)), "senza_allenatore": senza,
                          "allenatori": int(pd.concat([
                              g.home_club_manager_name,
                              g.away_club_manager_name]).map(
                                  A.normalizza_nome).nunique())}
        print(f"  {lega:5s} partite {len(g):6d}  senza allenatore {senza:3d}"
              f"  allenatori distinti {per_lega[lega]['allenatori']:4d}")

    print()
    print("=" * 72)
    print("2 · IDENTITA' — il nome non e' una chiave")
    print("=" * 72)
    # 2a. grafie diverse, stesso uomo: la normalizzazione le unisce
    gruppi = (tutte.groupby("manager_key")["allenatore"].nunique())
    ambigui = gruppi[gruppi > 1]
    righe_amb = tutte[tutte.manager_key.isin(ambigui.index)]
    gruppi_p = (perim.groupby("manager_key")["allenatore"].nunique())
    ambigui_p = gruppi_p[gruppi_p > 1]
    righe_amb_p = perim[perim.manager_key.isin(ambigui_p.index)]
    print(f"  globale : {tutte.allenatore.nunique()} grafie -> "
          f"{tutte.manager_key.nunique()} chiavi; {len(ambigui)} gruppi uniti, "
          f"{len(righe_amb)} club-partita ({100*len(righe_amb)/len(tutte):.2f}%)")
    print(f"  perimetro: {perim.allenatore.nunique()} grafie -> "
          f"{perim.manager_key.nunique()} chiavi; {len(ambigui_p)} gruppi uniti, "
          f"{len(righe_amb_p)} club-partita "
          f"({100*len(righe_amb_p)/len(perim):.2f}% delle righe, "
          f"{100*righe_amb_p.game_id.nunique()/perim.game_id.nunique():.2f}% "
          f"delle partite)")
    dettaglio_ambigui = []
    for chiave in ambigui_p.index:
        for grafia, s in perim[perim.manager_key == chiave].groupby("allenatore"):
            dettaglio_ambigui.append({
                "manager_key": chiave, "grafia": grafia, "partite": int(len(s)),
                "da": str(s.date.min().date()), "a": str(s.date.max().date())})
            print(f"     {chiave:20s} | {grafia:22s} {len(s):4d} partite  "
                  f"{s.date.min().date()} -> {s.date.max().date()}")

    # 2b. stesso nome, uomini diversi: il test di impossibilita' fisica
    conf = A.conflitti_identita(tutte)
    conf7 = A.conflitti_identita(tutte, giorni=7)
    chiavi_perim = set(perim.manager_key)
    print(f"\n  stesso nome, STESSO GIORNO, due club: "
          f"{conf.manager_key.nunique()} nomi, {len(conf)} coppie")
    for chiave, s in conf.groupby("manager_key"):
        dentro = "  <-- nel perimetro" if chiave in chiavi_perim else ""
        print(f"     {chiave:20s} {len(s):3d} collisioni  "
              f"({s.date_a.min().date()} -> {s.date_a.max().date()}){dentro}")
    print(f"  con finestra di 7 giorni: {conf7.manager_key.nunique()} nomi "
          f"(include i passaggi lampo veri: e' un limite superiore)")

    print()
    print("=" * 72)
    print("3 · MANDATI")
    print("=" * 72)
    grezzi = A.panchine(tutte)
    ricuciti = A.panchine(tutte, ricuci=True)
    print(f"  mandati globali, grezzi   : {len(grezzi)}")
    print(f"  mandati globali, ricuciti : {len(ricuciti)}"
          f"  (assorbite {int(ricuciti.interruzioni.sum())} interruzioni)")
    print(f"  pattern A->X->A (vice in panchina): {int(grezzi.interruzione.sum())}"
          f" = {100*grezzi.interruzione.mean():.2f}% dei mandati, "
          f"di cui {int((grezzi.interruzione & (grezzi.partite == 1)).sum())} "
          f"di una partita sola")
    print(f"  conservazione: {int(ricuciti.partite.sum())} + "
          f"{int(ricuciti.partite_altrui.sum())} = {len(tutte)} righe ✅"
          if ricuciti.partite.sum() + ricuciti.partite_altrui.sum() == len(tutte)
          else "  ⚠️ CONSERVAZIONE ROTTA")

    club_perim = set(perim.club_id)

    def _nella_finestra(m: pd.DataFrame) -> pd.DataFrame:
        return m[m.club_id.isin(club_perim)
                 & (m.data_a >= perim.date.min())
                 & (m.data_da <= perim.date.max())]

    # il confronto «quanto si perde a guardare solo il campionato» si fa sui
    # mandati GREZZI: e' li' che vivono i traghettatori di una partita
    finestra_g = _nella_finestra(grezzi)
    solo_lega_g = A.panchine(perim)
    finestra = _nella_finestra(ricuciti)
    solo_lega = A.panchine(perim, ricuci=True)
    print(f"\n  club del perimetro, timeline COMPLETA : {len(finestra_g)} "
          f"mandati grezzi ({len(finestra)} ricuciti)")
    print(f"  gli stessi, tagliati sul SOLO campionato: {len(solo_lega_g)} "
          f"({len(solo_lega)}) -> {len(finestra_g)-len(solo_lega_g)} "
          f"({len(finestra)-len(solo_lega)}) nascosti")

    durata = _riassunto(finestra.partite)
    print(f"\n  durata di un mandato (partite): mediana {durata['mediana']:.0f}, "
          f"media {durata['media']:.1f}, p10 {durata['p10']:.0f}, "
          f"p90 {durata['p90']:.0f}, max {durata['max']:.0f}")

    cambi = A.cambi_panchina(ricuciti)
    cambi_grezzi = A.cambi_panchina(grezzi)
    perim_key = perim.assign(stagione=A._stagione(perim.date))
    cs = perim_key.groupby(["club_id", "stagione"])["manager_key"].nunique()
    print(f"\n  cambi in corso di stagione (globale, mandati ricuciti): {len(cambi)}")
    print(f"  gli stessi contati sui mandati grezzi                  : "
          f"{len(cambi_grezzi)}  -> +{len(cambi_grezzi)-len(cambi)} eventi finti")
    print(f"  club-stagione del perimetro con piu' di un allenatore  : "
          f"{int((cs > 1).sum())}/{len(cs)} ({100*(cs > 1).mean():.1f}%)")

    print()
    print("=" * 72)
    print("4 · ESPERIENZA — quanta se ne vede davvero")
    print("=" * 72)
    # all'inizio dell'ultima stagione del perimetro
    as_of = "2025-08-01"
    esp = A.esperienza_prima(as_of, tutte)
    attivi = set(perim[perim.date >= as_of].manager_key)
    esp_attivi = esp[esp.index.isin(attivi)]
    mai_visti = sorted(attivi - set(esp.index))
    print(f"  allenatori in panchina nelle 5 leghe dopo il {as_of}: {len(attivi)}")
    print(f"    senza NESSUNA partita precedente visibile: {len(mai_visti)} "
          f"({100*len(mai_visti)/len(attivi):.1f}%)")
    print(f"    con esperienza CENSURATA a sinistra      : "
          f"{int(esp_attivi.censurata.sum())} "
          f"({100*esp_attivi.censurata.mean():.1f}% di chi ne ha)")
    print(f"    mediana delle partite viste prima        : "
          f"{esp_attivi.partite_prima.median():.0f}")
    print(f"    esempi senza passato visibile: {', '.join(mai_visti[:8])}")

    falsi = ["carlo ancelotti", "jose mourinho", "claudio ranieri",
             "roy hodgson", "ronald koeman"]
    print("\n  i falsi esordi che il bordo del dataset produce:")
    falsi_dett = {}
    for nome in falsi:
        s = tutte[tutte.manager_key == nome]
        st = perim[perim.manager_key == nome]
        prima = s.loc[s.date.idxmin()]
        falsi_dett[nome] = {
            "prima_partita_visibile": str(prima.date.date()),
            "competizione": prima.competition_id,
            "prima_nel_perimetro": str(st.date.min().date()) if len(st) else None,
            "partite_visibili": int(len(s))}
        print(f"     {nome:18s} prima visibile {prima.date.date()} "
              f"({prima.competition_id}), {len(s)} partite in tutto")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "fase": 140,
        "fonte": A.FONTE,
        "copertura": cop,
        "copertura_per_lega": per_lega,
        "identita": {
            "grafie_globali": int(tutte.allenatore.nunique()),
            "chiavi_globali": int(tutte.manager_key.nunique()),
            "gruppi_uniti_globali": int(len(ambigui)),
            "grafie_perimetro": int(perim.allenatore.nunique()),
            "chiavi_perimetro": int(perim.manager_key.nunique()),
            "gruppi_uniti_perimetro": int(len(ambigui_p)),
            "partite_toccate_perimetro": int(righe_amb_p.game_id.nunique()),
            "quota_partite_perimetro": round(
                righe_amb_p.game_id.nunique() / perim.game_id.nunique(), 4),
            "dettaglio_gruppi_perimetro": dettaglio_ambigui,
            "omonimi_stesso_giorno": int(conf.manager_key.nunique()),
            "omonimi_stesso_giorno_nomi": sorted(conf.manager_key.unique()),
            "omonimi_nel_perimetro": sorted(
                set(conf.manager_key) & chiavi_perim),
            "omonimi_finestra_7_giorni": int(conf7.manager_key.nunique()),
        },
        "mandati": {
            "globali_grezzi": int(len(grezzi)),
            "globali_ricuciti": int(len(ricuciti)),
            "interruzioni": int(grezzi.interruzione.sum()),
            "interruzioni_una_partita": int(
                (grezzi.interruzione & (grezzi.partite == 1)).sum()),
            "perimetro_timeline_completa": int(len(finestra_g)),
            "perimetro_solo_lega": int(len(solo_lega_g)),
            "perimetro_timeline_completa_ricuciti": int(len(finestra)),
            "perimetro_solo_lega_ricuciti": int(len(solo_lega)),
            "durata_partite": durata,
            "cambi_in_stagione_ricuciti": int(len(cambi)),
            "cambi_in_stagione_grezzi": int(len(cambi_grezzi)),
            "club_stagione_con_piu_allenatori": int((cs > 1).sum()),
            "club_stagione_totali": int(len(cs)),
        },
        "esperienza": {
            "as_of": as_of,
            "allenatori_attivi": len(attivi),
            "senza_passato_visibile": len(mai_visti),
            "censurati": int(esp_attivi.censurata.sum()),
            "mediana_partite_prima": float(esp_attivi.partite_prima.median()),
            "falsi_esordi": falsi_dett,
        },
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nscritto {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
