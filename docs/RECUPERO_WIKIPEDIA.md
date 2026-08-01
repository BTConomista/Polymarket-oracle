# Piano di recupero dei giocatori Wikipedia falliti (01/08/2026)

> ## ⚠️ STATO: ANALISI COMPLETE, **VERIFICA NON ESEGUITA**
>
> Quattro agenti hanno analizzato i quattro fronti e prodotto stime e codice.
> **I quattro scettici e la sintesi sono falliti per limite di sessione**, quindi
> nulla di ciò che segue è stato sottoposto alla verifica avversariale.
>
> **Non è materiale su cui agire così com'è.** Il precedente pesa: nell'audit del
> database carriere lo scettico ha declassato **27 rilievi su 72**, e in quello
> sulle fonti **25 su 88**. Le stime qui sotto vanno lette come **limiti
> superiori ottimistici** finché qualcuno non le rimette in discussione.
>
> **L'unica cosa verificata in proprio dalla sessione** è il rilievo §0, perché
> costava due minuti e riguarda il nostro codice.

---

## §0 · L'unico rilievo VERIFICATO: la classificazione degli errori è sbagliata

`wikipedia_careers.py:380` decide così se una pagina ha un infobox:

```python
if "infobox" not in html:
    return Esito(..., "nessun_infobox")
```

**È un test di STRINGA, non di forma.** Le voci di *nome proprio* di Wikipedia
(«Pedro», «Danilo», «Fernando», «Marcelo», «Allan») **hanno** un
`infobox name`: passano il test, il parser non trova righe di carriera, e
finiscono etichettate `nessun_blocco` — cioè in un fronte diverso da quello a
cui appartengono.

**Misurato in proprio dalla sessione**: delle 615 pagine `nessun_blocco`
presenti in cache, **330 (53,7%) sono in realtà pagine-indice**. Gli esempi sono
esattamente i mononimi brasiliani e iberici del bias noto.

**Conseguenza pratica**: il fronte «disambigua» non è di 2.102 pagine ma di circa
**2.500**, e i conteggi per stato che abbiamo pubblicato finora **sotto-stimano
il problema e sovra-stimano la sua varietà**. Non è un errore nei dati raccolti:
è un errore nell'*etichetta* con cui li abbiamo classificati — che però decide
quale strategia di recupero si applica.

*(Regola R6: il pericolo non è il valore mancante, è quello che sembra dire una
cosa e ne dice un'altra.)*

---

## Le quattro analisi, come sono uscite (NON verificate)

| fronte | su quanti | stima recuperati | costo |
|---|---:|---:|---|
| **1 · pagine-indice** | 2.499 | **2.017** | +1 richiesta per recuperato (~34 min) |
| **2 · 404 sul nome** | 1.389 | **477** | 480 richieste in tutto |
| **3 · identità respinte + quarantena** | 351 | **254** | 137 richieste (~2,5 min) |
| **4 · pagina senza carriera** | 634 | **116** | 126 richieste (~2 min) |
| **totale** | 4.873 | **~2.864** | ~2.760 richieste, ~46 min |

⚠️ I totali non si sommano in modo pulito: i fronti si sovrappongono, perché il
rilievo §0 sposta ~360 righe dal fronte 4 al fronte 1.

---

## FRONTE 1 — le pagine di disambigua (`nessun_infobox`), più la stessa cosa mal etichettata dentro `nessun_blocco` e `errore`.
**Stima**: 2017 su 2499

**Tasso**: copertura del selettore 2.038/2.499 = 81,6% IC95 [80,0%, 83,0%]; sui soli `nessun_infobox` 1.846/2.139 = 86,3% IC95 [84,8%, 87,7%]. Recuperati unici 2.017 (alcuni player_id compaiono due volte in esiti.jsonl per il ritentativo degli `errore`). Il tasso di CONFERMA della scelta, misurato su 30 pagine scaricate: 30/30 = 100%, IC95 [88,6%, 100%] — quindi i recuperati attesi sono fra 1.788 e 2.017.

**Falsi positivi attesi**: ZERO osservati su 30 (tutti `confermata_data`, con la data al giorno; un solo caso a 1 giorno di distanza, Vladimir Ignatenko 2006-05-11 contro 2006-05-12 — dentro la tolleranza, R4: si dichiara). Limite superiore 95%: ≤0,285% dei recuperati, cioè **≤6 giocatori su 2.017**. Deriva dal prodotto di due misure indipendenti: quota di scelte col bersaglio assente ≤11,4% (regola del tre su 0/30) × quota di impostori che `verifica_identita` lascia passare 2,51% (limite superiore su 3.914 accoppiamenti stesso-paese/stesso-anno). Da confrontare con lo 0,268% già presente nella raccolta attuale: il ramo-indice NON peggiora la qualità del database.

**Costo**: **+1 richiesta per giocatore recuperato, 0 per gli astenuti.** Le pagine-indice sono già in cache (2.138/2.139 dei `nessun_infobox`), quindi il passo di selezione è **interamente offline**. Si spendono ~2.017 richieste per 2.017 recuperi — cioè +0,45 richieste per ogni giocatore fallito del fronte complessivo (2.017 su 4.477). A 1 richiesta al secondo: **circa 34 minuti** di raccolta, in un processo solo. Nessuna richiesta va sprecata sugli astenuti (461 pagine), che è il vantaggio concreto dell'astensione. Le uniche pagine-indice ancora da scaricare sono 28 (1 `nessun_infobox` + 27 `errore` senza cache).

### Strategia

## La procedura, passo per passo

**Passo 0 — riclassificare, prima di raccogliere.** Lo stato `nessun_infobox` non identifica il fronte: lo identifica solo in parte. Il test attuale è `"infobox" not in html`, che è una *stringa*, non una forma. «Danilo», «Fernando», «Roberto», «Fábio» sono voci di **nome proprio** che HANNO un `infobox name`: passano il test, il parser non trova righe di carriera, e finiscono in `nessun_blocco`. «Dante» reindirizza a Dante Alighieri, con tanto di infobox. Misurato: **336 dei 620** `nessun_blocco` in cache e **24 dei 313** `errore` sono pagine-indice esattamente come le disambigue. Quindi il fronte non è 2.102 pagine ma **2.499**. Si sostituisce il test-stringa con `e_pagina_indice(html)`, che guarda due segnali in OR: la dichiarazione di Wikipedia (`#disambigbox`, `.dmbox`, categorie «… disambiguation / given name / surname») e la forma (≥2 righe «… (born AAAA), …»). Falsi allarmi su 600 voci vere di calciatori: **0**.

**Passo 1 — estrarre i candidati dalla pagina-indice, senza aprire nulla.** Si scorrono le `<li>` dentro `div.mw-parser-output`, saltando le sezioni non-persona (*See also*, *Places*, *Other uses*, *Fictional*…), i navbox e le note. Di ogni riga si prende il **primo link a persona** e **tutto il testo della riga**. Zero richieste.

**Passo 2 — scegliere con ciò che la riga già dice.** È il punto: la riga d'indice contiene quasi sempre l'anno di nascita, spesso il mese, quasi sempre la nazionalità in forma di aggettivo, spesso il ruolo e a volte i club. `Koke (footballer, born 1992), full name Jorge Resurrección Merodio, Spanish football midfielder for Atlético Madrid and Spain` è, da sola, sufficiente. Si assegna un punteggio (anno ±5,0 · mese ±2,0/−4,0 · club +2,5 fino a 2 · nazionalità ±2,0 · ruolo +1,0/−1,5 · non-calciatore −6,0) e si prende il primo **solo se** supera soglia 5,0 **e** stacca il secondo di almeno 3,0.

**Passo 3 — astenersi, quando non si sa.** Il 13,7% delle pagine finisce qui: 223 sotto soglia, 49 ambigue, 20 senza candidati. L'astensione costa zero richieste e zero rischio, ed è una decisione, non un fallimento.

**Passo 4 — una sola richiesta, e poi il giudice.** Si scarica la pagina scelta (1 richiesta) e si applica `verifica_identita` **già esistente**, che lavora sulla data di nascita **al giorno**. Questa è la vera barriera, non il punteggio.

**Passo 5 — su questo ramo, niente quarantena.** `solo_data=True`: sul ramo-indice si accetta **solo** `confermata_data`. Motivo: sul ramo per-nome una data discorde è spesso un'anagrafica contestata fra fonti; qui invece abbiamo scelto la pagina *proprio perché* l'anno coincideva, quindi una data discorde è un sintomo, non un dubbio. Costo misurato: 1,19% (223 su 18.790 pagine risolte non sono `confermata_data`).

## Perché non serve un selettore severo

Le due barriere sono indipendenti e si moltiplicano. Il selettore, da solo, aderisce al 6,87% dei profili che **non sono** sulla pagina. `verifica_identita`, da sola, lascia passare il 2,02% degli impostori stesso-paese/stesso-anno — che è il pavimento del paradosso dei compleanni (7/365 = 1,9%), non un difetto del codice. Stringere il selettore fino a chiedere anno + (mese o club) porta il placebo a 0,10% ma **crolla la copertura al 10,2%**: si pagherebbero 76 punti di copertura per un rischio che il secondo stadio già annulla.

## Costo e ordine di esecuzione

Le pagine-indice sono **già tutte in cache** (2.138/2.139). Si spende **1 richiesta per giocatore recuperato**, zero per gli astenuti: ~2.017 richieste, ~34 minuti a 1 req/s. Solo `/wiki/<Nome>`, nessun `/w/`, `/api/`, `Special:`.

### I numeri misurati

| cosa | valore | come |
|---|---|---|
| Pagine `nessun_infobox` censite | 2.139, di cui 2.138 in cache (99,95%) | lettura di esiti.jsonl + esistenza del file `urllib.parse.quote(titolo, safe='')[:150] + '.html.gz'`. Il conteggio è più alto del brief (2.102) perché la raccolta è proseguita in background. |
| Che cosa sono davvero, classificate in cache | 1.806 disambigua di nome-persona · 123 disambigua generiche · 149 voci di nome/cognome con elenco · 54 indici senza categoria · 6 anomale. Totale: 2.132/2.138 (99,7%) sono INDICI DI PERSONE | BeautifulSoup su ogni pagina in cache: presenza di `#disambigbox`, categorie in `#mw-normal-catlinks`, incipit «may refer to», presenza di un `table.infobox`. |
| R6 — lo stesso problema sotto un'altra etichetta | 336/620 `nessun_blocco` in cache e 24/313 `errore` sono pagine-indice. Sui 178 `identita_non_confermata`: 0 | `e_pagina_indice()` applicata alle pagine in cache di quegli stati. Su un sotto-campione di 200 brasiliani `nessun_blocco`: 100 senza alcun infobox, 96 con un infobox NON calcistico (`infobox name`), 4 altro. |
| Copertura del selettore (astensione inclusa) | 1.846/2.139 = 86,3% IC95 [84,8%, 87,7%] sui `nessun_infobox`; 2.038/2.499 = 81,6% [80,0%, 83,0%] sul fronte esteso | `scegli_da_indice` con soglia 5,0 / margine 3,0 su tutte le pagine in cache. Astensioni: 223 sotto soglia, 49 ambigue, 20 senza candidati. |
| Corroborazione delle scelte | 11,8% anno + mese o club · 87,0% anno unico sulla pagina · 1,2% anno conteso da un altro calciatore | per ogni scelta si ri-punteggiano tutti gli altri candidati e si conta quanti sono calciatori con lo STESSO anno di nascita del nostro giocatore. |
| Tasso di conferma (campione di rete, 30 pagine) | 30/30 = 100%, IC95 [88,6%, 100%] — tutte `confermata_data` | campione riproducibile seed=20260801: 24 estratte a caso dalle scelte, 6 forzate dal tier 'anno conteso'. Scaricate una alla volta con `W.fetch_page` (1 req/s, cache, robots), poi `parse_career` + `bday_pagina` + `verifica_identita`. Tappe estratte: da 3 a 20 per giocatore. |
| PLACEBO (R7) — il selettore giudicato con un profilo che NON è sulla pagina | 6,87% IC95 [6,26%, 7,53%] con impostore della stessa nazionalità (6.048 accoppiamenti). Se l'impostore ha ANCHE lo stesso anno di nascita: 83,5% [82,5%, 84,5%] su 5.091 | per ogni pagina-indice si estraggono 3 impostori a caso dai 2.138 giocatori, filtrati per nazionalità (A) o nazionalità+anno (B), e si rilancia `scegli_da_indice`. Ogni accettazione è per costruzione un falso positivo. Il caso B dice che anno+nazionalità NON bastano da soli — ed è il motivo per cui  |
| Il filtro a valle — quanto lascia passare `verifica_identita` | 2,02% IC95 [1,62%, 2,51%] entrano nel DB · 4,42% [3,82%, 5,11%] finiscono in quarantena · 93,6% respinti | 3.914 impostori su pagine VERE già scaricate (esiti `ok` con bday e tappe): si passa a `verifica_identita` la data di nascita della pagina e l'anagrafica + i club di un giocatore diverso con stesso paese e stesso anno. Il 2,02% coincide col pavimento del paradosso dei compleanni (7/365 = 1,9%): è ir |
| Costo della regola `solo_data=True` (niente quarantena su questo ramo) | 1,19% — 223 su 18.790 pagine già risolte non sono `confermata_data` (210 quarantena, 13 confermata_club) | distribuzione del campo `identita` fra gli esiti `ok` di esiti.jsonl. Nel campione di 30 il costo è stato 0. |
| Curva di scambio copertura/rischio | (soglia 3, margine 2) 88,6% / 8,35% · (5,3) 86,1% / 6,87% · (7,5) 77,7% / 3,63% · anno+(mese|club) obbligatori 10,2% / 0,10% | griglia rilanciata sulle 2.138 pagine, con il placebo A ricalcolato a ogni punto. Il punto (5,3) è quello oltre il quale si perde copertura senza guadagnare sicurezza. |
| Due bug del parser, entrambi silenziosi (R6 applicato al codice) | href protocollo-relativi in cache → 0 candidati · `find_parent(class_=regex 'toc')` risale fino a `<html>` (`vector-toc-available`) → 0 candidati | trovati eseguendo l'estrattore sulla cache. Nessuno dei due solleva un'eccezione: restituiscono una lista vuota, che sembra un risultato legittimo. Entrambi documentati nel codice proposto. |

### Rischi dichiarati

- **Il campione di rete è 30, e si vede.** 30/30 dà un IC95 che scende a 88,6%: il tasso di recupero vero potrebbe essere l'88% invece del 100%, e il numero di recuperati fra 1.788 e 2.017. Non è un numero chiuso: è un numero che la raccolta vera chiuderà. Va rimisurato sui primi 300 recuperi effettivi prima di dichiarare il fronte concluso.
- **Il limite superiore sui falsi positivi (0,285%) è un limite, non una stima.** È il prodotto di due limiti superiori (bersaglio assente ≤11,4% da 0/30 · leak di `verifica_identita` ≤2,51%). La stima puntuale è molto più bassa, ma con 0 eventi osservati non si può dire quanto. Se il tasso vero di bersaglio-assente fosse il 3%, i falsi positivi sarebbero ~1,5 giocatori su 2.017.
- **Il placebo adversariale è alto e va detto: 83,5%.** Se due giocatori condividono nazionalità e anno di nascita e solo uno è sull'indice, il selettore aggancia l'altro senza esitare. Non diventa un errore nel database solo perché `verifica_identita` sta a valle. Chi in futuro riusasse `scegli_da_indice` **senza** il secondo stadio introdurrebbe errori a due cifre percentuali. Il codice lo dichiara nel docstring di `risolvi_da_indice`.
- **La quarantena è una via d'ingresso, e su questo ramo va chiusa.** Il 4,42% degli impostori finisce in `quarantena` — che nella raccolta attuale viene comunque salvata (199 righe dentro gli `ok`). Con `solo_data=True` questa via è chiusa a costo dell'1,19%. Se un domani qualcuno passasse `solo_data=False` per «recuperare di più», riaprirebbe il canale peggiore.
- **Il ruolo come feature è fragile.** `position` nel nostro dataset è la posizione ATTUALE/prevalente; la riga d'indice descrive spesso il ruolo di inizio carriera. Pesa +1,0/−1,5, quindi non ribalta una decisione da solo, ma su un giocatore riconvertito (terzino diventato centrocampista) può togliere 2,5 punti al candidato giusto. È una delle cause plausibili delle 223 astensioni sotto soglia.
- **I demonimi sono una mappa a mano, e le mappe a mano invecchiano.** Copre i paesi con ≥100 giocatori; una nazione assente non rompe nulla (il candidato semplicemente non prende il +2,0) ma abbassa la copertura in silenzio. Nota già trovata: `Turkey` e `Türkiye` convivono nel dataset come due paesi distinti — entrambe mappate, ma è il tipo di cosa che si ripresenterà.
- **L'anno di nascita del nostro dataset è assunto giusto.** Tutto il selettore ci si appoggia. Se `date_of_birth` di player-scores è sbagliato per un giocatore, il selettore sceglierà con sicurezza la persona sbagliata — e poi `verifica_identita` la respingerà, quindi il danno è una richiesta sprecata, non un dato falso. È il comportamento voluto, ma va detto che il fronte NON recupererà mai chi ha l'anagrafica sbagliata da noi.
- **`indice_non_risolto` è uno stato nuovo.** Va aggiunto all'elenco degli stati in `data/carriere_wikipedia/README.md` e NON va messo fra gli esiti definitivi che non si ritentano: un indice non risolto oggi può diventare risolvibile domani, se la pagina Wikipedia si arricchisce o se il selettore migliora.

<details><summary>Codice proposto (non applicato)</summary>

```python
# ===========================================================================
# FRONTE 1 — RISOLUZIONE DALLE PAGINE-INDICE (disambigua e voci di nome)
# Da incastrare in src/data/wikipedia_careers.py, dopo `verifica_identita`.
# Usa quello che il modulo ha gia': re, urllib.parse, dataclass/field,
# BeautifulSoup, Esito, Tappa, fetch_page, parse_career, bday_pagina,
# verifica_identita. Nessuna dipendenza nuova.
# ===========================================================================

# Namespace da ignorare fra i link di una riga d'indice.
NS_ESCLUSI = ("Category:", "Help:", "Wikipedia:", "File:", "Template:",
              "Portal:", "Special:", "Talk:", "Module:", "MOS:", "WP:")
# Sezioni di una pagina-indice che non contengono persone.
SEZ_ESCLUSE = ("see also", "references", "external links", "places",
               "other uses", "fictional", "ships", "further reading",
               "in fiction", "music", "films")

# Nazione del nostro dataset -> aggettivi come compaiono nelle righe d'indice
# («Brazilian football forward»). Copre i paesi con >=100 giocatori nella
# popolazione; una nazione assente non rompe nulla, semplicemente non porta il
# suo +2,0 (il selettore degrada, non sbaglia).
DEMONIMI: dict[str, tuple[str, ...]] = {
    "Brazil": ("brazilian",), "Spain": ("spanish",), "Portugal": ("portuguese",),
    "England": ("english",), "Scotland": ("scottish",), "Wales": ("welsh",),
    "Ireland": ("irish",), "France": ("french",), "Italy": ("italian",),
    "Germany": ("german",), "Netherlands": ("dutch",),
    "Argentina": ("argentine", "argentinian"), "Russia": ("russian",),
    "Denmark": ("danish",), "Sweden": ("swedish",), "Norway": ("norwegian",),
    "Belgium": ("belgian",), "Poland": ("polish",), "Croatia": ("croatian",),
    "Serbia": ("serbian",), "Turkey": ("turkish",), "Türkiye": ("turkish",),
    "Greece": ("greek",), "Austria": ("austrian",), "Switzerland": ("swiss",),
    "Ukraine": ("ukrainian",), "Colombia": ("colombian",),
    "Uruguay": ("uruguayan",), "Mexico": ("mexican",), "Chile": ("chilean",),
    "Japan": ("japanese",), "United States": ("american",),
    "Nigeria": ("nigerian",), "Ghana": ("ghanaian",), "Senegal": ("senegalese",),
    "Cote d'Ivoire": ("ivorian",), "Cameroon": ("cameroonian",),
    "Morocco": ("moroccan",), "Algeria": ("algerian",), "Tunisia": ("tunisian",),
    "Czech Republic": ("czech",), "Slovakia": ("slovak",),
    "Hungary": ("hungarian",), "Romania": ("romanian",),
    "Finland": ("finnish",), "Iceland": ("icelandic",), "Israel": ("israeli",),
    "Australia": ("australian",), "Canada": ("canadian",),
    "Bosnia-Herzegovina": ("bosnian",), "Albania": ("albanian",),
    "North Macedonia": ("macedonian",), "Montenegro": ("montenegrin",),
    "Slovenia": ("slovenian",), "Bulgaria": ("bulgarian",),
    "Georgia": ("georgian",), "Congo": ("congolese",), "Mali": ("malian",),
    "Guinea": ("guinean",), "Angola": ("angolan",), "Gabon": ("gabonese",),
    "South Africa": ("south african",), "Jamaica": ("jamaican",),
    "Costa Rica": ("costa rican",), "China": ("chinese",), "Iran": ("iranian",),
    "Estonia": ("estonian",), "Latvia": ("latvian",),
    "Lithuania": ("lithuanian",), "Belarus": ("belarusian",),
    "Cyprus": ("cypriot",), "Peru": ("peruvian",), "Ecuador": ("ecuadorian",),
    "Venezuela": ("venezuelan",), "Paraguay": ("paraguayan",),
}
_TUTTI_DEMONIMI = {x for v in DEMONIMI.values() for x in v}

RUOLI: dict[str, tuple[str, ...]] = {
    "Goalkeeper": ("goalkeeper", "keeper"),
    "Defender": ("defender", "back", "defence"),
    "Midfield": ("midfielder", "midfield"),
    "Attack": ("forward", "striker", "winger", "attacker"),
}

_MESI = {m: i + 1 for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"))}

_RE_NATO = re.compile(r"born\s+(?:\d{1,2}\s+)?([A-Za-z]+)?\s*(?:\d{1,2},?\s*)?(\d{4})")
_RE_CALCIO = re.compile(r"footballer|football|soccer", re.I)
_RE_HREF = re.compile(
    r"^(?:https?:)?//[a-z-]+\.wikipedia\.org/wiki/(.+)$|^/wiki/(.+)$", re.I)

# Soglie del selettore. Punto operativo scelto il 01/08/2026: copertura 86,3%
# delle pagine-indice (1.846/2.139), con il 6,9% di adesioni a un profilo che
# NON e' sulla pagina (placebo). La griglia misurata:
#   (soglia, margine)  copertura   placebo
#      (3, 2)            88,6%      8,35%
#      (5, 3)  <-- qui   86,1%      6,87%
#      (7, 5)            77,7%      3,63%
#      anno + (mese|club) obbligatori: 10,2% di copertura, 0,10% di placebo
# Stringere costa 8 punti di copertura per 3 di placebo, e non serve: la vera
# difesa e' `verifica_identita` a valle, che lavora sulla data AL GIORNO e
# taglia il 98% degli agganci sbagliati (vedi `risolvi_da_indice`).
SOGLIA = 5.0
MARGINE = 3.0

_STOP_CLUB = {"fc", "cf", "sc", "ac", "as", "cd", "ud", "sv", "afc", "club",
              "de", "of", "the", "city", "united", "real", "athletic",
              "atletico", "sporting", "racing", "deportivo", "ii", "b", "and"}


@dataclass
class Candidato:
    """Una riga di una pagina-indice: un link a persona + il testo che la
    descrive. Il testo e' oro: contiene gia' anno di nascita, nazionalita',
    ruolo e spesso i club — cioe' tutto cio' che serve a scegliere **senza
    aprire il link**, che e' l'unica cosa che costa una richiesta."""
    titolo: str
    testo: str
    sezione: str = ""
    punteggio: float = 0.0
    dettaglio: dict = field(default_factory=dict)


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _titolo_da_href(href: str) -> str | None:
    """`/wiki/X`, `//en.wikipedia.org/wiki/X`, `https://en.wikipedia.org/wiki/X`.

    ⚠️ Le pagine **in cache** hanno gli href in forma protocollo-relativa
    (`//en.wikipedia.org/wiki/...`), non `/wiki/...`. Un parser che accetta solo
    la seconda forma es
```

</details>

## Fronte 2 — i giocatori con 404 sul nome (`stato = nessuna_pagina`). Alla fotografia del 01/08/2026 ore 10:38 sono **1.389** (non 1.354: la raccolta in background è andata avanti mentre lavoravo), di cui **199 della nostra popolazione**. Per definizione nessuno ha la pagina in cache. La scoperta centrale è che il fronte **non si risolve indovinando le varianti del nome, ma leggendo i titoli veri che sono già dentro la cache**: le 20.924 pagine scaricate contengono, nei loro wikilink, **218.026 titoli reali di en.wikipedia**, e lì dentro c'è il titolo giusto di 477 dei 1.389 falliti. Costo di questa scoperta: **zero richieste**.
**Stima**: 477 su 1389

**Tasso**: 34,3% del fronte (477/1.389). Con l'incertezza sul tasso di successo del candidato misurato su campione (18/18, Wilson 95% [82,4%, 100%]) la stima scende a un intervallo di [393, 477] giocatori, cioè [28,3%, 34,3%]. Sui NOSTRI: 99 dei 199. Il residuo (912) non è recuperabile con le varianti: un 404 vero sul nome nudo significa quasi sempre che la voce inglese NON esiste, e questo è misurato, non supposto.

**Falsi positivi attesi**: Punto: 0. Due misure indipendenti. (1) Campione reale: 0 agganci sbagliati su 20 pagine scaricate (18 candidati + 2 sospetti costruiti apposta), Wilson 95% superiore 16,1% — potenza bassa, lo dichiaro. (2) PLACEBO a costo zero su n grande: ho ri-eseguito il matcher sui 18.245 giocatori 'ok' dopo aver TOLTO dal gazetteer il loro titolo vero, così ogni candidato prodotto è per costruzione un'altra pagina. Ne ha prodotti 2.134 (11,7% dei giocatori); 107 erano verificabili gratis perché già in cache; il giudice-data ne ha respinti **107 su 107** (l'unico 'passato', Burak Yilmaz → Burak Yılmaz, è la STESSA persona sotto l'alias accentato, quindi non è un errore). Wilson 95% superiore **3,47%** → attesi **≤ 13 agganci sbagliati sui 477**, punto 0. Sul solo strato rischioso (chiave-cognome): 0/98 respinti, superiore 3,77%.

**Costo**: **0,022 richieste in più per giocatore tentato** (480 richieste su 22.254), cioè **0,35 per giocatore fallito** — contro le **5,0** di un piano a cinque varianti cieche (5 × 1.354 = 6.770 richieste). Il fattore 14 di risparmio non viene da varianti migliori: viene dal fatto che il grosso del lavoro (218.026 titoli veri) si fa **a zero richieste** dentro la cache, e la rete serve solo per la conferma.

Dettaglio: costruzione del gazetteer 0 richieste (~35 s di CPU su 20.924 file). Recupero: 477 candidati, di cui 7 già in cache → 470 pagine da scaricare; il primo candidato è bastato 18 volte su 18, quindi il tetto di 2 candidati per giocatore si attiva raramente → **≈480 richieste, 8 minuti a 1 richiesta/secondo**. Secondo giro dopo la fine della raccolta: di nuovo 0 richieste per rigenerare il gazetteer, più le poche conferme dei nuovi candidati.

Costo già speso da me: **31 richieste** (1 ogni 3 secondi, sequenziali, con la raccolta in background già a 1/s), tutte su `/wiki/<Titolo>`, nessuna su `/w/`, `/api/` o `/wiki/Special:`. Le 31 pagine sono finite nella cache e sono quindi già pagate per la raccolta vera.

Costo che consiglio di NON spendere: 912 × 1 richiesta = 912 per `(footballer, born AAAA)` (resa misurata 0/6) e altre ~900 per le regole per-famiglia (resa 2/5, IC [11,8%, 76,9%] — troppo largo per impegnare 900 richieste).

### Strategia

PASSO 0 — COSTRUIRE IL GAZETTEER (0 richieste, ~35 s di CPU). Scorrere `data/wikipedia_cache/en/*.html.gz` ed estrarre da ogni pagina i wikilink `rel="mw:WikiLink" href="https://en.wikipedia.org/wiki/TITOLO"`. Le pagine sono in HTML Parsoid: i link del corpo sono ASSOLUTI, non `/wiki/…` relativi — un parser che cerca `href="/wiki/` trova 5 link per pagina invece di 450 (ci sono cascato al primo tentativo). Scartare i link con `class="new"` (link ROSSI: la pagina non esiste — generarli sarebbe fabbricare 404 garantiti, regola R6) e i namespace (`Category:`, `Template:`). Tenere i titoli di 2-4 parole. Risultato misurato: **218.026 titoli reali**.

PASSO 1 — INDICIZZARE CON QUATTRO CHIAVI, dalla più stretta alla più larga. Ogni chiave è una FAMIGLIA di fallimento, non una variante generica:
  A · grafia (solo diacritici e punteggiatura ripiegati) → Bosko Sutalo = Boško Šutalo, Frederik Sörensen = Frederik Sørensen, Albert Grønbaek = Grønbæk. **221 giocatori.**
  B · traslitterazione (A + collassi g/h, j/i/y, w/v, z/s, ck/k, doppie, ie/ei) → Artem Gromov = Artem Hromov, Ilya Zabarnyi = Illia Zabarnyi, Sergey Pesjakov = Sergei Pesyakov. **+126.**
  C · ordine (token ordinati) → Ja-cheol Koo = Koo Ja-cheol, In-beom Hwang = Hwang In-beom. **+28** (praticamente tutta la Corea).
  D · solo cognome, con FILTRO sul nome di battesimo (prefisso comune ≥3 lettere oppure lista chiusa di ipocoristici greci) → Vasilios Torosidis = Vasilis Torosidis, Konstantinos Giannoulis = Kostas Giannoulis, Javi Eraso = Javier Eraso, Álex Pozo = Alejandro Pozo. **+102.** D si usa SOLO se A, B, C sono vuote.

PASSO 2 — SCARICARE, AL MASSIMO 2 CANDIDATI PER GIOCATORE, uno alla volta, 1 richiesta/secondo. 477 giocatori, 7 dei quali hanno il candidato già in cache. Sul campione il PRIMO candidato è bastato 18 volte su 18 → **≈ 480 richieste in tutto, 8 minuti**.

PASSO 3 — GIUDICARE CON UNA REGOLA PIÙ SEVERA DEL SOLITO. Sul percorso-variante accettare **solo `confermata_data`**, mai `confermata_club`: il nome l'abbiamo cambiato noi, quindi non è più una prova d'identità, e l'unica prova indipendente che resta è la data di nascita — che esiste per il **100%** dei 1.389. Non costa niente: sul campione tutte e 18 le conferme sono passate per la data, zero per i club.

PASSO 4 — REGISTRARE LO STRATO (A/B/C/D) nell'esito, in `dettaglio`. Senza, il tasso di errore resta un numero unico che non dice niente; con, si rimisura per famiglia (regola R7).

PASSO 5 — RIPETERE ALLA FINE DELLA RACCOLTA (volano). Il gazetteer cresce di ~4 titoli nuovi per pagina scaricata: i ~6.700 giocatori ancora da fare e i 477 recuperati aggiungeranno titoli, e un secondo giro sui 912 residui costa di nuovo zero richieste.

COSA **NON** FARE, e questo è il risultato negativo più utile del lavoro: **non provare `Nome (footballer, born AAAA)`**. Sembra la variante ovvia (è il disambiguante standard di Wikipedia, e la data di nascita ce l'abbiamo per tutti) ed è **0 su 6** nel campione. Il motivo è strutturale e va scritto come identità, non come impressione: il titolo disambiguato esiste solo quando il titolo nudo è occupato — e in quel caso il nome nudo NON restituisce 404, restituisce la pagina di disambigua (fronte 1, `nessun_infobox`). Un 404 vero sul nome nudo dice che quel nome su en.wikipedia **non esiste in nessuna forma**. Applicarla ai 912 residui costerebbe 912 richieste per una resa attesa fra 0% e 39%, quasi tutta sul bordo inferiore.

### I numeri misurati

| cosa | valore | come |
|---|---|---|
| Fronte 2 alla fotografia del 01/08/2026 10:38 | 1.389 (di cui 199 nostri) | conteggio su copia read-only di esiti.jsonl, deduplicata per player_id; 22.499 giocatori distinti tentati. Il brief diceva 1.354: la raccolta in background è avanzata. |
| Titoli reali di en.wikipedia estratti dalla cache | 218.026 (da 20.924 pagine) | regex sui wikilink Parsoid `rel="mw:WikiLink" href="https://en.wikipedia.org/wiki/…"`, esclusi i link rossi (class="new") e i namespace. 0 richieste, 35 s. |
| Copertura cumulativa delle 4 chiavi | A 221 → +B 126 → +C 28 → +D 102 = 477 (34,3%) | matching delle chiavi dei 1.389 nomi contro l'indice del gazetteer; D applicata solo dove A/B/C sono vuote e filtrata sul nome di battesimo. |
| Campione reale — percorso GRATUITO (candidato dal gazetteer) | 18/18 confermati dalla data di nascita | 31 richieste vere, una alla volta, 3 s di pausa (la raccolta in background era già a 1/s). Strati A 5/5, B 5/5, C 3/3, D 5/5. Wilson 95% [82,4%, 100%]. |
| Campione reale — percorso A PAGAMENTO (varianti indovinate) | 2/11 | `(footballer, born AAAA)` 0/6 [0%, 39%]; regola ucraina g→h 1/2; forma corta greca 1/3. Estrazione casuale con seed 20260801 dentro ogni strato, nessun cherry-picking. |
| Falsi positivi nel campione reale | 0/20 (superiore 95% 16,1%) | 18 candidati + 2 sospetti costruiti apposta (Charly Musonda Jr.→Chavo Guerrero Jr., un wrestler; Yannik Wagner→Yana Vagner, una scrittrice). Entrambi respinti: il primo bday 1970 vs 1996 e nessun blocco carriera, il secondo è una disambigua. |
| PLACEBO a costo zero — quanto spesso il matcher inventa un candidato | 2.134 candidati sbagliati su 18.245 (11,7%) | ri-eseguito il matcher sui giocatori 'ok' con il loro titolo vero RIMOSSO dal gazetteer: ogni candidato prodotto è per costruzione un'altra pagina. |
| PLACEBO — quanti di quei candidati sbagliati PASSANO il giudice | 0 su 107 verificabili (superiore 95% 3,47%) | 107 dei 2.134 avevano la pagina già in cache → verifica gratis. L'unico che passava è Burak Yilmaz → Burak Yılmaz: stessa persona sotto l'alias accentato, non un errore. Sullo strato D da solo: 0/98, superiore 3,77%. |
| Falsi positivi attesi sui 477 recuperati | 0 (punto) — ≤ 13 (superiore 95%) | 477 × 3,47% = 12,6. È il numero che rende la strategia 'finita' secondo il criterio del brief. |
| Riduzione della CONFONDENTE di nazionalità | chi-quadro 1.439 → 1.029 (p resta < 1e-180) | tasso di 404 per cittadinanza prima e dopo il recupero, paesi con ≥100 giocatori. Croazia 15,5%→4,8%, Serbia 10,4%→2,7%, Cechia 8,5%→0,6%, Danimarca 10,0%→6,1%, Ucraina 29,5%→21,2%. Il bias si RIDUCE ma NON sparisce. |
| `first_name`/`last_name` di players.csv.gz — aiutano? | NO: `first_name + ' ' + last_name == name` nel 100,0% dei 1.389 | confronto diretto. Sono uno split di `name`, informazione zero. L'unico uso residuo: `first_name` NaN marca il nome d'arte brasiliano (mononimo). |
| Colonna `url` (Transfermarkt) — aiuta? | NO: `player_code == slug(name)` nel 98,3% | l'1,7% di scarto è solo punteggiatura (N'Dri→ndri, ‘Duncan’→lsquo-duncan-rsquo). Nessuna informazione nuova sul titolo Wikipedia, e Transfermarkt ha un robots.txt diverso che non stiamo autorizzati a interrogare. |
| Composizione del fronte per famiglia linguistica | Ucraina 284 · Grecia 97 · Russia 84 · Danimarca 74 · Brasile 73 · Spagna 57 · Croazia+Bosnia+Serbia+Slovenia 120 · Turchia 68 · Corea 28 | incrocio con players.csv.gz. Profilo COMPLETAMENTE DIVERSO dal fronte 1 (disambigue): lì il problema sono i mononimi brasiliani/iberici, qui è la TRASLITTERAZIONE (Ucraina 29,5% di tasso, Bosnia 22,7%, Croazia 15,5%). |
| Crescita del gazetteer | ≈4 titoli nuovi per pagina scaricata (1.000 file → 46k titoli; 21.283 → 242k) | curva misurata su permutazione casuale dei file. Il gazetteer si arricchisce da solo mentre la raccolta procede → il passo 5 (secondo giro) è gratis e non a rendimento nullo. |

### Rischi dichiarati

- **Il rischio non è distribuito uniformemente: sta quasi tutto nella chiave D (cognome).** Le chiavi A/B/C cambiano solo la grafia dello STESSO stringa-nome; D cambia il nome di battesimo e può agganciare un'altra persona. Nel placebo D ha prodotto 748 candidati sbagliati su 2.134. Mitigazione misurata: filtro sul nome di battesimo (prefisso ≥3 o ipocoristico), D usata solo se A/B/C sono vuote, e giudizio con la sola data di nascita → 0/98 passati. Se un domani si volesse allargare D, quel 3,77% di soglia superiore va rimisurato, non ereditato.
- **I due falsi positivi veri che ho trovato venivano dallo stesso bug: 'Jr.' usato come cognome.** «Charly Musonda Jr.» → «Chavo Guerrero Jr.» (un wrestler, bday 1970 contro 1996) e «Aleksey Eremenko Jr.» → «Alejandro Alvarado Jr.». Il filtro `_ONORIFICI` li elimina a costo zero. È R6 puro: due nomi che condividono un suffisso onorifico non condividono niente.
- **Il placebo ha potenza limitata dove conta di più.** Ha generato 2.134 candidati sbagliati ma solo 107 erano verificabili gratis (quelli con la pagina già in cache); gli altri 2.027 no, perché sono pagine di non-calciatori che non abbiamo. Quindi il 3,47% di soglia superiore vale sul sottoinsieme verificabile, che potrebbe non essere rappresentativo: le pagine in cache sono tutte di calciatori, e proprio l'omonimo-calciatore è il caso più insidioso. Lo dichiaro invece di nasconderlo: per stringere l'intervallo servirebbe scaricare un campione dei candidati-placebo, cioè spendere richieste per misurare il rischio anziché per raccogliere dati. È una scelta che lascio al titolare.
- **Il bias di nazionalità si riduce ma NON si chiude.** chi-quadro 1.439 → 1.029, p ancora < 1e-180. L'Ucraina resta al 21,2% di 404 contro lo 0,7% dell'Olanda. La confondente sopravvive al recupero, e ogni analisi che usi lo strato 2 deve continuare a dichiararlo. Chiudere quel divario richiederebbe una fonte diversa (Wikipedia ucraina), non varianti sull'inglese.
- **Il residuo di 912 non è 'da recuperare più avanti': è quasi tutto irrecuperabile per costruzione.** Un 404 sul nome nudo significa che il titolo non esiste; se esistesse un disambiguante, il nome nudo darebbe una pagina di disambigua e il giocatore starebbe nel fronte 1. La misura (0/6 su `(footballer, born AAAA)`) e l'argomento strutturale puntano nella stessa direzione. Il rischio qui è opposto a quello degli omonimi: **spendere 1.800 richieste per convincersi di un fatto già noto**.
- **`nessun_infobox` interrompe la scala dei suffissi.** In `scripts/fetch_wikipedia_careers.py` il ciclo fa `if e.stato != "nessuna_pagina": break`: se il nome nudo restituisce una pagina di DISAMBIGUA, i suffissi `(footballer)` e `(soccer)` non vengono mai provati. È un'osservazione sul fronte 1, non sul mio, ma la registro perché spiega perché quel fronte è il più grosso e perché i due fronti non vanno trattati con la stessa scala di varianti.
- **Anomalia dichiarata, non è un errore (R4): `players.csv.gz` contiene la stessa nazione sotto DUE etichette** — «Turkey» (426 giocatori, 9,2% di 404) e «Türkiye» (360, 8,1%). Le statistiche per paese si spezzano in due e la copertura del recupero ne risente in modo artificiale (Turkey 28%, Türkiye 3%). Non l'ho corretto (R3: nessuna modifica a mano), ma chiunque aggreghi per cittadinanza deve saperlo.
- **Il gazetteer è un dato derivato, non una fonte.** Vive nella cache, che non è versionata e non sopravvive al container. Va ricostruito a ogni sessione (35 s) e non va mai trattato come verità: dice che un titolo ESISTE, non che sia la persona giusta. Il giudice resta `verifica_identita`, e sul percorso-variante nella sua forma più severa.

<details><summary>Codice proposto (non applicato)</summary>

```python
"""PROPOSTA (non applicata) — da aggiungere a src/data/wikipedia_careers.py.

RECUPERO DEI 404: non si INDOVINA il titolo, lo si LEGGE.

Le 20.924 pagine gia' in `data/wikipedia_cache/` contengono, nei loro
wikilink, 218.026 titoli REALI di en.wikipedia. Il titolo giusto di un
giocatore che ha fallito per grafia sta quasi sempre li' dentro, perche' la
sua pagina e' linkata da quella di un compagno o di un avversario che
abbiamo gia' scaricato. Costo: ZERO richieste.
Misurato il 01/08/2026: 477 dei 1.389 falliti ottengono un candidato, e su
un campione di 18 il candidato era giusto 18 volte su 18.
"""

from __future__ import annotations

import collections
import glob
import gzip
import os
import re
import unicodedata
import urllib.parse

# `class="new"` marca un link ROSSO: la pagina NON esiste. Tenerlo
# significherebbe generare candidati garantiti 404 (regola R6: finto pieno).
_RE_WIKILINK = re.compile(
    rb'rel="mw:WikiLink" href="https://en\.wikipedia\.org/wiki/([^"?#]+)"([^>]{0,200})'
)

# Suffissi onorifici: NON sono cognomi. Usarli come chiave ha prodotto due
# falsi positivi veri e misurati — «Charly Musonda Jr.» -> «Chavo Guerrero Jr.»
# (un wrestler) e «Aleksey Eremenko Jr.» -> «Alejandro Alvarado Jr.».
_ONORIFICI = frozenset({"jr", "sr", "ii", "iii", "jnr", "snr"})

# Ipocoristici greci che la regola del prefisso non puo' vedere (Konstantinos
# e Kostas condividono solo 2 lettere). Lista chiusa e dichiarata.
_IPOCORISTICI = {
    "konstantinos": {"kostas"}, "georgios": {"giorgos", "yorgos"},
    "athanasios": {"thanasis", "sakis"}, "ioannis": {"giannis", "yiannis"},
    "emmanouil": {"manolis"}, "charalampos": {"babis", "charis"},
    "anastasios": {"tasos"}, "dimosthenis": {"dimos"},
    "eleftherios": {"lefteris"}, "panagiotis": {"panos"},
    "vasilios": {"vasilis"}, "nikolaos": {"nikos"},
    "dimitrios": {"dimitris"}, "stylianos": {"stelios"},
    "efstathios": {"stathis"}, "theodoros": {"thodoris"},
    "alexandros": {"alexis"}, "evangelos": {"vangelis"},
    "efthymios": {"efthymis"},
}


def _piatto(s: str) -> str:
    """Toglie i diacritici e le lettere non ASCII delle lingue europee."""
    s = "".join(c for c in unicodedata.normalize("NFD", str(s))
                if unicodedata.category(c) != "Mn")
    for a, b in (("ø", "o"), ("Ø", "O"), ("æ", "ae"), ("Æ", "Ae"), ("ð", "d"),
                 ("Ð", "D"), ("ł", "l"), ("Ł", "L"), ("đ", "d"), ("Đ", "D"),
                 ("þ", "th"), ("Þ", "Th"), ("ı", "i"), ("İ", "I"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def _token(s: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]", " ", _piatto(s).lower()).split()


def _collassa(t: str) -> str:
    """Collassa le differenze di TRASLITTERAZIONE, non quelle di persona.

    Ogni sostituzione ha un caso misurato dietro:
      g/h   Gromov -> Hromov, Bogdanov -> Bohdanov  (ucraino: г si translittera
            h nello schema ufficiale, g in quello che usa Transfermarkt);
      j/i/y Pesjakov -> Pesyakov, Ilya -> Illia     (russo/ucraino);
      w/v   Wagner/Vagner;  z/s  Adzic/Adžić;  ck/k;
      doppie: Ilya -> Illia;  ie/ei -> e: Matvienko -> Matviyenko.
    """
    t = t.replace("kh", "h").replace("ch", "h")
    t = (t.replace("g", "h").replace("j", "i").replace("y", "i")
          .replace("ck", "k").replace("w", "v").replace("z", "s"))
    t = re.sub(r"(.)\1+", r"\1", t)
    return t.replace("ie", "e").replace("ei", "e")


def chiavi(nome: str) -> tuple[str, str, str, str]:
    """Le quattro chiavi, dalla piu' stretta alla piu' larga.

    A  grafia   — solo diacritici/punteggiatura  (Bosko Sutalo = Boško Šutalo)
    B  translit — + i collassi di `_collassa`    (Artem Gromov = Artem Hromov)
    C  ordine   — token ordinati                 (Ja-cheol Koo = Koo Ja-cheol)
    D  cognome  — solo l'ultimo token utile      (Nikolaos/Nikos Korovesis)
    """
    tok = _token(nome)
    if not tok:
        return "", "", "", ""
    utili = [t for t in tok if t not in _ONORIFICI] or tok
    piatto = "".join(tok)
    return (piatto,
            _collassa(piatto),
            "|".join(sorted(_collassa(t) for t in utili)),
            _collassa(utili[-1]))


def costruisci_gazetteer(cache_dir=None) -> dict[str, list[str]]:
    """I titoli REALI di en.wikipedia linkati dalle pagine gia' in cache.

    Zero richieste. Cresce da solo: ogni pagina scaricata dalla raccolta
    normale ne aggiunge (~4 titoli nuovi per pagina, misurato).
    """
    cache_dir = str(cache_dir or (CACHE_DIR / "en"))
    titoli: set[str] = set()
    for p in glob.glob(os.path.join(cache_dir, "*.html.gz")):
        try:
            raw = gzip.decompress(open(p, "rb").read())
        except Exception:
            continue
        for m in _RE_WIKILINK.finditer(raw):
            if b'class="new"' in m.group(2):
                continue                       # link rosso: non esiste
            t = urllib.parse.unquote(
                m.group(1).decode("utf-8", "replace")).replace("_", " ")
            if ":" in t:                       # Category:, Template:, ...
                continue
            if 1 < len(t.split()) <= 4:        # forma da nome di persona
                titoli.add(t)
    idx: dict[str, list[str]] = collections.defaultdict(list)
    for t in titoli:
        a, b, c, d = chiavi(t)
        for k in (f"A{a}", f"B{b}", f"C{c}", f"D{d}"):
            idx[k].append(t)
    return dict(idx)


def _prefisso(a: str, b: str) -> int:
    a, b = _piatto(a).lower(), _piatto(b).lower()
    k = 0
    for x, y in zip(a, b):
        if x != y:
            break
        k += 1
    return k


def _nome_compatibile(a: str, b: str) -> bool:
    """Per la chiave D: il nome di battesimo dev'essere la stessa persona.

    Senza questo filtro la chiave-cognome aggancia «Adu Ares» -> «Austin
    Aries» e «Dong-jun Lee» -> «Derrek Lee». Con il filtro, i due nomi devono
    condividere almeno 3 lettere iniziali (Javi/Javier, Alex/Alejandro,
    Nikolaos/Nikos) oppure stare nella lista chiusa degli ipoco
```

</details>

## Fronte 3 — le 152 respinte (`identita_non_confermata`) e le 199 in quarantena dello strato 2 Wikipedia. ⚠️ La raccolta gira in background: mentre lavoravo i due gruppi sono passati a 170 e 211. Tutte le misure sono fatte sui numeri correnti (170/211) e RIPORTATE COME TASSI; le cifre assolute qui sotto sono riscalate ai 351 del brief.
**Stima**: 254 su 351

**Tasso**: 72,3% — IC95% [60%, 84%] (212-294 righe). Scomposto: QUARANTENA 181/199 = 91,0% [86,4%, 94,2%] (Wilson su n=211 misurati); RESPINTE 73/152 = 47,8% [26%, 70%] (somma di tre rami con IC propagati; il ramo dominante e' misurato su n=20, quindi l'intervallo e' largo e va dichiarato tale).

**Falsi positivi attesi**: 0,3 righe su 254 — IC95% [0,05, 1,6]. Viene dal tasso di falsi positivi MISURATO della regola proposta contro il placebo piu' duro costruibile (avversario che condivide un club col nostro giocatore, n=922): 0,11% [0,02%, 0,61%]. Controllo diretto e indipendente: sulle 16 pagine nuove trovate dal titolo-con-anno, 13 sono state attaccate e ZERO erano di un'altra persona — le 3 sbagliate (Burak Yilmaz, Romario, Liam Henderson) sono state scartate dalla regola. ⚠️ 0/13 preso da solo ha potenza nulla (limite superiore 23% per la regola del tre): il numero che regge e' quello del placebo a n=922. In piu' la regola TOGLIE dal database 2 carriere sbagliate che oggi ci sono dentro (18 tappe: Javier Olaizola e Bruno Alves, entrambi in quarantena e oggi contati fra gli `ok`).

**Costo**: +0,006 richieste per giocatore sui 22.254 tentati — cioe' 137 richieste in tutto per l'intero fronte, ~2,5 minuti a 1 richiesta/secondo. Dettaglio: le 199 in QUARANTENA costano ZERO (tutto quello che serve — le tappe, la data della pagina, nazionalita'/ruolo/altezza — e' gia' in `data/wikipedia_cache/en/` e in `esiti.jsonl`); le 152 RESPINTE costano ~0,9 richieste a testa, cioe' 33 titoli letti dagli hatnote (che sono gratis da TROVARE, si pagano solo da PRENDERE) piu' 104 costruiti alla cieca. Nessuna richiesta e' sprecata su chi la regola risolve gia' in locale, ed e' per questo che il passo 4 (rileggere la pagina che abbiamo) viene PRIMA del passo 5 (chiederne una nuova). Se un domani si applica lo stesso codice ai 2.102 `nessun_infobox`, il conto sale a ~1 richiesta per riga ma il ritrovamento e' molto piu' alto (58,2% ha gia' il titolo esatto in cache) — e' un fronte diverso e va deciso a parte.

### Strategia

PASSO 0 — cambiare il dato che si confronta, non la soglia.
Oggi `verifica_identita()` confronta INSIEMI DI NOMI DI CLUB. Il nome del club da solo non identifica nessuno: padre e figlio giocano nello stesso club (Javier Olaizola padre a Mallorca negli anni '90, il nostro figlio a Mallorca 2025-26), e i compagni di squadra pure. Da `appearances.csv` si ricava, per `player_id` (quindi immune all'omonimia), la terna `(club, primo_anno, ultimo_anno)`; dall'infobox si ha `(club, anno_da, anno_a)`. Il confronto giusto e' `club COINCIDE **e** le finestre si SOVRAPPONGONO` (tolleranza ±1 anno, perche' la grana dell'infobox e' l'anno-stagione). Chiamo `k` il numero di club dello strato 1 confermati anche negli anni. Serve anche un normalizzatore di nomi club che tolga i diacritici e le sigle societarie: il matcher attuale e' un `in` fra stringhe minuscole e fallisce in silenzio (Svyatoslav Georgievski ha 4 club su 4 coincidenti e oggi e' RESPINTO).

PASSO 1 — leggere la FORMA dello scarto anagrafico, non la sua ampiezza.
Non «quanti giorni» ma «che tipo di refuso»: Δ FORTE = entro 31 giorni, oppure stesso giorno+mese con anno diverso, oppure giorno/mese invertiti (German Lux: 1982-06-07 contro 1982-07-06). Δ DEBOLE = entro 366 giorni. Δ ESTRANEO = tutto il resto. La taratura non e' arbitraria: sulle 2.389 coppie di persone DIVERSE con lo stesso nome dentro `players.csv`, solo lo 0,96% sta entro 31 giorni e solo lo 0,25% condivide giorno+mese. Un Δ di quella forma non e' «un'altra persona»: e' un refuso fra due fonti.

PASSO 2 — il terzo voto, che costa zero richieste.
Nazionalita' (riga «place of birth» + categorie «X men's footballers»), ruolo e altezza (±3 cm) stanno gia' dentro l'HTML scaricato. NON bastano da soli — Aaron Ramsey nato 1990 corrobora 3 su 3 con il nostro nato 2003 (gallese, centrocampista, stessa statura) ed e' un'altra persona — ma come terzo voto abbattono i falsi positivi di 40 volte.

PASSO 3 — la regola (`verifica_identita_v2`, tre assi indipendenti, non una cascata).
  a) date entro 3 giorni                        -> `confermata_data`   (invariata)
  b) k == 0                                     -> `respinta`          (e' qui che cadono ENTRAMBE le 2 identita' davvero sbagliate della quarantena)
  c) Δ FORTE  e k >= 1                          -> `confermata_coerenza`
  d) Δ DEBOLE e k >= 1 e >=2 tratti concordi e 0 discordi -> `confermata_coerenza`
  e) Δ ignoto e k >= 2                          -> `confermata_coerenza`
  f) Δ ESTRANEO                                 -> `quarantena` (mai promozione automatica: giudizio umano)
Questa regola DOMINA l'alternativa piu' stretta su entrambi gli assi (0,11% di falsi positivi contro 0,43%, e 91,9% di recupero contro 81,5%) e non perde nulla sul gruppo a identita' certa (1.000/1.000 restano `confermata_data`).

PASSO 4 — le respinte: prima si riprova la regola sulla pagina che gia' abbiamo (0 richieste).
14 delle 170 (8,2% [5,0%, 13,3%]) non erano omonimi: erano FALSE RESPINTE, buttate da un matcher di club cieco ai diacritici e da una tolleranza di 3 giorni troppo secca.

PASSO 5 — le respinte vere: il titolo che porta l'anno di nascita.
Wikipedia disambigua i calciatori omonimi con la convenzione `Nome (footballer, born AAAA)`. Noi l'anno atteso ce l'abbiamo. Due sorgenti, in quest'ordine:
  5a. leggerlo dall'HATNOTE della pagina sbagliata che abbiamo gia' in cache — 37 su 170 (21,8%) contengono il titolo ESATTO col nostro anno, tutti link BLU (0 rossi). Costo per trovarlo: ZERO richieste. Costo per prenderlo: 1 richiesta a testa.
  5b. costruirlo alla cieca per i restanti. 1 richiesta a testa.
⚠️ Il titolo con l'anno NON e' univoco: `Burak Yilmaz (footballer, born 1995)` esiste ed e' una TERZA persona (7 febbraio contro il nostro 27 novembre). Quindi ogni pagina nuova ripassa comunque dal PASSO 3. E' esattamente cosi' che la sonda ha attaccato 13 pagine su 16 con 0 errori.

PASSO 6 — l'ordine dei tentativi cambia.
Oggi i suffissi si provano SOLO sul 404. Va provato il titolo-con-anno **anche quando il nome nudo ha dato una pagina con l'infobox**, se la verifica dice `respinta`: quella pagina e' di un altro, e la persona giusta puo' avere la sua voce. Costo: +1 richiesta solo sui respinti, non su tutti.

PASSO 7 — cosa resta a mano, ed e' poco.
17 righe su 211 restano in `quarantena` (Δ ESTRANEO, oppure DEBOLE senza corroborazione). Le ho aperte una per una: 2 sono davvero un'altra persona (Olaizola, Bruno Alves — entrambe con k=0), 3 sono la persona giusta con l'anagrafica sbagliata SULLA PAGINA (Haris Belkebla: la voce dice 3 agosto 2000, ma e' l'algerino del Brest/Angers nato 28 gennaio 1994, stessa altezza al centimetro, stesso ruolo, stesso club attuale — la data della pagina e' un finto pieno, R6), le altre 12 sono ambigue. La regola non le indovina: le DICHIARA.

### I numeri misurati

| cosa | valore | come |
|---|---|---|
| QUARANTENA — quante sono davvero la persona giusta | 192/211 = 91,0% promosse in automatico; 17 al giudizio umano; 2 RESPINTE (oggi sono nel database e sono sbagliate) | `verifica_identita_v2` eseguita sulle 211 righe `identita=quarantena` estratte da esiti.jsonl, con gli span club×anni da appearances.csv e la corroborazione letta dall'HTML in cache. Validazione girata sul codice proposto, non sullo script d'analisi. |
| Quanto la quarantena somiglia al gruppo a identita' CERTA (R7, con potenza) | nazionalita' Δ=−1,8% IC95% [−6,2%, +2,6%] · ruolo Δ=+4,7% [−0,5%, +9,9%] · altezza±3cm Δ=−2,8% [−7,0%, +1,4%]. MDE all'80% di potenza: 6,3% / 7,4% / 6,0% | Tre proporzioni indipendenti dalla data e dai club, lette dall'infobox in cache: quarantena promossa (n≈206) contro un campione casuale di 1.000 `confermata_data`. Tutti e tre gli IC a cavallo dello zero: una contaminazione ≥6-7% sarebbe stata vista, e non c'e'. |
| Limite inferiore distribution-free su quante quarantene sono la persona giusta | π ≥ 94,3% (stima puntuale), ≥ 89,9% al 95% | Miscela: p_osservata(Δ≤366gg)=94,8% sulle 211 quarantene; p_nulla(Δ≤366gg)=8,96% misurata sulle 2.389 coppie di persone DIVERSE con lo stesso nome in players.csv. π ≥ (p_oss − p_null)/(1 − p_null), con l'estremo inferiore di Wilson su entrambe. E' conservativo: assume che nessun refuso vero superi l |
| Falsi positivi della regola proposta — placebo «avversario che condivide un club» | 0,11% — IC95% [0,02%, 0,61%] su n=922. Confronto: regola stretta 0,43% [0,17%, 1,11%] con solo 81,5% di recupero; regola permissiva senza corroborazione 4,56% [3,39%, 6,10%] con 97,6% | Per ogni pagina a identita' certa si sceglie a caso un giocatore DIVERSO che condivide almeno un club con la carriera della pagina, e si chiede alla regola se attaccherebbe. E' il caso peggiore costruibile: garantisce la sovrapposizione di club, cioe' l'evidenza su cui si reggeva la regola vecchia. |
| Falsi positivi — placebo OMONIMO ESATTO (dichiarato senza potenza) | 0/86 con la regola completa; 3/86 = 3,5% con la sola coerenza club×anni a k=1, 0/86 a k≥2. Ristretto a chi ha anche club in comune: n=5, IC [0%, 43%] | Pagine confermate accoppiate con l'anagrafica di un omonimo esatto del dataset. ⚠️ R7: a n=5 non c'e' potenza; il numero NON va citato come conferma. I 3 falsi agganci a k=1 sono TUTTI casi di famiglia (Nikolaos Lazaridis 1979/1997, Robinho 1984/1997, Andre Santos 1983/1989) — e' proprio la trappola |
| Sensibilita' — quanto costa la nuova regola a chi era gia' giusto | 0. 1.000/1.000 restano `confermata_data`. La coerenza club×anni da sola scatta sul 96,9% [95,6%, 97,8%] delle identita' certe | La regola nuova non tocca il ramo della data entro 3 giorni; agisce solo sotto. Il 96,9% e' la sensibilita' del solo asse club×anni, misurata sul campione di 1.000 confermate: il 3,1% che non scatta sono giocatori i cui club dello strato 1 non compaiono nell'infobox (seconde squadre, prestiti brevi) |
| La trappola FRATELLI / PADRE-FIGLIO — esiste, e l'ho trovata nel nostro campione | SI. Caso conclamato: Javier Olaizola, pagina 28/11/1969 (San Sebastian, terzino destro, Eibar/Real Burgos/Mallorca) contro il nostro nato 15/03/2007 (centrale, Mallorca 2025-26). 37 anni di scarto, CLUB IN COMUNE, e la copertura-club lo confermava. Secondo caso: Bruno Alves 1981 (il portoghese, 187 cm, centrale) contro il nostro 1990 (179 cm, mediano) | Ispezione diretta delle pagine in cache (data, luogo di nascita, altezza, ruolo, categorie) per tutti i 7 casi di quarantena che la regola non risolve in automatico. Entrambi cadono su k=0: la finestra temporale li uccide, il nome del club no. |
| Quanto e' diffusa la trappola di famiglia, misurata | Nel dataset: 988 gruppi di omonimi esatti, 2.389 coppie. Con almeno un CLUB in comune: 15 coppie fratelli (2-9 anni) e 2 coppie padre-figlio (18-40 anni), cioe' lo 0,7% delle coppie omonime | Prodotto cartesiano dentro ogni gruppo di nomi identici in players.csv, incrociato con l'insieme dei club da appearances.csv. ⚠️ R4: e' un LIMITE INFERIORE. Olaizola padre (1969) non e' nel nostro dataset — vive solo su Wikipedia. Il conteggio vede solo le trappole che players.csv contiene; quelle c |
| RESPINTE — quante sono FALSE respinte (la pagina in mano e' gia' la persona giusta) | 14/170 = 8,2% — IC95% [5,0%, 13,3%]. Costo: ZERO richieste di rete | Applicazione della regola nuova alle 170 respinte. Sono casi come Svyatoslav Georgievski (5 giorni di scarto, 4 club su 4 coerenti anche negli anni: bocciato dai diacritici) e German Lux (giorno e mese invertiti). |
| RESPINTE — la persona giusta ha una pagina? (via HATNOTE, gia' in cache) | 37/170 = 21,8% hanno nell'hatnote il titolo ESATTO col nostro anno di nascita, tutti link BLU, zero rossi. Sonda su 8: pagina esistente 8/8 = 100%, aggancio corretto 7/8 = 87,5% [52,9%, 97,8%] | Estrazione degli attributi `title=` dai blocchi `div.hatnote`/`div.dablink` delle 170 pagine in cache. Poi 8 richieste vere a 1/s. L'unico non agganciato e' `Burak Yilmaz (footballer, born 1995)`: la pagina esiste ma e' una TERZA persona (7 febbraio contro 27 novembre) — la verifica l'ha scartata co |
| RESPINTE — la persona giusta ha una pagina? (titolo COSTRUITO alla cieca) | pagina esistente 8/20 = 40% [21,9%, 61,3%]; aggancio corretto 6/20 = 30% [14,5%, 51,9%]. Delle 8 esistenti, 3 (37,5%) erano di UN'ALTRA persona e sono state scartate | 20 richieste vere a 1/s su `Nome (footballer, born AAAA)` per respinte NON coperte dall'hatnote. Le 3 scartate: Romario 1992 (13/03 contro 15/01), Liam Henderson 1996 (25/04 contro 23/08), piu' Burak Yilmaz nell'altro strato. Il complemento — il 60% che da' 404 — e' la risposta onesta alla domanda:  |
| RESPINTE — esito end-to-end della sonda | 16 pagine trovate, 13 attaccate, 0 identita' sbagliate | Ogni pagina della sonda ri-passata dal parser dell'infobox + regola nuova. Le 3 non attaccate sono esattamente le 3 pagine di un'altra persona. Nessuna richiesta aggiuntiva: le pagine erano gia' in cache dopo la sonda. |
| SOTTOPRODOTTO fuori dal mio fronte, ma e' lo stesso codice | 58,2% delle pagine di DISAMBIGUA in cache (campione 400 dei 2.102 `nessun_infobox`) contiene gia' il titolo `Nome (footballer, born <nostro anno>)`. Altre 34,2% linkano calciatori di altri anni | Stesso estrattore, applicato al corpo della disambigua invece che all'hatnote. Zero richieste di rete: le pagine sono gia' scaricate. E' il fronte 1 (i mononimi brasiliani/spagnoli/portoghesi) e questa e' la chiave. |
| ANOMALIA R6 trovata e dichiarata: due dialetti HTML nella stessa cache | Prima misura sulle disambigua: 0/250 = 0,0%. Misura corretta: 58,2%. Non un dato mancante — un PARSER cieco | Le pagine in cache convivono in due formati: quello classico con href relativi `/wiki/...` e l'output Parsoid con href ASSOLUTI (`rel="mw:WikiLink"`, id `mwXX`). Un selettore `a[href^="/wiki/"]` vede zero link sul secondo e non solleva nessun errore. Chiunque tocchi questa cache deve usare un estrat |
| Quanto vale in righe di carriera | Quarantena: 1.643 tappe senior gia' nel database la cui identita' passa da «dubbia» a «confermata», meno 18 tappe di due persone sbagliate che escono. Respinte: ~73 giocatori × 8,0 tappe senior ≈ 580 tappe NUOVE | Conteggio diretto delle `tappe` non giovanili nelle due popolazioni di esiti.jsonl; media di 8,0 tappe senior per giocatore misurata sui respinti. |
| Il costo di rete dell'intero fronte | 137 richieste in tutto (~2,5 minuti a 1 richiesta/secondo). ZERO per le 199 in quarantena | 33 titoli letti dagli hatnote + 104 costruiti alla cieca, scalati ai 152 del brief. La quarantena non chiede nemmeno una richiesta: tutto quello che serve e' gia' in `data/wikipedia_cache/en/`. |

### Rischi dichiarati

- POTENZA ASIMMETRICA. Il ramo piu' grosso del recupero delle respinte (il titolo costruito alla cieca) e' misurato su n=20: 30% [14,5%, 51,9%]. Il ramo vale ~31 righe con IC [15, 54]. Se serve stringere, bastano altre 40-60 richieste — ma vanno fatte dal processo unico, non da un agente.
- IL PLACEBO OMONIMO NON HA POTENZA. 0/86 con la regola completa suona bene ma l'IC arriva al 4%, e ristretto a chi ha anche club in comune n=5 -> IC [0%, 43%]. Il numero che regge e' il placebo «stesso club» a n=922. Non citare il placebo omonimo come conferma (R7).
- IL CONTEGGIO DELLE TRAPPOLE DI FAMIGLIA E' UN LIMITE INFERIORE. 15 coppie fratelli + 2 padre-figlio con club in comune contano solo le coppie in cui ENTRAMBI stanno in players.csv. Javier Olaizola padre (1969) non c'e': vive solo su Wikipedia. Il vero denominatore e' piu' grande e non e' misurabile con i dati che abbiamo.
- IL TITOLO CON L'ANNO NON E' UNIVOCO. Esistono due calciatori omonimi nati lo STESSO anno: `Burak Yilmaz (footballer, born 1995)` non e' il nostro Burak Yilmaz del 1995. Il titolo e' un candidato, mai una prova: ogni pagina nuova deve ripassare dalla verifica d'identita', altrimenti si reintroduce l'errore che la verifica esiste per impedire.
- IL BIAS DI CITTADINANZA NON SI CHIUDE QUI. Questo fronte vale 351 righe su 4.477; i mononimi brasiliani/spagnoli/portoghesi stanno quasi tutti nei 2.102 `nessun_infobox`. Il 58,2% misurato sulle disambigua dice che la chiave e' la stessa, ma finche' quel fronte non e' fatto la confondente resta.
- LA CORROBORAZIONE E' RUMOROSA SULLA POPOLAZIONE SBAGLIATA. Altezza e nazionalita' sono contestate fra le fonti proprio per i giocatori la cui data e' contestata: usarle come TERZO voto (dopo club×anni) va bene, usarle come primo no. Aaron Ramsey 1990 contro 2003 corrobora 3 su 3 ed e' un'altra persona.
- LE 17 RIGHE LASCIATE A MANO NON SONO UN RESIDUO TRASCURABILE. Contengono le 2 identita' sbagliate che oggi stanno nel database. Se nessuno le guarda, la regola ha comunque fatto il suo lavoro (non le promuove) ma il database resta sporco: vanno RIMOSSE, non solo non-promosse.
- TOLLERANZA ±1 ANNO SULLE FINESTRE. E' un iperparametro non ottimizzato: l'ho fissato a priori sulla grana annuale dell'infobox, non per griglia. Alzarlo aumenta il recupero e i falsi positivi; il numero che ho misurato vale per ±1.
- DERIVA DEI DATI. La raccolta gira: fra l'inizio e la fine di questa analisi le due popolazioni sono passate da 152/199 a 170/211. I TASSI trasferiscono, i conteggi assoluti no. Rifare i conti sul file finale prima di scrivere numeri nel README.

<details><summary>Codice proposto (non applicato)</summary>

```python
Il file completo, pronto, e' in `/tmp/claude-0/-home-user-Polymarket-oracle/1edc272d-613d-56fc-909b-6ca07c8eb53a/scratchpad/proposta.py` (284 righe, importa e gira; NON applicato al repo, come richiesto). Gli script di misura che producono ogni numero di questa risposta stanno accanto: `coer.py` (coerenza club×anni), `corrob.py` (i tre tratti dalla pagina). Il nucleo:

```python
# --- asse 1: i club, ma con gli ANNI -----------------------------------------

_STOP_CLUB = {"fc","cf","ac","sc","afc","cd","ud","sd","ss","as","club","de",
              "futbol","football","calcio","sa","sad","spa","s","p","a","the",
              "sportiva","societa","atletico","e","associacao","esporte","clube",
              "gmbh","co","kgaa","ev","f","c","u","d","team","kulubu","spor","ii","1"}

def _norm_club(s: str) -> str:
    """'Fudbalski Klub Rabotnicki Skopje' e 'Rabotnicki' devono coincidere.

    Il matcher precedente era un `in` fra stringhe minuscole: i diacritici lo
    facevano fallire in silenzio. Costo misurato: Svyatoslav Georgievski, 4
    club su 4 coincidenti, respinto per 5 giorni di scarto anagrafico.
    """
    s = _ud.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = _re.sub(r"[^a-zA-Z0-9 ]", " ", s).lower()
    return " ".join(t for t in s.split() if t and t not in _STOP_CLUB)

def club_coincide(nostro: str, loro: str) -> bool:
    a, b = _norm_club(nostro), _norm_club(loro)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return bool({t for t in set(a.split()) & set(b.split()) if len(t) >= 4})

def coerenza_temporale(club_anni, tappe, *, tolleranza=1, anno_corrente=None):
    """Quanti club dello STRATO 1 la pagina conferma **anche negli anni**.

    `club_anni`: iterabile di `(nome_club, primo_anno, ultimo_anno)` da
    `appearances.csv` — quindi su `player_id`, immune all'omonimia.

    Ritorna `(k_club, k_club_e_anni, n_club)`. E' `k_club_e_anni` che
    discrimina: il solo NOME del club non basta, perche' padre e figlio giocano
    nello stesso club (Javier Olaizola, Mallorca anni '90 contro Mallorca
    2025-26) e i compagni di squadra pure.
    """
    anno_corrente = anno_corrente or _dt.date.today().year
    k_c = k_ct = 0
    for club, y0, y1 in club_anni:
        m_c = m_ct = False
        for t in tappe:
            if not club_coincide(club, t.club):
                continue
            m_c = True
            da, a = t.anno_da, t.anno_a
            if da is None and a is None:
                continue
            if a is None:
                a = anno_corrente if t.aperta else da
            if da is None:
                da = a
            if max(da, y0 - tolleranza) <= min(a + tolleranza, y1):
                m_ct = True
        k_c += m_c
        k_ct += m_ct
    return k_c, k_ct, len(list(club_anni))


# --- asse 2: la FORMA della discordanza anagrafica ---------------------------

def livello_delta(bday, nascita_attesa) -> str:
    """Non «quanto» differiscono le due date, ma **come**.

    Misurato sulle 2.389 coppie di persone DIVERSE con lo stesso nome dentro
    `players.csv`: solo lo 0,96% ha le date entro 31 giorni e solo lo 0,25%
    condivide giorno+mese. Uno scarto di quella forma non e' «un'altra
    persona»: e' un refuso anagrafico fra due fonti.
    """
    a, b = _data(bday), _data(nascita_attesa)
    if a is None or b is None:
        return "ignoto"
    dd = abs((a - b).days)
    if dd <= 31:                                   return "FORTE"   # giorno o mese
    if a.month == b.month and a.day == b.day:      return "FORTE"   # anno
    if a.day == b.month and a.month == b.day:      return "FORTE"   # gg/mm invertiti
    if dd <= 366:                                  return "DEBOLE"
    return "ESTRANEO"


# --- asse 3: i tratti gia' dentro l'HTML che abbiamo (zero richieste) --------
# corroborazione(html, anagrafica) -> (concordi, discordi) su nazionalita'
# (place of birth + categorie "X men's footballers"), ruolo e altezza +-3 cm.
# Presi da SOLI non bastano: Aaron Ramsey nato 1990 corrobora 3 su 3 con il
# nostro nato 2003 (gallese, centrocampista, stessa statura) ed e' un'altra
# persona. Servono come TERZO voto, mai come prova.


# --- la regola ---------------------------------------------------------------

def verifica_identita_v2(bday, nascita_attesa, tappe, club_anni=None,
                         corrob=(0, 0), tolleranza_giorni=3):
    """Tre assi INDIPENDENTI, non una gerarchia a cascata.

    Esiti: `confermata_data` · `confermata_coerenza` · `quarantena` · `respinta`.

    MISURATO — avversario che condivide un club col nostro giocatore (n=922,
    il placebo piu' duro costruibile):

        regola                                 falsi positivi      quarantena recuperata
        stretta      (DEBOLE richiede k>=2)    0,43% [0,17;1,11]   81,5%
        permissiva   (DEBOLE basta k=1)        4,56% [3,39;6,10]   97,6%
        QUESTA       (permissiva + 2/3 tratti) 0,11% [0,02;0,61]   91,9%

    Questa DOMINA la stretta su entrambi gli assi: meno errori E piu' recupero.
    Sensibilita' sul gruppo a identita' certa (n=1.000): 100%, nessuna perdita.

    ⚠️ Il placebo OMONIMO ha n=5 -> IC [0%, 43%]: su quell'avversario non c'e'
    potenza e il numero non va citato come conferma (R7).
    """
    senior = [t for t in tappe if not t.giovanili] or list(tappe)
    _, k, _ = coerenza_temporale(club_anni or [], senior)
    liv = livello_delta(bday, nascita_attesa)
    conc, disc = corrob

    a, b = _data(bday), _data(nascita_attesa)
    if a and b and abs((a - b).days) <= tolleranza_giorni:
        return "confermata_data"
    if k == 0:
        # Nessun club confermato NEGLI ANNI. E' il caso padre-figlio/omonimo:
        # le 2 sole identita' davvero sbagliate rimaste in quarantena (Javier
        # Olaizola 1969 contro il nostro 2007, stesso Mallorca; Bruno Alves
        # 1981 contro il nostro 1990) cadono tutte e due esattamente qui.
        return "respinta"
    if liv == "FORTE
```

</details>

## Fronte 4 — i «nessun_blocco»: pagina con infobox ma senza tabella carriera (634 casi al 01/08/2026, tutti in cache, diagnosi a ZERO richieste di rete)
**Stima**: 116 su 634

**Tasso**: 18,3% (116/634), IC95 [14,9%, 19,4%] propagando la precisione misurata dell'instradamento (23/25) sui 126 casi instradabili — NON dall'ipotesi del fronte. Con la leva che il fronte proponeva (ampliare le etichette di sezione) il recupero e' ZERO: 0/634, IC95 [0%, 0,60%].

**Falsi positivi attesi**: MISURATO su campione di rete di 25 pagine (1 richiesta al secondo): la regola d'instradamento da sola aggancia la persona sbagliata 2 volte su 25 = 8,0% (IC95 [2,2%, 25,0%]) — due omonimi nati lo STESSO ANNO ma in un altro giorno (Leonardo 1988-02-05 contro il nostro 1988-04-09; Bruno Barbosa 1994-04-28 contro 1994-05-26). Composta con verifica_identita() esistente: 23 confermata_data + 2 respinta = 0 agganci sbagliati su 25, IC95 [0%, 13,3%]. Estrapolando ai 126: ~10 candidati respinti, ~116 confermati per data. Residuo NON misurabile con n=25: omonimi con lo stesso giorno di nascita esatto (non osservati; la potenza esclude solo tassi > 13,3%).

**Costo**: "+1 richiesta per giocatore, e solo per i 126 instradabili con certezza: 126 richieste in totale (~2 minuti a 1 req/s). Tutto il resto costa ZERO: la classificazione dei 634, il censimento delle intestazioni, la misura del danno da ampliamento e il guadagno delle 7.421 tappe si fanno sulle pagine già in cache. Le 25 richieste del campione di verifica sono già state spese in questa analisi (pagine ora in cache, riusabili). Se si vuole stringere l'intervallo sui falsi positivi prima di procedere: +75 richieste."

### Strategia

PASSO 0 — non ampliare le etichette. È la conclusione, non una premessa: il censimento dice che l'ipotesi (a) è falsa e che l'ampliamento è dannoso. Lasciare INTESTAZIONI_SENIOR = ("senior career",) e INTESTAZIONI_GIOVANILI = ("youth career","college career").

PASSO 1 (0 richieste) — riclassificare i 634 leggendo le pagine già in cache con `classifica_pagina()`: disambigua 200 · pagina_di_nome 144 · soggetto_diverso 275 · senza_infobox 12 · senza_blocco vero 3. Sostituire il test `if "infobox" not in html`, che non testa ciò che dice. Effetto: `nessun_blocco` smette di essere un fallimento d'identità silenzioso travestito da bug del parser.

PASSO 2 (0 richieste) — togliere il vincolo «la cella anni deve contenere un anno a 4 cifre» in parse_career, con guardia sulla FORMA della cella (vuota, oppure sole cifre/`?`/trattini). Questa leva NON serve ai 634 (recupera 3 pagine, tutte omonimi, tutte respinte) ma vale +7.421 tappe (+3,96%) sulle 19.968 pagine che GIÀ funzionano, senza scaricare nulla. Va rifatta girando il parser sulla cache, non sulla rete.

PASSO 3 (1 richiesta per giocatore, 126 in tutto, ~2 minuti a 1 req/s) — instradamento: la pagina sbagliata è una tabella di instradamento. Si estraggono dai link della pagina in cache i titoli con disambiguatore calcistico; si tiene SOLO il caso in cui esiste ESATTAMENTE UN candidato il cui titolo porta l'anno di nascita atteso (`candidati_calcistici`); si scarica quella pagina e si passa il risultato per `verifica_identita()` invariata. Regola gerarchica NON allentata: se la data non coincide entro 3 giorni, si respinge.

PASSO 4 (da NON fare finché non è misurato a parte) — i 208 casi con candidati ma nessuno con l'anno atteso, i 18 con più candidati dello stesso anno e i 282 senza candidati restano aperti: appartengono al fronte 3 (disambigua/mononimi) e vanno risolti lì, con la ricerca per nome+data, non da qui. Aprirli qui significherebbe alzare la copertura con una regola la cui precisione non è stata misurata.

PASSO 5 — registrare gli esiti nuovi con lo stato che dice la CAUSA (`disambigua`, `pagina_di_nome`, `soggetto_diverso`, `senza_blocco`) e la provenienza dell'instradamento (`titolo_instradato`), così la sessione dopo non ri-tenta i 287 «soggetto_diverso» credendoli un problema di parsing.

### I numeri misurati

| cosa | valore | come |
|---|---|---|
| Ipotesi (c) — la pagina è di un altro soggetto | 631/634 = 99,53% (IC95 98,6-99,8%) | Censimento COMPLETO delle 634 pagine in cache: disambigua 200 (id=disambigbox / Category:All_disambiguation_pages), pagine di NOME 144 (shortdescription 'Name list'/'given name'), soggetto diverso 287 (basket, baseball, ciclismo, città, santi, re, club). Verificato con tre segnali indipendenti: shor |
| Ipotesi (a) — etichetta di sezione diversa | 0 casi | Censimento delle intestazioni su 2.000 pagine che oggi funzionano: 'Senior career' compare in 2.000/2.000 (100%). Il Template:Infobox football biography ha UNA sola etichetta, senza varianti per portieri o giocatrici. Le intestazioni alternative trovate nei 634 ('Career history', 'Career information |
| Ipotesi (b) — assenza vera del blocco | 0 casi puri; 3 casi di anni assenti (club presente) | Le uniche 3 biografie di calcio del lotto (Omar Traoré, Julius Beck, Víctor Fernández) hanno la sezione 'Senior career*' con la colonna Years VUOTA: il club c'è, l'anno no. Il parser le scartava per il vincolo sull'anno, non per l'etichetta. |
| Le 3 biografie di calcio sono la persona GIUSTA? | 0 su 3 | Omar Traoré: pagina 1975-02-27 (senegalese), nostro player_id 388294 nato 1998-02-04. Julius Beck: pagina neozelandese in nazionale nel 1967, nostro 802512 nato 2005-04-27. Víctor Fernández: pagina dell'allenatore nato 1960, nostro 415205 nato 1998-05-02. Recupero netto del fronte con l'ampliamento  |
| Danno dell'ampliamento «prudente» (club/professional/playing career, senior clubs) | 0 righe cambiate su 2.000 pagine buone, ma 13 pagine / 111 righe di ALTRI SPORT sui 634 | Innocuo sulle pagine buone, inutile sul calcio: 13/13 pagine recuperate sono NBA (Mohamed Bamba, Ben Gordon, Nenê), pallamano, ciclismo. L'unica cosa che fermerebbe l'iniezione è la verifica d'identità: seconda linea, non prima. |
| Danno dell'ampliamento con «career history / career information / teams» | 18 pagine / 141 righe, 18 su 18 di altri sport | Stesso censimento sui 634. Aggiunge baseball (Iván Rodríguez), pallavolo (Rodrigão), ciclismo World Tour (Mads Pedersen). Zero calcio. |
| Danno dell'ampliamento con «career» generico | rompe il 92,0% delle pagine buone | Su 2.000 pagine oggi corrette: 1.840 cambiate, +7.765 righe SPURIE (le nazionali giovanili promosse a tappe di club: 'Spain U17', 'Germany U19', 'France U21') e 3.161 righe PERSE. È il rischio principale del fronte, ed è reale solo per questa variante. |
| Guadagno vero della rimozione del vincolo sull'anno (censimento completo) | +7.421 tappe (+3,96%) su 5.206 pagine (26,07%, IC95 25,5-26,7%) | Parser attuale contro parser rilassato su TUTTE le 19.968 pagine 'ok' in cache: 187.308 → 194.729 righe. Il 99,30% delle aggiunte è giovanile (7.369 su 7.421). Mediana 1 riga per pagina toccata, massimo 8. Controllo spazzatura: i club aggiunti sono club veri (Ajax 35, Red Star Belgrade 30, Feyenoord |
| Forma della cella-anni nelle righe recuperate | 738 su 739 vuote, 1 con '200?–200?' | Misurato sul campione di 2.000: giustifica la guardia proposta (accettare solo cella vuota o sole cifre/`?`/trattini), che tiene fuori le righe-etichetta di altri template ('High school', 'College', 'NBA draft', 'Drafted by'). |
| Potenziale d'instradamento già presente nelle pagine scaricate | 352/634 = 55,5% (IC95 51,6-59,3%) con almeno un candidato; 126/634 = 19,9% (IC95 17,0-23,2%) con UN solo candidato dell'anno giusto | Estrazione dei link con disambiguatore calcistico dal corpo della pagina in cache e confronto dell'anno nel titolo ('Pedro (footballer, born 2006)') con nascita_attesa. 18 casi hanno più candidati dello stesso anno, 208 nessuno con quell'anno, 282 nessun candidato. |
| Precisione dell'instradamento, misurata sulla rete | 23/25 = 92,0% (IC95 75,0-97,8%) prima della verifica; 0/25 agganci sbagliati dopo (IC95 0-13,3%) | Campione di 25 titoli distinti, una richiesta al secondo, 25 richieste in totale. Confronto <span class='bday'> contro date_of_birth. I 2 errori (stesso anno, altro giorno) sono entrambi respinti da verifica_identita() senza toccarla. |
| Tappe attese dal recupero | ~1.150 tappe su ~116 giocatori | Media di 9,9 tappe per pagina confermata sul campione di 25 (228 tappe su 23 pagine), moltiplicata per i 116 attesi. Costo: 126 richieste. |
| Il confine fra `nessun_infobox` e `nessun_blocco` è arbitrario | 252/634 pagine «nessun_blocco» non hanno alcun <table class='infobox'>, e 195 di quelle sono disambigue | Il test `if "infobox" not in html` è vero su quasi ogni voce, perché la stringa compare nel CSS TemplateStyles incorporato ('.mw-parser-output .infobox .side-box{...}'). Regola R6: non è un NaN, è un test che dichiara di misurare una cosa e ne misura un'altra. |
| Composizione per cittadinanza dei 634 | Brasile 265 (41,8%), Portogallo 77, Spagna 60; mononimi 62,6% | Join con files/player_scores/players.csv.gz. Nelle classi A e B i mononimi sono il 95,0% e il 93,1%: questo fronte è la STESSA confondente del fronte 3, non un fronte di parsing. |

### Rischi dichiarati

- La leva che il fronte proponeva (ampliare le etichette) è quella da NON tirare: nella variante generica «career» distrugge il 92,0% delle pagine che oggi funzionano (+7.765 righe spurie, −3.161 righe). Le varianti prudenti non rompono nulla ma iniettano carriere NBA/ciclismo su player_id di calciatori: il guadagno misurato sul calcio è esattamente zero, quindi il rapporto rischio/beneficio non è «basso», è indefinito.
- Le CATEGORIE di Wikipedia NON sono un segnale d'identità affidabile (R4, anomalia dichiarata anche se non è un errore nostro): la voce del GOLFISTA Sergio García porta tre categorie di calcio, fra cui «Men's association football players not categorized by position». Un filtro «è un calciatore se ha categorie di calcio» l'avrebbe accettato. La firma affidabile è la nota a piè d'infobox «* Club domestic league appearances and goals».
- La regola d'instradamento si appoggia all'anno nel TITOLO della voce: è un dato scritto a mano da un redattore, non un campo strutturato. Due omonimi nati lo stesso anno esistono e li abbiamo misurati (2 su 25). L'unica difesa è la data piena della verifica d'identità: se un giorno si allenta quella (per «recuperare di più»), questa strategia diventa un iniettore di omonimi.
- Il residuo non misurato: omonimi con lo STESSO giorno di nascita. Con n=25 la potenza esclude solo tassi superiori al 13,3%. Prima di girare la strategia sui 126 conviene ampliare il campione di verifica a ~100 pagine (100 richieste, ~2 minuti) per stringere l'intervallo.
- La rimozione del vincolo sull'anno introduce 7.421 tappe con anno_da=None: sono dato mancante DICHIARATO, non finto pieno — ma qualunque analisi che ordini la carriera per anno deve gestirle esplicitamente (regola R8: il valore c'è, il momento no). Il 99,3% sono giovanili, quindi impattano soprattutto la ricostruzione del settore giovanile, non le tappe senior.
- I 634 continuano a crescere mentre la raccolta gira (erano 557 quando il fronte è stato scritto, 634 al momento della misura): le percentuali sono stabili ma i valori assoluti vanno rimisurati sul file finale prima di eseguire.
- 287 pagine «soggetto_diverso» e 282 senza alcun candidato restano scoperte da questa strategia. Chiuderle significa cercare fuori dalla pagina (ricerca per nome+data), che è il fronte 3: non va fatto qui, perché la sua precisione non è stata misurata in questo lavoro.

<details><summary>Codice proposto (non applicato)</summary>

```python
"# ─── PROPOSTA per src/data/wikipedia_careers.py — NON applicata al repo ───\n# Verificata girando sulla cache: parse_career proposta == attuale sulle pagine\n# senza righe anni-vuoti (Lewandowski 11==11) e le aggiunge dove ci sono\n# (Randy Wolters 13→17, Pape Demba Diop 4→6).\n\n# ── 1. INTESTAZIONI: l'elenco CORRETTO è quello che c'è già. Misurato. ──────\n# Censimento 01/08/2026 su 2.000 pagine che oggi funzionano: \"Senior career\"\n# compare in 2.000/2.000 (100%). Il Template:Infobox football biography usa UNA\n# sola etichetta, senza varianti per portieri o per giocatrici. Ampliare NON\n# recupera calcio e IMPORTA altri sport (misurato sui 634 «nessun_blocco»):\n#   +(\"club career\",\"professional career\",\"playing career\",\"senior clubs\")\n#        -> 13 pagine, 111 righe — 13 su 13 sono NBA/ciclismo/pallamano;\n#   + (\"career history\",\"career information\",\"teams\")\n#        -> 18 pagine, 141 righe — 18 su 18 altri sport. Zero calcio;\n#   + \"career\" generico\n#        -> rompe il 92,0% delle pagine buone (1.840/2.000): +7.765 righe\n#           spurie (nazionali giovanili promosse a club) e 3.161 righe PERSE.\nINTESTAZIONI_SENIOR = (\"senior career\",)\nINTESTAZIONI_GIOVANILI = (\"youth career\", \"college career\")\nINTESTAZIONI_FINE = (\"international career\", \"managerial career\",\n                     \"medal record\", \"honours\")\n\n# Cella-anni senza anno: ammessa solo se vuota o \"quasi-anno\" ('200?–200?').\n# Tiene fuori le righe-etichetta di ALTRI template (\"High school\", \"College\",\n# \"NBA draft\", \"Drafted by\"). Misurato: 738 righe su 739 hanno la cella vuota.\n_RE_ANNI_AMMESSI = re.compile(r\"[\\d?–—\\-\\s]*\")\n_FIRMA_CALCIO = \"club domestic league appearances and goals\"\n\n\n# ── 2. PERCHÉ la pagina non dà una carriera. Zero richieste: legge la cache. ─\ndef classifica_pagina(html: str) -> str:\n    \"\"\"Sostituisce il test `if \"infobox\" not in html`, che **non testa ciò che\n    dice**: la stringa \"infobox\" sta nel CSS TemplateStyles incorporato in quasi\n    ogni voce, disambigue comprese (R6). Misura: 252 delle 634 pagine finite in\n    `nessun_blocco` non hanno NESSUN `<table class=\"infobox\">`, e 195 di quelle\n    sono disambigue — lo stesso fenomeno di `nessun_infobox`, separato da un\n    confine arbitrario.\n\n    Censimento completo dei 634 (tutti in cache, 0 richieste):\n      disambigua        200 (31,5%)\n      pagina_di_nome    144 (22,7%)   liste antroponimiche (\"Name list\")\n      soggetto_diverso  275 (43,4%)   altro sport, città, santi, re, club\n      senza_infobox      12 ( 1,9%)\n      senza_blocco        3 ( 0,5%)   biografie di calcio vere\n    Cioè: il 99,5% di questo fronte NON è parsing, è la pagina sbagliata. È un\n    fallimento d'IDENTITÀ silenzioso: se la voce sbagliata è di un calciatore lo\n    stato lo dichiara (`identita_non_confermata`); se è di un cestista finisce\n    qui e sembra un bug del parser.\n    \"\"\"\n    soup = BeautifulSoup(html, \"lxml\")\n    if soup.find(id=\"disambigbox\") or \"Category:All_disambiguation_pages\" in html:\n        return \"disambigua\"\n    sd = soup.find(\"div\", class_=\"shortdescription\")\n    sd = sd.get_text(\" \", strip=True) if sd else \"\"\n    if re.search(r\"name list|given name|surname|list of people with the same\",\n                 sd, re.I):\n        return \"pagina_di_nome\"\n    if _FIRMA_CALCIO in html.lower():\n        return \"senza_blocco\"          # è una voce di calcio: manca il dato\n    if soup.find(\"table\", class_=_e_infobox) is None:\n        return \"senza_infobox\"\n    return \"soggetto_diverso\"\n\n\n# ── 3. La pagina sbagliata è una TABELLA DI INSTRADAMENTO ───────────────────\ndef candidati_calcistici(html: str, anno_atteso: int | None) -> list[str]:\n    \"\"\"I titoli-candidato già presenti NELLA PAGINA SCARICATA.\n\n    Misurato sui 634: 352 (55,5%) contengono almeno un link con disambiguatore\n    calcistico; **126 (19,9%, IC95 17,0-23,2%)** ne contengono ESATTAMENTE UNO\n    con l'anno di nascita atteso nel titolo. Campione di rete di 25 pagine (1\n    richiesta al secondo): 23/25 sono la persona giusta (precisione 92,0%, IC95\n    75,0-97,8%); le 2 sbagliate hanno lo stesso ANNO ma un'altra data, e\n    `verifica_identita` le respinge entrambe -> 0 agganci sbagliati su 25\n    (IC95 0-13,3%).\n\n    Ritorna i candidati con l'anno giusto: si scarica SOLO se la lista ha\n    lunghezza 1. Con più di un candidato l'anno non basta e il caso va al\n    fronte 3 (ricerca per nome+data), non risolto qui.\n    \"\"\"\n    soup = BeautifulSoup(html, \"lxml\")\n    corpo = soup.find(\"div\", class_=\"mw-parser-output\") or soup\n    re_foot = re.compile(r\"footballer|football player|soccer\", re.I)\n    re_anno = re.compile(r\"born\\s+(?:\\w+\\s+)?(\\d{4})\")\n    titoli: list[str] = []\n    for a in corpo.find_all(\"a\"):\n        t = a.get(\"title\")\n        if not t or t in titoli:\n            continue\n        if \"page does not exist\" in t or t.startswith(\"Edit section\"):\n            continue\n        if re_foot.search(t):\n            titoli.append(t)\n    if anno_atteso is None:\n        return titoli\n    return [t for t in titoli\n            if (m := re_anno.search(t)) and int(m.group(1)) == anno_atteso]\n\n\n# ── 4. parse_career: UNA sola modifica, sulla riga del vincolo dell'anno ────\ndef parse_career(html: str, player_id: int, url: str) -> list[Tappa]:\n    \"\"\"Come oggi, con una modifica: **anni ignoti ≠ riga non valida**.\n\n    Wikipedia lascia la colonna Years VUOTA quando gli anni non si sanno.\n    Pretendere un anno a 4 cifre buttava via in silenzio tappe con il club\n    scritto per esteso. Censimento su TUTTE le 19.968 pagine già riuscite:\n      +7.421 tappe (+3,96% sulle 187.308 attuali) su 5.206 pagine\n      (26,07%, IC95 25,5-26,7%), di cui il 99,30% giovanili;\n      mediana 1 riga per pagina toccata, massimo 8.\n    Controllo spazzatura: i club aggiunti sono club veri (Ajax 35, Red Star\n    B
```

</details>
