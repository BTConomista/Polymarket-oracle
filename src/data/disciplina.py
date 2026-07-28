"""Squalifiche e diffide: le regole per competizione, e il loro effetto (Fase 123).

PERCHE' STA QUI E NON FRA LE FONTI DA CERCARE. Squalifiche e diffide non vanno
**cercate**: si **calcolano**. Bastano i cartellini (che il progetto ha, con il
minuto, da ``game_events``) e il regolamento della competizione. E' l'opposto
degli infortuni, che richiedono per forza una notizia esterna.

Conseguenza pratica: questo e' il pezzo del bollettino quotidiano che funziona
**senza dipendere da nessun sito** -- quindi senza i vincoli di ``robots.txt``
che limitano il resto (Fase 119).

⚠️ LE REGOLE NON SONO UNIVERSALI E CAMBIANO NEL TEMPO. La Ligue 1 e' passata a
**5** ammonizioni dalla stagione 2025-26 (prima erano 3): chi codificasse "il
calcio" con una soglia unica sbaglierebbe due leghe su cinque e la UEFA. Per
questo le soglie stanno in una TABELLA con la fonte accanto, non sparse nel
codice.

FONTI (lette il 28/07/2026, non a memoria):
  Serie A   art. 19 c.9 Codice di Giustizia Sportiva -- diffida al 4°, squalifica
            al 5°, poi soglie che si stringono (10, 14, 17, 19, poi ogni)
  Premier   5 ammonizioni entro la 19ª giornata -> 1 turno; 10 entro la 32ª ->
            2 turni; 15 -> 3 turni
  LaLiga    5 ammonizioni -> 1 turno
  Bundesliga 5 ammonizioni -> 1 turno
  Ligue 1   5 ammonizioni -> 1 turno (dal 2025-26; prima 3)
  UEFA      art. 63 del regolamento: 3 ammonizioni -> 1 turno, poi a ogni
            ammonizione DISPARI successiva (5ª, 7ª...). I gialli si azzerano
            dopo i play-off e di nuovo dopo i quarti.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Regola:
    """Le soglie di una competizione, e come si contano."""

    #: numero di ammonizioni a cui scatta una squalifica, in ordine
    soglie: tuple[int, ...]
    #: turni di squalifica per ciascuna soglia (stessa lunghezza di `soglie`)
    turni: tuple[int, ...]
    #: dopo l'ultima soglia esplicita, ogni quante ammonizioni si e' squalificati
    #: (0 = non si ripete piu')
    passo_dopo_ultima: int = 0
    #: momenti in cui i gialli si azzerano (solo descrittivo, per il diario)
    azzeramenti: tuple[str, ...] = ()
    fonte: str = ""
    #: parti della regola che NON siamo riusciti a verificare su fonte primaria
    incerto: tuple[str, ...] = field(default_factory=tuple)


# I cartellini si contano PER COMPETIZIONE: un giallo in campionato non conta
# in coppa, ed e' il motivo per cui la stessa squadra puo' avere due liste di
# diffidati diverse nello stesso weekend.
REGOLE: dict[str, Regola] = {
    "serie_a": Regola(
        soglie=(5, 10, 14, 17, 19), turni=(1, 1, 1, 1, 1), passo_dopo_ultima=1,
        azzeramenti=("fine stagione",),
        fonte="art. 19 c.9 Codice di Giustizia Sportiva (FIGC)"),
    "premier_league": Regola(
        soglie=(5, 10, 15), turni=(1, 2, 3), passo_dopo_ultima=0,
        azzeramenti=("dopo la 19ª giornata", "dopo la 32ª giornata"),
        fonte="regolamento Premier League",
        incerto=("le prime due soglie valgono solo entro la 19ª e la 32ª "
                 "giornata: il taglio per giornata NON e' implementato qui",)),
    "la_liga": Regola(soglie=(5,), turni=(1,), passo_dopo_ultima=5,
                      azzeramenti=("fine stagione",), fonte="RFEF/LaLiga"),
    "bundesliga": Regola(soglie=(5,), turni=(1,), passo_dopo_ultima=5,
                         azzeramenti=("fine stagione",), fonte="DFL"),
    "ligue_1": Regola(soglie=(5,), turni=(1,), passo_dopo_ultima=5,
                      azzeramenti=("fine stagione",),
                      fonte="LFP, regola semplificata dal 2025-26 (prima: 3)"),
    "uefa": Regola(
        soglie=(3,), turni=(1,), passo_dopo_ultima=2,
        azzeramenti=("dopo i play-off", "dopo i quarti di finale"),
        fonte="art. 63 regolamento UEFA Champions League 2026/27"),
}


def soglia_successiva(cartellini: int, competizione: str) -> int | None:
    """A quante ammonizioni scatta la PROSSIMA squalifica, da `cartellini`.

    ``None`` se la competizione non prevede altre soglie (Premier oltre la 15ª).
    """
    r = REGOLE[competizione]
    for s in r.soglie:
        if cartellini < s:
            return s
    if not r.passo_dopo_ultima:
        return None
    ultima = r.soglie[-1]
    # quante volte il passo ci sta oltre l'ultima soglia, arrotondando in su
    passi = (cartellini - ultima) // r.passo_dopo_ultima + 1
    return ultima + passi * r.passo_dopo_ultima


def stato(cartellini: int, competizione: str) -> dict:
    """Lo stato disciplinare di un giocatore in una competizione.

    E' un **fatto** calcolato, non una stima: dipende solo dal conteggio dei
    cartellini e dal regolamento.
    """
    if competizione not in REGOLE:
        raise KeyError(f"regole non note per {competizione!r}: "
                       f"note {sorted(REGOLE)}")
    r = REGOLE[competizione]
    prossima = soglia_successiva(cartellini, competizione)
    mancanti = None if prossima is None else prossima - cartellini
    # Squalificato ORA = ha appena raggiunto una soglia.
    turni = 0
    if cartellini in r.soglie:
        turni = r.turni[r.soglie.index(cartellini)]
    elif (r.passo_dopo_ultima and cartellini > r.soglie[-1]
          and (cartellini - r.soglie[-1]) % r.passo_dopo_ultima == 0):
        turni = r.turni[-1]
    return {
        "competizione": competizione,
        "cartellini": cartellini,
        "squalificato": turni > 0,
        "turni_squalifica": turni,
        # DIFFIDATO = a UNA sola ammonizione dalla squalifica. E' la
        # definizione italiana di "diffida", ed e' quella che interessa:
        # identifica chi rischia di saltare la prossima partita.
        "diffidato": mancanti == 1,
        "ammonizioni_alla_squalifica": mancanti,
        "fonte_regola": r.fonte,
    }


def incentivo_cartellino(mancanti: int | None,
                         importanza_prossima: float,
                         importanza_successiva: float) -> dict:
    """🧠 GIUDIZIO, non misura: conviene al diffidato prendersi il giallo ora?

    ⚠️ QUESTA FUNZIONE NON MISURA UN COMPORTAMENTO, calcola un **incentivo**.
    Che il giocatore poi ci si comporti davvero e' un'ipotesi non verificata, e
    va trattata come tale (``tipo: "giudizio"``, `README` §1 della stagione).

    Il ragionamento, che e' il motivo per cui l'utente l'ha chiesta: un
    diffidato salta la partita **successiva a quella in cui prende il giallo**.
    Quindi, se la gara imminente vale poco e quella dopo vale molto, "smaltire"
    la diffida subito costa poco e libera la partita che conta; se invece e'
    imminente quella importante, conviene evitare il cartellino.

    Con `p` = importanza della prossima partita e `s` = quella della
    successiva, entrambe in [0, 1]:

        incentivo = s - p      (positivo -> conviene smaltire ora)

    E' deliberatamente banale: mettere qui un modello elaborato darebbe
    un'illusione di precisione su una quantita' (l'importanza) che nessuno ha
    misurato. Il valore sta nel **segno**, non nel numero.
    """
    if mancanti != 1:
        return {"applicabile": False,
                "motivo": "non e' diffidato: nessuna scelta da fare"}
    incentivo = importanza_successiva - importanza_prossima
    if incentivo > 0.2:
        lettura = ("conviene smaltire la diffida ORA: la partita che conta "
                   "e' quella dopo")
    elif incentivo < -0.2:
        lettura = ("conviene EVITARE il cartellino: la partita che conta e' "
                   "quella imminente")
    else:
        lettura = "nessun incentivo chiaro: le due partite pesano uguale"
    return {
        "applicabile": True,
        "incentivo": round(incentivo, 3),
        "lettura": lettura,
        "tipo": "giudizio",
        "avvertenza": ("e' un incentivo calcolato, non un comportamento "
                       "osservato: nessuno ha mai misurato se i giocatori vi "
                       "si conformino"),
    }
