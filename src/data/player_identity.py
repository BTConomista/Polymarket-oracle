"""Collega i dati diretta.it (per NOME) al `player_id` del database carriere.

IL PROBLEMA. Le due metà del database giocatori non si parlano:

* le statistiche per giocatore-partita 2025-26 (`src/data/player_stats.py`,
  raccolta diretta.it) hanno **solo il nome**, scritto «Cognome Nome» e **senza
  segni diacritici** — `Garces Facundo`, `Yildiz Kenan`;
* le carriere (`src/data/careers.py`) e tutto ciò che ne deriva sono su
  **`player_id`**, con i nomi scritti «Nome Cognome» **con** i diacritici —
  `Facundo Garcés`, `Kenan Yıldız`.

Finché il ponte non esiste, sapere la carriera di un giocatore e sapere come ha
giocato domenica sono due cose che non si possono mettere nella stessa frase.

LA CHIAVE: `(data, insieme dei token del nome)`. Non il nome, non la squadra.

* la **data** allinea perfettamente — 175 giornate su 175 in comune fra le due
  fonti, misurato;
* l'**insieme** dei token rende l'ordine irrilevante, che è esattamente la
  differenza fra le due convenzioni (`{garces, facundo}` da entrambe le parti);
* la **squadra non serve** e sarebbe dannosa: richiederebbe di allineare anche i
  nomi dei club (un secondo problema di normalizzazione) per guadagnare nulla —
  la coppia (data, nome) è già praticamente univoca: **15 chiavi ambigue su
  35.356**, lo 0,04%.

⚠️ Le chiavi ambigue NON si agganciano. Due giocatori diversi con lo stesso
insieme di token nello stesso giorno esistono, e sceglierne uno a caso
significherebbe attribuire a un giocatore la carriera di un altro — lo stesso
errore che la verifica d'identità Wikidata è servita a chiudere, rifatto qui a
valle. Meglio un buco dichiarato che un aggancio inventato.

⏱️ R8: l'aggancio è **`statico`** — lega un'identità a un'identità, non aggiunge
nessuna misura. Non cambia la disponibilità temporale di ciò che collega: le
statistiche restano `post`, la carriera resta da leggere con `career_before`.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Lettere che NFKD **non** decompone, perché non sono lettere accentate ma
# lettere a sé: la `ı` turca senza punto, la `ø` danese, la `ł` polacca. Senza
# questa tabella `Kenan Yıldız` non aggancia `Yildiz Kenan` — misurato: vale
# 4 giocatori e 101 righe, cioè lo 0,3%.
_TRADUZIONE = str.maketrans({
    "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ß": "ss", "æ": "ae", "Æ": "ae", "ð": "d", "þ": "th",
    "ı": "i", "İ": "i", "ħ": "h", "ŋ": "n", "œ": "oe", "ĸ": "k",
})


def normalizza_nome(nome: str | None) -> frozenset[str]:
    """Il nome ridotto a un **insieme** di token minuscoli e senza diacritici.

    Insieme e non lista: è ciò che rende «Cognome Nome» e «Nome Cognome» la
    stessa chiave. I token di una lettera sola si scartano (iniziali puntate).
    """
    if not isinstance(nome, str) or not nome.strip():
        return frozenset()
    t = nome.translate(_TRADUZIONE)
    t = "".join(c for c in unicodedata.normalize("NFKD", t)
                if not unicodedata.combining(c))
    t = re.sub(r"[^a-z ]", " ", t.lower())
    return frozenset(x for x in t.split() if len(x) > 1)


def _chiave(data, nome) -> str:
    tok = normalizza_nome(nome)
    if not tok:
        return ""
    return f"{pd.Timestamp(data).strftime('%Y%m%d')}|{'_'.join(sorted(tok))}"


def tabella_aggancio(appearances=None, *, dal="2025-07-01") -> pd.DataFrame:
    """La tabella `chiave -> player_id`, costruita dalle `appearances`.

    Le chiavi che mappano a **più di un** `player_id` vengono ESCLUSE, non
    risolte a caso: vedi la nota in testa al modulo.
    """
    from . import careers as C

    app = appearances if appearances is not None else C._load_appearances()
    a = app[app["date"] >= pd.Timestamp(dal)].copy()
    nomi = pd.read_csv(
        C.ROOT_DATA.parent / "files" / "player_scores" / "players.csv.gz",
        usecols=["player_id", "name"],
    )
    a = a.merge(nomi, on="player_id", how="left")
    a["chiave"] = [_chiave(d, n) for d, n in zip(a["date"], a["name"])]
    a = a[a["chiave"] != ""]

    per_chiave = a.groupby("chiave")["player_id"].agg(["nunique", "first"])
    univoche = per_chiave[per_chiave["nunique"] == 1]
    return pd.DataFrame({
        "chiave": univoche.index,
        "player_id": univoche["first"].to_numpy(),
    })


def collega(df: pd.DataFrame, appearances=None, *, colonna_nome="Giocatore",
            colonna_data="Data") -> pd.DataFrame:
    """Aggiunge `player_id` a un DataFrame di statistiche diretta.it.

    Ritorna una COPIA con la colonna in più; le righe non agganciate hanno
    `player_id` nullo — dichiarato, non silenzioso.
    """
    out = df.copy()
    date = pd.to_datetime(out[colonna_data], dayfirst=True)
    out["chiave"] = [_chiave(d, n) for d, n in zip(date, out[colonna_nome])]
    mappa = tabella_aggancio(appearances).set_index("chiave")["player_id"]
    out["player_id"] = out["chiave"].map(mappa)
    return out.drop(columns="chiave")
