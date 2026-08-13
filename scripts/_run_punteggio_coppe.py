"""Il punteggio delle coppe somma la lotteria dei rigori? Misurato, non dedotto.

Ogni numero della `RIGORI_NEL_PUNTEGGIO` di `src/data/tre_fonti.py` esce da qui.

⚠️ LA DOMANDA NON HA UNA RISPOSTA SOLA, ed e' il punto. Nelle raccolte a tre
fonti convivono DUE convenzioni per `Gol casa/trasferta (SofaScore)`:

    Europa League, Conference   -> il punteggio SOMMA i rigori   (va riparato)
    Champions, sei supercoppe   -> il punteggio e' gia' pulito   (non toccare)

Non si deduce dal torneo (sono tutte UEFA), non si deduce dalla fonte (e' sempre
SofaScore), non si deduce dalla presenza dei rigori (ci sono in tutte). L'unico
modo e' misurarla per raccolta — e rifarlo su ogni consegna nuova.

Il costo di non averlo fatto: per un mese `punteggio_vero()` ha restituito il
punteggio GONFIATO sull'Europa League, perche' l'integrazione aveva ragionato
per file («la Conference dichiara le colonne derivate, quindi le UEFA sono
coperte») invece che per raccolta. Un «Partizan-AEK Larnaca 7-7» che era 2-1.

TRE PROVE INDIPENDENTI, in ordine di forza:

 1. **I gol contati negli EVENTI** — il dato piu' fine della stessa fonte
    (R5 passo 1). ⚠️ Contarli e' meno ovvio di quanto sembri: i rigori segnati
    sono `Tipo=Gol` con `Sottotipo=penalty`, mentre `Tipo=Rigore` esiste SOLO
    col sottotipo `missed`. Contare `Tipo in (Gol, Rigore)` gonfia il conto dei
    rigori sbagliati — errore commesso e corretto scrivendo questo script.
 2. **La colonna DERIVATA che la Conference dichiara da sola**: se la nostra
    sottrazione la riproduce, la regola non e' inventata da noi.
 3. **L'identita' dei tempi** `Gol == 1T + 2T + supplementari`: dove regge, il
    punteggio non puo' contenere i rigori.

Uso:
    python scripts/_run_punteggio_coppe.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import tre_fonti as tf  # noqa: E402


def gol_dagli_eventi(lega: str) -> pd.Series:
    """I gol VERI di ogni squadra-partita, contati uno per uno negli eventi.

    ⚠️ `Tipo=Rigore` sono i rigori **sbagliati** (nell'Europa League: 29 righe,
    tutte `missed`). I rigori segnati stanno gia' fra i `Gol`, col sottotipo
    `penalty`. Sommarli sarebbe contarli due volte al contrario: si conterebbe
    come gol un rigore fallito.
    """
    ev = tf.eventi(lega, categoria="Evento").dropna(subset=["Squadra"])
    segnati = ev[ev["Tipo"] == "Gol"]
    return segnati.groupby(["Data", "Squadra"]).size().rename("gol_eventi")


def _lato(df: pd.DataFrame, casa: str, trasferta: str) -> pd.Series:
    return df.apply(lambda r: r[casa] if r["Campo"] == "Casa" else r[trasferta], axis=1)


def prova_eventi(lega: str) -> dict:
    s = tf.squadre(lega, periodo="Totale").set_index(["Data", "Squadra"])
    s = s.join(gol_dagli_eventi(lega))
    s["gol_eventi"] = s["gol_eventi"].fillna(0)
    grezzo = _lato(s, "Gol casa (SofaScore)", "Gol trasferta (SofaScore)")
    rig = pd.to_numeric(_lato(s, *tf.COLONNE_RIGORI), errors="coerce")
    con = rig.notna() & (rig.notna())
    lotteria = s[con]
    senza = s[~con]
    return {
        "squadra_partita": len(s),
        "con_lotteria": int(con.sum()),
        "sottraendo_ok": int(((grezzo - rig.fillna(0))[con] == lotteria["gol_eventi"]).sum()),
        "grezzo_ok": int((grezzo[con] == lotteria["gol_eventi"]).sum()),
        "senza_lotteria": len(senza),
        "senza_lotteria_ok": int((grezzo[~con] == senza["gol_eventi"]).sum()),
    }


def prova_tempi(lega: str) -> dict:
    """`Gol == 1T + 2T + supplementari`. Dove regge, i rigori non sono dentro."""
    s = tf.squadre(lega, periodo="Totale")
    s = s[s["Campo"] == "Casa"]
    num = lambda c: pd.to_numeric(s[c], errors="coerce").fillna(0) if c in s else 0  # noqa: E731
    casa = num("Casa 1T (SofaScore)") + num("Casa 2T (SofaScore)") + num("Casa suppl. (SofaScore)")
    via = (num("Trasferta 1T (SofaScore)") + num("Trasferta 2T (SofaScore)")
           + num("Trasferta suppl. (SofaScore)"))
    ok = (s["Gol casa (SofaScore)"] == casa) & (s["Gol trasferta (SofaScore)"] == via)
    rig = pd.to_numeric(s[tf.COLONNE_RIGORI[0]], errors="coerce") if tf.COLONNE_RIGORI[0] in s else None
    return {"partite": len(s), "identita_ok": int(ok.sum()),
            "partite_ai_rigori": int(rig.notna().sum()) if rig is not None else 0}


def main() -> None:
    coppe = [k for k in tf.RIGORI_NEL_PUNTEGGIO if k in tf.leghe_disponibili()]

    print("=" * 78)
    print("PROVA 1 · i gol contati negli EVENTI (il dato piu' fine della stessa fonte)")
    print("=" * 78)
    print(f"\n{'raccolta':26s} {'sq-partita':>10s} {'lotteria':>9s} "
          f"{'Gol−Rigori':>11s} {'Gol grezzo':>11s} {'senza lotteria':>15s}")
    for k in coppe:
        try:
            r = prova_eventi(k)
        except Exception as e:                       # raccolte senza blocco eventi utile
            print(f"  {k:24s} eventi non confrontabili: {type(e).__name__}")
            continue
        print(f"  {k:24s} {r['squadra_partita']:10d} {r['con_lotteria']:9d} "
              f"{r['sottraendo_ok']:>6d}/{r['con_lotteria']:<4d} "
              f"{r['grezzo_ok']:>6d}/{r['con_lotteria']:<4d} "
              f"{r['senza_lotteria_ok']:>7d}/{r['senza_lotteria']:<7d}")

    print("\n" + "=" * 78)
    print("PROVA 2 · contro la colonna DERIVATA che la Conference dichiara da sola")
    print("=" * 78)
    s = tf.squadre("uefa_conference_league", periodo="Totale")
    rig_c = pd.to_numeric(s[tf.COLONNE_RIGORI[0]], errors="coerce")
    con = rig_c.notna()
    nostro_c = s.loc[con, "Gol casa (SofaScore)"] - rig_c[con]
    loro_c = pd.to_numeric(s.loc[con, tf.COLONNE_PUNTEGGIO_VERO[0]], errors="coerce")
    print(f"\n  la nostra sottrazione riproduce la colonna dell'export: "
          f"{int((nostro_c == loro_c).sum())}/{int(con.sum())} squadra-partita")

    print("\n" + "=" * 78)
    print("PROVA 3 · l'identita' dei tempi  Gol == 1T + 2T + supplementari")
    print("=" * 78)
    print(f"\n{'raccolta':26s} {'partite':>8s} {'identita regge':>15s} {'ai rigori':>10s}")
    for k in coppe:
        r = prova_tempi(k)
        print(f"  {k:24s} {r['partite']:8d} {r['identita_ok']:>8d}/{r['partite']:<6d} "
              f"{r['partite_ai_rigori']:10d}")

    print("\n" + "=" * 78)
    print("CONCLUSIONE — la tabella `RIGORI_NEL_PUNTEGGIO` di src/data/tre_fonti.py")
    print("=" * 78)
    for k in coppe:
        stato = "SOMMA i rigori -> riparata in lettura" if tf.RIGORI_NEL_PUNTEGGIO[k] \
                else "gia' pulita -> non si tocca"
        print(f"  {k:26s} {stato}")
    print("\n  ⚠️ Da rifare su OGNI consegna nuova: la convenzione non si eredita.")


if __name__ == "__main__":
    main()
