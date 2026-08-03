"""Appaiare le due fonti sulle COPPE: quale club e' quale, quale partita e' quale.

PERCHE' ESISTE — e' il bug che chiude. Due script facevano la stessa cosa in due
modi diversi. `registra_raccolta_coppa_diretta.py` sapeva **dedurre** i club
dalle partite, ripiegare sul nome quando il `club_id` non c'e' e appaiare per
sovrapposizione di token dentro la giornata; `aggancia_coppe.py` no — si fermava
a `Agganciatore.aggancia(nome)`. Stesse due fonti, stesso dato, due risultati
diversi:

    Copa del Rey       partite appaiate   117/117  (registra)   77/117  (aggancia)
    Coupe de France    partite appaiate   161/201  (registra)     0/201  (aggancia)

La divergenza **era** la causa principale del buco sulle due coppe nuove, non un
dettaglio di implementazione. Per questo la risoluzione dei club e
l'appaiamento delle partite vivono qui, in un punto solo, e i due script la
chiamano invece di riscriverla.

FORMA DELLE DUE FONTI (e' l'unico accoppiamento che questo modulo ha col resto):

    manuale (diretta.it)     `Data` gg.mm.aaaa, `Casa`, `Ospite`
    automatica (nostra)      `data` ISO, `casa`, `ospite`,
                             `home_club_id`, `away_club_id`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from .club_matching import Agganciatore, normalizza

# Nomi che diretta.it scrive in modo che il registro non riconosce da solo.
# ⚠️ Qui stanno SOLO i casi verificati a candidato unico contro
# `club_names.csv.gz`. Gli esonimi italiani («Stoccarda», «Colonia») NON stanno
# qui: valgono per qualunque fonte in lingua italiana e vivono in
# `club_matching.ALIAS`.
ALIAS_COPPA = {
    "Entella": "Virtus Entella",
    "L.R. Vicenza": "LR Vicenza",
    "Inter": "Inter Milan",
    "Sudtirol": "FC Sudtirol",
    "Juve Stabia": "SS Juve Stabia",
    "Internazionale": "Inter Milan",
}


def chiave_squadra(club_id, nome) -> str:
    """Un lato della chiave di partita: il `club_id` se c'e', il nome se manca.

    ⚠️ La chiave NON puo' essere il solo `club_id`. Nella Coupe de France i club
    sono dilettantistici e il registro player-scores non li ha: tutte le righe
    diventerebbero «data|<NA>|<NA>» e collasserebbero l'una sull'altra — il
    merge esplode in un prodotto cartesiano (201 partite diventavano 4.804) che
    SEMBRA una lista di divergenze. Dove l'id c'e' si usa quello (e' l'identita'
    vera); dove manca si ripiega sul nome normalizzato, che almeno distingue le
    righe fra loro.
    """
    if pd.notna(club_id):
        return str(int(club_id))
    return "~" + "".join(sorted(normalizza(str(nome))))


def chiave_partita(data, id_casa, id_ospite, nome_casa, nome_ospite) -> str:
    """`data|lato casa|lato ospite`, con il ripiego sul nome di `chiave_squadra`."""
    return (f"{str(data)[:10]}"
            f"|{chiave_squadra(id_casa, nome_casa)}"
            f"|{chiave_squadra(id_ospite, nome_ospite)}")


def deduci_club(manuale: pd.DataFrame, automatica: pd.DataFrame,
                ag: Agganciatore) -> dict[str, int]:
    """`nome diretta.it -> club_id` DEDOTTO dalle partite, non scritto a mano.

    ⭐ Il problema che risolve. La Copa del Rey ha 21 nomi che il registro non
    riconosce, e **sette sono ambigui**: «Murcia» ha 4 candidati (Real Murcia,
    UCAM Murcia…), «Ourense CF» e «UD Ourense» sono due club DIVERSI della
    stessa citta', e cosi' «SD Logrones» e «UD Logrones». Scrivere alias a mano
    su nomi cosi' e' il modo migliore per rifare il caso «Brest»: un aggancio
    sbagliato non da' errore, attribuisce le partite a un altro club.

    Il metodo: **l'eliminazione, applicata ai club invece che ai giocatori.**
    Se in una partita una delle due squadre si aggancia gia' e in quella data
    esiste UNA SOLA partita automatica con quel club da quel lato, allora
    l'altra squadra e' determinata — non indovinata.

    Tre garanzie, tutte necessarie:
      1. si accetta solo se la partita candidata e' **unica** nella giornata;
      2. la deduzione dev'essere **coerente su tutte** le partite di quel nome:
         un nome che risulterebbe due club diversi viene scartato del tutto;
      3. se il nome aveva gia' dei candidati per somiglianza, il club dedotto
         **dev'essere fra quelli** — altrimenti si sta contraddicendo il
         registro, e in quel caso non si deduce.
    """
    def risolvi(n):
        return ag.aggancia(ALIAS_COPPA.get(n, n))

    per_data: dict[str, list] = {}
    for r in automatica.itertuples():
        per_data.setdefault(str(r.data)[:10], []).append(
            (r.home_club_id, r.away_club_id))

    proposte: dict[str, set] = {}
    for _, r in manuale.iterrows():
        giorno = pd.to_datetime(r["Data"], format="%d.%m.%Y").strftime("%Y-%m-%d")
        righe = per_data.get(giorno, [])
        casa, osp = risolvi(r["Casa"]), risolvi(r["Ospite"])
        if casa is not None and osp is None:
            cand = {b for a, b in righe if a == casa}
            if len(cand) == 1:
                proposte.setdefault(r["Ospite"], set()).add(next(iter(cand)))
        elif casa is None and osp is not None:
            cand = {a for a, b in righe if b == osp}
            if len(cand) == 1:
                proposte.setdefault(r["Casa"], set()).add(next(iter(cand)))

    dedotti = {}
    for nome, ids in proposte.items():
        if len(ids) != 1:
            continue                                    # garanzia 2
        club = int(next(iter(ids)))
        somiglianti = ag.candidati(ALIAS_COPPA.get(nome, nome))
        if somiglianti and club not in somiglianti:
            continue                                    # garanzia 3
        dedotti[nome] = club
    return dedotti


@dataclass
class Appaiamento:
    """L'esito di `appaia_partite`: le chiavi allineate e come ci si e' arrivati.

    `cid` e' la risoluzione COMPLETA del nome di un club — alias, registro e
    deduzione dalle partite — ed e' la stessa che deve servire le formazioni:
    un club dedotto per le partite e non per le formazioni lascerebbe i
    giocatori di quel club senza `club_id`, quindi senza candidati, quindi
    vuoti.
    """

    cid: Callable[[str], object]
    dedotti: dict[str, int]
    data_iso: list[str]
    k_manuale: list[str]
    k_automatica: list[str]
    rimappate: int
    contese: int


def appaia_partite(manuale: pd.DataFrame, automatica: pd.DataFrame,
                   ag: Agganciatore | None = None) -> Appaiamento:
    """Allinea le partite delle due fonti, in tre passi di forza decrescente.

    1. **club_id** dove il registro li da', **dedotti** dalle partite dove il
       nome non basta (`deduci_club`);
    2. **chiave** `data|lato|lato`, che ripiega sul nome normalizzato quando il
       `club_id` non esiste proprio (club dilettantistici);
    3. ⭐ **appaiamento per nome dentro la giornata** per cio' che resta. Serve
       alla Coupe de France, dove nessuno dei due lati ha un `club_id` (il
       registro non copre ne' la Ligue 2 ne' i dilettanti) e le due fonti
       scrivono il nome in due FORME diverse: diretta.it la corta, la nostra
       fonte quella per esteso — «Cannes»/«AS Cannes», «Grenoble»/«Grenoble Foot
       38», «Sochaux»/«FC Sochaux-Montbéliard». La chiave del passo 2 le vede
       come due squadre diverse; la sovrapposizione dei token no. Dentro una
       singola data le partite sono poche, quindi si accetta **solo** il
       candidato migliore e unico. Misurato: **122 partite su 201** appaiate
       cosi', e in 160 delle 161 coppie i due nomi non coincidono alla lettera.
       Il punteggio non e' la chiave: resta la verifica indipendente che dice se
       l'appaiamento regge (157/161 punteggi identici).

    ⚠️ Una partita automatica contesa da due righe manuali non va a nessuna
    delle due (`contese`). E' la regola di sempre — un aggancio incerto resta
    vuoto — applicata qui: l'alternativa sarebbe far vincere la prima riga in
    ordine di file, cioe' scegliere a caso. Sulle sei coppe raccolte le contese
    sono **zero**: il guardrail non toglie niente a cio' che gia' funzionava.
    """
    if ag is None:
        ag = Agganciatore()

    def per_nome(n):
        return ag.aggancia(ALIAS_COPPA.get(n, n))

    dedotti = deduci_club(manuale, automatica, ag)

    def cid(n):
        c = per_nome(n)
        return c if c is not None else dedotti.get(n)

    data_iso = list(pd.to_datetime(manuale["Data"], format="%d.%m.%Y")
                    .dt.strftime("%Y-%m-%d"))
    ids_casa = [cid(n) for n in manuale["Casa"]]
    ids_osp = [cid(n) for n in manuale["Ospite"]]
    k_man = [chiave_partita(d, a, b, na, nb) for d, a, b, na, nb
             in zip(data_iso, ids_casa, ids_osp, manuale["Casa"], manuale["Ospite"])]
    # ⚠️ Sul lato AUTOMATICO gli identificatori ci sono gia': non si ri-derivano
    # dal nome. Ri-derivarli e' un giro inutile che introduce un punto di
    # rottura — «FC Südtirol-Alto Adige» non si agganciava (il registro lo
    # chiama «FC Südtirol») e la partita Como-Südtirol spariva, pur avendo
    # `home_club_id` scritto nella riga accanto.
    k_aut = [chiave_partita(d, a, b, na, nb) for d, a, b, na, nb
             in zip(automatica["data"], automatica["home_club_id"],
                    automatica["away_club_id"], automatica["casa"],
                    automatica["ospite"])]

    # --- terzo passo: appaiamento per nome dentro la giornata ---------------- #
    insieme_aut, insieme_man = set(k_aut), set(k_man)
    libere: dict[str, list[tuple[str, str, str]]] = {}
    for d, k, casa, osp in zip(automatica["data"], k_aut,
                               automatica["casa"], automatica["ospite"]):
        if k not in insieme_man:
            libere.setdefault(str(d)[:10], []).append((k, str(casa), str(osp)))

    proposte: dict[str, list[str]] = {}
    for d, k, casa, osp in zip(data_iso, k_man, manuale["Casa"], manuale["Ospite"]):
        if k in insieme_aut:
            continue
        punteggi = []
        for k_altra, casa_a, osp_a in libere.get(d, []):
            a = len(normalizza(str(casa)) & normalizza(casa_a))
            b = len(normalizza(str(osp)) & normalizza(osp_a))
            if a and b:
                punteggi.append((a + b, k_altra))
        punteggi.sort(reverse=True)
        # unico migliore, e strettamente migliore del secondo
        if punteggi and (len(punteggi) == 1 or punteggi[0][0] > punteggi[1][0]):
            proposte.setdefault(punteggi[0][1], []).append(k)

    rimappa = {k_da[0]: k_a for k_a, k_da in proposte.items() if len(k_da) == 1}
    contese = sum(len(v) for v in proposte.values() if len(v) > 1)
    if rimappa:
        k_man = [rimappa.get(k, k) for k in k_man]

    return Appaiamento(cid=cid, dedotti=dedotti, data_iso=data_iso,
                       k_manuale=k_man, k_automatica=k_aut,
                       rimappate=len(rimappa), contese=contese)
