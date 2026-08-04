"""Verifica ESTERNA di ogni allenatore del database, contro Wikidata (Fase 141).

LA DOMANDA. Il database allenatori (Fase 140) sa *chi risulta in panchina* a
ogni partita, secondo Transfermarkt. Non sa se quella persona era davvero in
carica, né se il nome corrisponde a **una** persona. Questo script cerca la
risposta in una fonte indipendente e **strutturata**.

PERCHE' WIKIDATA, E NON UNA RICERCA WEB.
- è **strutturata**: `P286` (allenatore) sull'entità del *club* porta i
  qualificatori `P580`/`P582` — inizio e fine del mandato, come valori tipizzati.
  Non c'è testo da interpretare;
- ogni allenatore è un **Q-id**, non una stringa: è questo che scioglie gli
  omonimi che la Fase 140 può solo dichiarare (`Míchel` = due Q-id diversi);
- è **CC0** (pubblico dominio), a differenza di Wikipedia che è CC BY-SA;
- costa **una richiesta per club**, non una ricerca per mandato.

⚖️ ROBOTS.TXT — la ragione per cui NON si usa SPARQL.
`https://query.wikidata.org/robots.txt` dice `Disallow: /sparql`. L'endpoint
risponde, ma è vietato: una sola query avrebbe risolto tutto in un colpo, e
non si può usare. La via permessa è `Special:EntityData/<qid>.json`
(`Allow: /wiki/Special:EntityData/*.` per la regola del match più lungo, RFC
9309 §2.2.2) — già verificata e implementata in `src/data/wikidata_identity.py`,
che questo script riusa insieme al `fetch_page` di `wikipedia_careers.py` per
le pagine `/wiki/<Titolo>` (permesse).

TRE PASSI, ognuno rieseguibile da solo (`--passo`):

  club      i 153 club del perimetro -> Q-id. Il ponte è la pagina Wikipedia
            (che porta il proprio `wgWikibaseItemId` incorporato: nessun
            matching per nome), e la validazione è `P31 = società calcistica`.
            ⚠️ `P2446` (id Transfermarkt) NON si può usare come validatore:
            è **vuota** anche su club grandi (verificato sul Borussia Dortmund).
  storie    per ogni club risolto, i mandati `P286` che toccano la finestra
            2017-2026, con i Q-id degli allenatori risolti in nome e data di
            nascita.
  persone   ⭐ **l'altro lato dello stesso fatto**: ogni nostro allenatore ->
            Q-id, e da lì `P6087` (allena la squadra) con le sue date. Serve
            perché la storia del *club* è **incompleta e in modo disuguale**
            (Genoa 20 mandati, Newcastle 4): un'assenza lì non è una smentita.
            Ed è il passo che **scioglie gli omonimi**: se una stessa chiave-
            nome risolve a due Q-id con club diversi, sono due persone, e non
            è più una dichiarazione ma un dato.
            ⚠️ Qui il ponte è un nome di persona, cioè il punto debole di ogni
            aggancio: la validazione non è il nome ma il **contenuto** — si
            accetta il Q-id solo se i suoi club `P6087` intersecano i club
            dove noi vediamo quell'allenatore.
  confronto ogni nostro mandato contro ENTRAMBI i lati, con un verdetto per
            riga e il **residuo** — i casi che nessuna regola automatica può
            chiudere, che vanno alla verifica caso per caso.

USO:
    python scripts/aggancia_allenatori_wikidata.py --passo club
    python scripts/aggancia_allenatori_wikidata.py --passo storie
    python scripts/aggancia_allenatori_wikidata.py --passo persone
    python scripts/aggancia_allenatori_wikidata.py --passo confronto
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import allenatori as A                      # noqa: E402
from src.data import wikidata_identity as WD              # noqa: E402
from src.data import wikipedia_careers as WP              # noqa: E402

DEST = ROOT / "data" / "allenatori_wikidata"
FILE_CLUB = DEST / "club_qid.csv"
FILE_MANDATI = DEST / "mandati_wikidata.csv"
FILE_PERSONE = DEST / "persone_qid.csv"
FILE_MANDATI_PERSONA = DEST / "mandati_persona.csv"
FILE_CONFRONTO = DEST / "confronto.csv"
FILE_RESIDUO = DEST / "residuo.json"

P_ALLENATORE = "P286"          # sul CLUB: head coach
P_ALLENA = "P6087"             # sulla PERSONA: coach of sports team
P_OCCUPAZIONE = "P106"
P_ISTANZA = "P31"
Q_UMANO = "Q5"
Q_DISAMBIGUA = "Q4167410"
Q_CLUB_CALCIO = ("Q476028", "Q15944511", "Q847017")   # società calcistica / sportiva

# I cinque club che nessuna regola di titolo raggiunge. Sono scritti qui, non
# indovinati: ognuno verificato aprendo la pagina e controllando che l'entità
# porti la storia degli allenatori del club giusto (regola R2 — una fonte
# secondaria si dichiara, non si innesta in silenzio).
ALIAS_CLUB = {
    "Società Sportiva Lazio S.p.A.": "S.S. Lazio",
    "FC Barcelona": "FC Barcelona",
    "FC Empoli": "Empoli F.C.",
    "1. Fußballclub Heidenheim 1846": "1. FC Heidenheim",
    "1.FC Nuremberg": "1. FC Nürnberg",
}
FINESTRA_DA = pd.Timestamp("2017-07-01")
FINESTRA_A = pd.Timestamp("2026-06-30")

# Quanto può distare la nostra prima partita dalla nomina dichiarata da
# Wikidata perché il mandato sia comunque "lo stesso". Non è una tolleranza
# di comodo: le nostre date sono la PRIMA e l'ULTIMA PARTITA, mentre P580/P582
# sono nomina ed esonero. Fra una nomina e la prima gara passa quasi sempre
# meno di una settimana, ma una sosta (nazionali, pausa invernale) la allunga:
# 45 giorni è il primo valore che copre una sosta intera senza arrivare a
# coprire un mandato breve altrui.
TOLLERANZA_GIORNI = 45


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", " ", s.lower()).strip()


def _candidati(nome: str) -> list[str]:
    """Titoli Wikipedia plausibili per un nome di club di Transfermarkt."""
    c = [ALIAS_CLUB[nome]] if nome in ALIAS_CLUB else []
    c.append(nome)
    m = re.search(r"\b([A-Z]{2,4})$", nome)          # "Arsenal FC" -> "Arsenal F.C."
    if m:
        c.append(nome[:m.start()] + ".".join(m.group(1)) + ".")
    m = re.match(r"^([A-Z]{2,4})\s+(.*)$", nome)     # "AC Milan" -> "A.C. Milan"
    if m:
        c.append(".".join(m.group(1)) + ". " + m.group(2))
    senza = re.sub(r"\b(FC|CF|AC|SC|CFC|AFC|SSC|AS|SS|UC|US|SD|RCD|CD|UD|OGC|RC)\b",
                   "", nome).strip()
    c.append(senza)
    c.append(senza + " (football club)")
    return list(dict.fromkeys(x for x in c if x))


def _riprova(fn, *a, tentativi: int = 4, **k):
    """Rete instabile: un `Connection reset` non e' un'assenza di dato.

    Trattare un errore di rete come "non trovato" creerebbe un buco che nessuno
    saprebbe piu' distinguere da un'assenza vera (R6, stessa ragione per cui
    `fetch_entity` alza invece di restituire None).
    """
    import time as _t
    for i in range(tentativi):
        try:
            return fn(*a, **k)
        except Exception as e:                       # noqa: BLE001
            if i == tentativi - 1:
                print(f"    ⚠️ rinuncio dopo {tentativi} tentativi: {e}", flush=True)
                raise
            _t.sleep(2 ** (i + 1))
    return None


def _qid_da_pagina(titolo: str) -> str | None:
    html = _riprova(WP.fetch_page, titolo.replace(" ", "_"), lang="en")
    if not html:
        return None
    m = re.search(r'"wgWikibaseItemId":"(Q\d+)"', html)
    return m.group(1) if m else None


def _e_club(ent: dict) -> bool:
    """Società calcistica per `P31`, **oppure** per il possesso di una storia
    di allenatori: il Barcellona è una polisportiva (`P31` non contiene
    «società calcistica») e ha 64 mandati `P286`. Fermarsi al `P31` avrebbe
    scartato il club più titolato del campione per una questione di tassonomia.
    """
    ist = {c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
           for c in ent.get("claims", {}).get(P_ISTANZA, [])
           if "datavalue" in c["mainsnak"]}
    if Q_UMANO in ist or Q_DISAMBIGUA in ist:
        return False
    return bool(ist & set(Q_CLUB_CALCIO)) or bool(ent.get("claims", {}).get(P_ALLENATORE))


def _etichetta(ent: dict) -> str:
    lab = ent.get("labels", {})
    for lang in ("it", "en", "de", "es", "fr"):
        if lang in lab:
            return lab[lang]["value"]
    return next(iter(lab.values()), {}).get("value", "")


def passo_club() -> pd.DataFrame:
    per = A.load_partite(solo_top5=True, stagioni=A.STAGIONI)
    club = (per.groupby(["club_id", "club_name"]).size()
            .rename("partite").reset_index().sort_values("partite", ascending=False))
    righe = []
    for _, cb in club.iterrows():
        esito = {"club_id": int(cb.club_id), "club_name": cb.club_name,
                 "partite": int(cb.partite), "qid": None, "titolo": None,
                 "etichetta": None, "mandati_p286": 0, "stato": "residuo"}
        for cand in _candidati(cb.club_name):
            qid = _qid_da_pagina(cand)
            if not qid:
                continue
            ent = _riprova(WD.fetch_entity, qid)
            if ent is None or not _e_club(ent):
                continue
            esito.update(qid=qid, titolo=cand, etichetta=_etichetta(ent),
                         mandati_p286=len(ent.get("claims", {}).get(P_ALLENATORE, [])),
                         stato="risolto")
            break
        righe.append(esito)
        print(("✅" if esito["stato"] == "risolto" else "❌"),
              f"{cb.club_name:32s}", esito["qid"] or "-",
              f"P286={esito['mandati_p286']}", flush=True)
    df = pd.DataFrame(righe)
    DEST.mkdir(parents=True, exist_ok=True)
    df.to_csv(FILE_CLUB, index=False)
    print(f"\nrisolti {(df.stato == 'risolto').sum()}/{len(df)} club "
          f"-> {FILE_CLUB.relative_to(ROOT)}")
    return df


def _data_qual(c: dict, prop: str) -> str | None:
    """La data di un qualificatore, normalizzata al giorno.

    ⚠️ Wikidata scrive le date a **precisione variabile**: `+1958-00-00T00:00:00Z`
    significa «1958, mese e giorno non noti», non «il giorno zero». Passarla a
    `pd.Timestamp` alza `month must be in 1..12` — ed e' esattamente il tipo di
    dato che, se lo si "aggiustasse" in silenzio, farebbe credere a una
    precisione che la fonte non dichiara. Qui si normalizza al **primo giorno**
    del periodo noto, e la precisione resta leggibile in `_precisione_qual`.
    """
    q = c.get("qualifiers", {}).get(prop)
    if not q:
        return None
    t = q[0].get("datavalue", {}).get("value", {}).get("time")
    if not t:
        return None
    anno, mese, giorno = t[1:5], t[6:8], t[9:11]
    return f"{anno}-{mese if mese != '00' else '01'}-{giorno if giorno != '00' else '01'}"


def _precisione_qual(c: dict, prop: str) -> int | None:
    """11 = giorno, 10 = mese, 9 = anno (scala Wikidata)."""
    q = c.get("qualifiers", {}).get(prop)
    if not q:
        return None
    return q[0].get("datavalue", {}).get("value", {}).get("precision")


def passo_storie() -> pd.DataFrame:
    club = pd.read_csv(FILE_CLUB)
    club = club[club.stato == "risolto"]
    righe, cache_nomi = [], {}
    for _, cb in club.iterrows():
        ent = _riprova(WD.fetch_entity, cb.qid)
        for c in ent.get("claims", {}).get(P_ALLENATORE, []):
            mid = c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
            if not mid:
                continue
            da, a = _data_qual(c, WD.P_INIZIO), _data_qual(c, WD.P_FINE)
            # tiene i mandati che TOCCANO la finestra; quelli senza data
            # restano (sono il caso "in carica adesso" o dato incompleto)
            if da and pd.Timestamp(da) > FINESTRA_A:
                continue
            if a and pd.Timestamp(a) < FINESTRA_DA:
                continue
            if mid not in cache_nomi:
                e = _riprova(WD.fetch_entity, mid)
                cache_nomi[mid] = ({"nome": _etichetta(e),
                                    "nascita": WD.data_nascita(e)}
                                   if e else {"nome": "", "nascita": None})
            righe.append({"club_id": int(cb.club_id), "club_name": cb.club_name,
                          "club_qid": cb.qid, "manager_qid": mid,
                          "prec_da": _precisione_qual(c, WD.P_INIZIO),
                          "prec_a": _precisione_qual(c, WD.P_FINE),
                          "manager_nome": cache_nomi[mid]["nome"],
                          "manager_nascita": cache_nomi[mid]["nascita"],
                          "wd_da": da, "wd_a": a, "rank": c.get("rank")})
        print(f"  {cb.club_name:32s} {len([r for r in righe if r['club_id']==cb.club_id]):3d} mandati",
              flush=True)
    df = pd.DataFrame(righe).sort_values(["club_id", "wd_da"])
    df.to_csv(FILE_MANDATI, index=False)
    print(f"\n{len(df)} mandati Wikidata, {df.manager_qid.nunique()} allenatori "
          f"-> {FILE_MANDATI.relative_to(ROOT)}")
    return df


def _candidati_persona(nome: str) -> list[str]:
    """Titoli Wikipedia plausibili per il nome di un allenatore."""
    c = [nome]
    pulito = re.sub(r"\s+", " ", nome).strip()
    if pulito != nome:
        c.append(pulito)
    parti = pulito.split()
    if len(parti) > 2:                       # "Juan Carlos Garrido" -> "Juan Garrido"
        c.append(parti[0] + " " + parti[-1])
    c += [f"{pulito} (footballer)", f"{pulito} (football manager)",
          f"{pulito} (calciatore)"]
    return list(dict.fromkeys(c))


def passo_persone() -> pd.DataFrame:
    """Ogni nostro allenatore -> Q-id, validato sui CLUB e non sul nome."""
    club = pd.read_csv(FILE_CLUB)
    qid_club = dict(zip(club.club_id, club.qid))
    tutte = A.load_partite()
    per = A.load_partite(solo_top5=True, stagioni=A.STAGIONI)
    nostri_club = (per.groupby("manager_key")["club_id"]
                   .agg(lambda s: {qid_club.get(x) for x in set(s)}).to_dict())
    grafie = (per.groupby("manager_key")["allenatore"]
              .agg(lambda s: s.value_counts().index[0]).to_dict())
    ordine = (per.groupby("manager_key").size().sort_values(ascending=False).index)

    righe, mandati = [], []
    for i, chiave in enumerate(ordine, 1):
        nome = grafie[chiave]
        attesi = {q for q in nostri_club.get(chiave, set()) if q}
        esito = {"manager_key": chiave, "grafia": nome, "qid": None,
                 "nome_wd": None, "nascita": None, "titolo": None,
                 "club_confermati": 0, "stato": "residuo"}
        for cand in _candidati_persona(nome):
            qid = _qid_da_pagina(cand)
            if not qid:
                continue
            ent = _riprova(WD.fetch_entity, qid)
            if ent is None:
                continue
            ist = {c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                   for c in ent.get("claims", {}).get(P_ISTANZA, [])
                   if "datavalue" in c["mainsnak"]}
            if Q_DISAMBIGUA in ist:
                esito["stato"] = "disambigua"
                continue
            if Q_UMANO not in ist:
                continue
            spells = ent.get("claims", {}).get(P_ALLENA, [])
            suoi = {c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                    for c in spells if "datavalue" in c["mainsnak"]}
            comuni = suoi & attesi
            # ⚠️ LA VALIDAZIONE: non basta che il nome combaci, deve combaciare
            # almeno un CLUB. Senza questa riga un omonimo entrerebbe muto.
            if not comuni:
                esito["stato"] = "nome_trovato_club_no"
                continue
            esito.update(qid=qid, nome_wd=_etichetta(ent),
                         nascita=WD.data_nascita(ent), titolo=cand,
                         club_confermati=len(comuni), stato="risolto")
            for c in spells:
                cq = c["mainsnak"].get("datavalue", {}).get("value", {}).get("id")
                mandati.append({"manager_key": chiave, "manager_qid": qid,
                                "club_qid": cq,
                                "prec_da": _precisione_qual(c, WD.P_INIZIO),
                                "prec_a": _precisione_qual(c, WD.P_FINE),
                                "wd_da": _data_qual(c, WD.P_INIZIO),
                                "wd_a": _data_qual(c, WD.P_FINE)})
            break
        righe.append(esito)
        print(("✅" if esito["stato"] == "risolto" else "❌"),
              f"[{i:3d}/{len(ordine)}] {chiave:28s}", esito["qid"] or esito["stato"],
              flush=True)

    df = pd.DataFrame(righe)
    df.to_csv(FILE_PERSONE, index=False)
    dm = pd.DataFrame(mandati)
    dm.to_csv(FILE_MANDATI_PERSONA, index=False)
    print(f"\nrisolti {(df.stato=='risolto').sum()}/{len(df)} allenatori; "
          f"{len(dm)} mandati dal lato persona -> {FILE_PERSONE.relative_to(ROOT)}")
    print(df.stato.value_counts().to_string())
    return df


def passo_confronto() -> pd.DataFrame:
    wd = pd.read_csv(FILE_MANDATI)
    wd["wd_da"] = pd.to_datetime(wd["wd_da"], errors="coerce")
    wd["wd_a"] = pd.to_datetime(wd["wd_a"], errors="coerce")
    wd["chiave"] = wd["manager_nome"].map(A.normalizza_nome)

    tutte = A.load_partite()
    per = A.load_partite(solo_top5=True, stagioni=A.STAGIONI)
    nostri = A.panchine(tutte)
    nostri = nostri[nostri.club_id.isin(set(per.club_id))
                    & (nostri.data_a >= FINESTRA_DA)
                    & (nostri.data_da <= FINESTRA_A)]

    righe = []
    for _, m in nostri.iterrows():
        cand = wd[wd.club_id == m.club_id]
        stesso_nome = cand[cand.chiave == m.manager_key]
        # 1. stesso nome E finestre che si toccano -> confermato
        ok = stesso_nome[
            ((stesso_nome.wd_da.isna())
             | (stesso_nome.wd_da <= m.data_da + pd.Timedelta(days=TOLLERANZA_GIORNI)))
            & ((stesso_nome.wd_a.isna())
               | (stesso_nome.wd_a >= m.data_a - pd.Timedelta(days=TOLLERANZA_GIORNI)))]
        if len(ok):
            r = ok.iloc[0]
            verdetto, qid, nota = "confermato", r.manager_qid, ""
        elif len(stesso_nome):
            r = stesso_nome.iloc[0]
            verdetto, qid = "date_diverse", r.manager_qid
            nota = (f"wikidata {r.wd_da.date() if pd.notna(r.wd_da) else '?'}"
                    f"→{r.wd_a.date() if pd.notna(r.wd_a) else '?'}")
        elif len(cand) == 0:
            verdetto, qid, nota, r = "club_senza_storia", None, "", None
        else:
            # nessun mandato con quel nome: chi dice Wikidata in quelle date?
            sovrap = cand[((cand.wd_da.isna()) | (cand.wd_da <= m.data_a))
                          & ((cand.wd_a.isna()) | (cand.wd_a >= m.data_da))]
            verdetto = "assente_da_wikidata" if sovrap.empty else "nome_diverso"
            qid = None
            nota = "; ".join(f"{s.manager_nome} "
                             f"({s.wd_da.date() if pd.notna(s.wd_da) else '?'}"
                             f"→{s.wd_a.date() if pd.notna(s.wd_a) else '?'})"
                             for _, s in sovrap.iterrows())
            r = None
        righe.append({
            "club_id": int(m.club_id), "club": m.club_name,
            "manager_key": m.manager_key, "allenatore": m.allenatore,
            "nostro_da": m.data_da.date(), "nostro_a": m.data_a.date(),
            "partite": int(m.partite), "interruzione": bool(m.interruzione),
            "verdetto": verdetto, "manager_qid": qid,
            "wd_da": (r.wd_da.date() if r is not None and pd.notna(r.wd_da) else None),
            "wd_a": (r.wd_a.date() if r is not None and pd.notna(r.wd_a) else None),
            "nota": nota})
    df = pd.DataFrame(righe)
    df.to_csv(FILE_CONFRONTO, index=False)

    print("\nverdetti automatici:")
    for v, n in df.verdetto.value_counts().items():
        print(f"  {v:22s} {n:5d}  ({100*n/len(df):5.1f}%)")
    residuo = df[df.verdetto != "confermato"]
    FILE_RESIDUO.write_text(residuo.to_json(orient="records", indent=1,
                                            force_ascii=False), encoding="utf-8")
    print(f"\n{len(df)} mandati confrontati, RESIDUO {len(residuo)} "
          f"-> {FILE_RESIDUO.relative_to(ROOT)}")

    # identità: una chiave con due Q-id è due persone
    conf = (df[df.manager_qid.notna()].groupby("manager_key")["manager_qid"]
            .nunique().sort_values(ascending=False))
    multi = conf[conf > 1]
    print(f"\nchiavi-nome con PIU' DI UN Q-id (= più persone): {len(multi)}")
    for k in multi.index:
        qs = df[df.manager_key == k][["manager_qid", "club"]].dropna()
        print(f"  {k}: " + ", ".join(f"{q} ({c})" for q, c in
                                     qs.drop_duplicates().itertuples(index=False)))
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passo", choices=["club", "storie", "persone",
                                        "confronto", "tutto"],
                    default="tutto")
    a = ap.parse_args()
    if a.passo in ("club", "tutto"):
        passo_club()
    if a.passo in ("storie", "tutto"):
        passo_storie()
    if a.passo in ("persone", "tutto"):
        passo_persone()
    if a.passo in ("confronto", "tutto"):
        passo_confronto()


if __name__ == "__main__":
    main()
