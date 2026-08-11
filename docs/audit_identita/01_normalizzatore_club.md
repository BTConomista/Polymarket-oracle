# Il normalizzatore dei nomi di club

> Dominio come dichiarato dall'agente: **Normalizzatore dei nomi di club — src/data/club_matching.py**

> 7 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

Questo dominio non ha un difetto di modello ma un difetto di COPERTURA ALFABETICA, e ha esattamente la forma che il modulo stesso documenta a riga 29 (ø/ł/đ) senza averla chiusa: `_TRADUZIONE` è una lista scritta a mano, e ogni carattere latino che NFKD non decompone e che non è in quella lista viene sostituito da uno spazio dal `re.sub(r"[^a-z0-9 ]", " ")` — cioè spezza il token invece di tradurlo, in silenzio. Ho enumerato l'universo: sono 320 caratteri latini alfabetici sotto U+2500 (comando in evidenza del difetto 1), di cui 5 attivi oggi nelle fonti. Il secondo difetto è la faccia R6 dello stesso problema: omoglifi cirillici e greci che RENDERIZZANO come ASCII ('FС Taganrog' con la С cirillica, 'Οlympiacos' con l'omicron greca) — finto pieno da manuale, perché nessun confronto snapshot-contro-fonte li vede e non agganciano mai. Ho scandito tutte e nove le fonti di nomi del repo (incluse le carriere Wikipedia, 22.410 club distinti, che il compito non elencava ed è dove i difetti sono più diffusi): 15 nomi hanno token sbagliati e 7 agganci univoci si recuperano, con zero regressioni e zero nuove collisioni. Le _STOPWORD invece NON hanno il difetto 'sporting' in forma attiva sulle fonti principali (0 nomi azzerati su 987), ma ce l'hanno latente e attivo sulle carriere (11 su 22.410, fra cui 'Sport'); il leave-one-out mostra che toglierle peggiora — la riparazione giusta lì è l'alias, non la lista.

---

## 1. I caratteri latini che NFKD non decompone vengono BUTTATI invece che tradotti: 'Ħ' e 'ə' confermati, ma sono 320 in tutto

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`

### Evidenza

CONFERMATO: `normalizza('Ħamrun Spartans')` -> {'amrun','spartans'} (il club esiste: 'Hamrun Spartans', club_id 17149, e l'aggancio fallisce SOLO per questo); `normalizza('Zirə FK')` -> {'zir'} (il club esiste: 'Zira FC', 46710). ESTESO: l'universo dei caratteri con lo stesso difetto è 320 sotto U+2500, ricalcolabile con `python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/universo.py`. Attivi oggi nelle fonti: Ħ (U+0126, sofascore + carriere), ə (U+0259, sofascore + carriere), Þ (U+00DE, 6 club islandesi in carriere: 'Þór Akureyri' -> {'akureyri','or'}). Censimento completo dei non-ASCII per fonte: `python .../scratchpad/censimento.py` -> 22 caratteri BUTTATI, 6 tradotti, 43 decomposti.

### Riparazione proposta

In src/data/club_matching.py, sostituire la tabella scritta a mano con una tabella DERIVATA dal nome Unicode più un residuo esplicito, così la famiglia si chiude invece di allungarsi a ogni fonte nuova:

```python
def _stroke_e_simili() -> dict[int, str]:
    """'LATIN <CAP|SMALL> LETTER X WITH ...' che NFKD non decompone -> 'x'.
    E' la famiglia di o-slash/l-stroke/d-stroke gia' nota (docstring, riga 29):
    NFKD non la tocca perche' il tratto non e' un segno combinante."""
    pat = re.compile(r"^LATIN (?:CAPITAL|SMALL) LETTER ([A-Z]) WITH ")
    fuori = {}
    for cp in range(0x100, 0x2500):
        c = chr(cp)
        if not c.isalpha():
            continue
        try:
            n = unicodedata.name(c)
        except ValueError:
            continue
        base = "".join(x for x in unicodedata.normalize("NFKD", c)
                       if not unicodedata.combining(x)).lower()
        if base and re.fullmatch(r"[a-z0-9]+", base):
            continue          # NFKD basta gia'
        m = pat.match(n)
        if m:
            fuori[cp] = m.group(1).lower()
    return fuori

# I caratteri il cui nome Unicode NON contiene la lettera base: qui la scelta
# e' una TRASLITTERAZIONE, e ognuna e' verificata contro `club_names.csv.gz`.
_ESPLICITI = {
    "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ß": "ss", "ẞ": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe",
    "ð": "d", "Ð": "d", "þ": "th", "Þ": "th", "ı": "i",
    "ŋ": "n", "Ŋ": "n",
    # schwa azero: la traslitterazione corrente e' 'a', non 'e'.
    # VERIFICATA 2/2 sul registro: 'Zirə'->'Zira FC' (46710),
    # 'Səbail'->'FK Sabail' (57890).
    "ə": "a", "Ə": "a",
}

_TRADUZIONE = {**_stroke_e_simili(),
               **{ord(k): v for k, v in _ESPLICITI.items()}}
```

(`_stroke_e_simili()` gira una volta all'import, ~9k iterazioni: costo trascurabile. Se si preferisce non generare a runtime, il risultato si congela in un dict letterale con lo stesso script.)

### Guadagno atteso

+7 agganci univoci misurati, 0 regressioni. Fonte per fonte (`python .../scratchpad/riparazione.py`): sofascore Partite 181->183 univoci su 212 ('Zirə FK'->46710, 'Ħamrun Spartans FC'->17149); carriere_wikipedia/tappe 3.915->3.920 su 22.410 ('Səbail'->57890, 'Þór'->21864, 'Þór Akureyri'->21864, 'Ħamrun Spartans'->17149, più 'FC Taganrog' che passa da AMBIGUO a univoco); 5 snapshot di lega, coppe_2526 e smarkets invariati (già 100%/100%/95,8%). 15 nomi cambiano token, tutti verso la forma giusta; 0 nuove collisioni nel registro (24->24); ogni nuova identità verificata contro club_names.csv.gz.

---

## 2. Omoglifi cirillici e greci: caratteri che renderizzano come ASCII e non agganceranno mai (finto pieno, R6)

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`

### Evidenza

CONFERMATO e ESTESO. Il test è la scrittura mista (LATIN + CYRILLIC/GREEK nello stesso nome): `python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/omoglifi.py`. Cinque casi in tutto il repo, non due: in files/player_scores/club_names.csv.gz 'FС Taganrog (-2015)' (16611) e 'FС Vologda (-2014)' (40427), С = U+0421 CYRILLIC CAPITAL LETTER ES, entrambi -> token {'f','taganrog'} / {'f','vologda'} con la 'f' spuria; in data/carriere_wikipedia/tappe.csv.gz 'Cherkashchyna Сherkasy' -> {'cherkashchyna','herkasy'}, 'Οlympiacos Ζacharo' (omicron U+039F + zeta U+0396 GRECHE) -> {'lympiacos','acharo'}, 'BRW-ВІК Volodymyr-Volynskyi' (В/І/К cirilliche) -> perde 'ВІК'. Il danno non è solo il mancato aggancio: la 'f' spuria di 16611 lo rende non-esatto, e 'FC Taganrog' cercato da Wikipedia esce AMBIGUO [16611, 78749 Forte Taganrog] invece che univoco.

### Riparazione proposta

De-confusione MIRATA, applicata solo dove è diagnostica — cioè ai nomi a scrittura mista. Un nome interamente cirillico (932, 'Футбольный клуб «Локомотив» Москва') NON va toccato: tradurlo lettera per lettera produrrebbe spazzatura, e restare vuoto è l'esito onesto.

```python
# Omoglifi: caratteri che RENDERIZZANO come un ASCII senza esserlo. Nessun
# confronto snapshot-contro-fonte li vede, perche' il dato COINCIDE con la
# fonte: e' un finto pieno (R6). Si applicano SOLO ai nomi a scrittura mista,
# dove la mescolanza e' gia' di per se' la diagnosi.
_OMOGLIFI = str.maketrans({
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
})

def _scritture(s: str) -> set[str]:
    out = set()
    for c in s:
        if c.isalpha():
            try:
                out.add(unicodedata.name(c).split()[0])
            except ValueError:
                pass
    return out

def _deconfondi(nome: str) -> str:
    sc = _scritture(nome)
    if "LATIN" in sc and sc & {"CYRILLIC", "GREEK"}:
        return nome.translate(_OMOGLIFI)
    return nome
```

e, in `normalizza`, una sola riga cambiata:

```python
    s = _deconfondi(nome).translate(_TRADUZIONE)   # era: nome.translate(...)
```

NOTA sul perché la correzione sta nel normalizzatore e non in un registro R3: il dato sbagliato vive in files/player_scores/club_names.csv.gz, che è una fonte ESTERNA congelata; correggerla a monte significherebbe divergere dall'originale consegnato (§5-ter). Il normalizzatore invece non modifica nessun dato, rende solo confrontabile ciò che a occhio è già identico. Se si preferisce la via R3, i due valori-prima da registrare sono esattamente 'FС Taganrog (-2015)' e 'FС Vologda (-2014)'.

### Guadagno atteso

Sulle fonti attuali: +1 aggancio (carriere_wikipedia, 'FC Taganrog' ambiguo->univoco 16611, che è il club giusto: 78749 è 'Forte Taganrog', un altro club) e 4 nomi con token riparati. Verificata l'assenza di falsi positivi, che è il rischio vero: 'Οlympiacos Ζacharo' dopo la riparazione ha i token giusti {'olympiacos','zacharo'} e resta correttamente ASSENTE — NON pesca l'Olympiakos del Pireo (683), perché 'zacharo' non è nell'indice. 0 nuove collisioni nel registro (24->24). Il valore principale è prospettico: la regola d'oro degli agganci protegge dagli ambigui, non dagli invisibili, e un omoglifo è invisibile.

---

## 3. La _TRADUZIONE è asimmetrica fra maiuscole e minuscole: ð/þ/œ ci sono, Ð/Þ/Œ/ẞ no — e Þ è attivo su 6 club

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/test_coppe_aggancio.py`

### Evidenza

Ri-calcolabile con: `python -c "import sys,unicodedata as ud; sys.path.insert(0,'.'); from src.data.club_matching import _TRADUZIONE; [print(chr(cp), alt) for cp in _TRADUZIONE for alt in {chr(cp).upper()} if len(alt)==1 and alt!=chr(cp) and ord(alt) not in _TRADUZIONE]"` -> Ð (U+00D0), Þ (U+00DE), Œ (U+0152); manca anche ẞ (U+1E9E, capitale di ß). Non è teorico: in data/carriere_wikipedia/tappe.csv.gz Þ compare in 6 nomi di club islandesi e produce token spazzatura — 'Þór' -> {'or'}, 'Þór Akureyri' -> {'akureyri','or'}, 'Þróttur Reykjavík' -> {'reykjavik','rottur'} — mentre il registro scrive quel club già traslitterato, 'Thór Akureyri' (21864). È lo stesso bug della riga 29 del docstring, ripetuto nella metà maiuscola della tabella.

### Riparazione proposta

Se non si adotta la tabella generativa del difetto 1, la riparazione minimale è aggiungere quattro voci a `_TRADUZIONE`:

```python
    "ð": "d", "Ð": "d", "þ": "th", "Þ": "th",
    "œ": "oe", "Œ": "oe", "ß": "ss", "ẞ": "ss",
```

Più un test-guardia che rende l'asimmetria impossibile invece di lasciarla alla disciplina di chi scrive: per ogni chiave della tabella, la controparte maiuscola/minuscola dev'esserci con la stessa traduzione (`assert _TRADUZIONE[ord(c.upper())] == _TRADUZIONE[ord(c)]` per ogni c con upper() di lunghezza 1).

### Guadagno atteso

+2 agganci univoci misurati su carriere_wikipedia ('Þór' e 'Þór Akureyri' -> 21864, entrambi assenti oggi) e 4 nomi con token riparati. La tabella generativa del difetto 1 include già questi casi: le due riparazioni non si sommano, la seconda è il ripiego se si vuole toccare meno codice.

---

## 4. Le _STOPWORD hanno ancora il difetto 'sporting', ma è LATENTE sulle fonti principali e ATTIVO solo sulle carriere — e togliere stopword peggiora

**categoria** `ambiguita-da-decidere` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/test_coppe_aggancio.py`

### Evidenza

MISURATO, e il verdetto è meno grave di quanto la domanda supponga. (1) Nomi che perdono TUTTI i token: 0 su 987 nelle 8 fonti principali (5 snapshot + coppe + sofascore + smarkets); 11 su 22.410 in carriere_wikipedia — 'Sport', 'Club' non compare ma 'AFC', 'HK', 'US' sì, più "AFC '34", 'AFC 2', 'FC 92', 'FC 93', 'SL 16', 'SL 16 FC', 'ÍF'; 1 su 3.173 nel registro ('AC Football Club', club_id 121777, i cui tre token sono tutti stopword). (2) Il difetto è latente ma reale: `normalizza('Sport')`, `('Club')`, `('US')`, `('Calcio')` danno tutti frozenset() — e 'Sport' è il nome corrente dello Sport Club do Recife, 'Club' quello del Club Brugge. (3) LEAVE-ONE-OUT su tutte e 52 le stopword (`python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/loo.py`, riferimento 804/1.019 univoci): togliere una stopword non conviene quasi mai — 'fc' costa -18 univoci (Barcelona, Arsenal, Juventus e Celtic diventano ambigui), 'fk' -5, 'de' -4, 'ac' -3, 'sk' -3; 32 stopword su 52 sono neutre sull'universo misurato. Gli unici Delta positivi ('ud' +3, 'cd' +2, 'sd' +2) arrivano con regressioni proprie (senza 'ud': Las Palmas e Levante diventano ambigui). (4) Ho misurato anche il fallback ovvio — «se l'insieme è vuoto, riprova senza stopword»: Delta = +0, ZERO nomi cambiati, perché l'indice inverso è costruito con le stesse stopword e 'sport' non vi compare affatto. Se lo si costruisse anche sui token completi, 'Sport' pescherebbe 16 club, 'Club' 100, 'Calcio' 53: ambiguo, cioè vuoto lo stesso.

### Riparazione proposta

NON toccare la lista delle stopword: il leave-one-out dice che ogni rimozione costa più di quanto renda, e il fallback misurato rende zero. La riparazione corretta è quella che il progetto ha già usato per 'sporting': un ALIAS caso per caso, aggiunto quando una fonte reale usa quel nome breve, ognuno verificato a candidato unico. Concretamente, due cose da fare ora:

1. un test-guardia che trasforma il difetto latente in un difetto rumoroso — oggi un nome azzerato è indistinguibile da un nome senza aggancio:

```python
def test_nessun_nome_delle_fonti_perde_tutti_i_token():
    """Il caso 'sporting': una parola che e' sigla per un club e nome per un
    altro. Non e' riparabile a priori, ma non deve passare in silenzio."""
    for nome in nomi_di_tutte_le_fonti():
        assert normalizza(nome), f"{nome!r} resta senza token: serve un ALIAS"
```

2. dichiarare in `_STOPWORD` quali voci sono nomi portanti altrove, così la prossima sessione non le tratta come innocue:

```python
# ⚠️ Queste NON sono innocue: sono nome corrente di un club vero, e un nome
# breve uguale a una di esse esce VUOTO (misurato 11/08/2026). Chi le
# incontra come nome intero deve aggiungere un ALIAS, non toglierle da qui:
# togliere 'fc' costa -18 agganci univoci, 'fk' -5, 'de' -4 (leave-one-out).
#   'sport'  -> Sport Club do Recife, Sport Boys, Sport Huancayo (16 club)
#   'club'   -> Club Brugge (100 club)
#   'calcio' -> Calcio Padova (53 club) ; 'us' (17) ; 'afc' (22)
```

### Guadagno atteso

Nessun aggancio in più oggi: il guadagno è che il prossimo nome azzerato si vede subito invece di sparire fra i 203 'assente'. È la differenza fra un buco dichiarato e un finto pieno (R6).

---

## 5. I token di un solo carattere sono rumore che entra nell'indice, ma scartarli è la riparazione SBAGLIATA: aggancerebbe 339 nomi, molti dei quali riserve

**categoria** `ambiguita-da-decidere` · **rischio** `alto` · **riparabile ora** `False`

**File**: `src/data/club_matching.py`

### Evidenza

La punteggiatura produce token monocarattere: 'Società Sportiva Lazio S.p.A.' -> token 'p', 'A.G.S Asteras Tripolis' -> 'a','g','s', 'F.C. Gladsaxe' -> 'f','c' (perché 'fc' è stopword ma 'f' e 'c' no). Misurato con `python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/monotoken.py`: 15 token monocarattere distinti, e nell'indice inverso 's' raggiunge 17 club, 'b' 10, 'a' 7. La riparazione istintiva — scartare i token di lunghezza 1 — l'ho MISURATA prima di proporla: Delta = +339 univoci su carriere_wikipedia, ma il campione dei nuovi agganci è dominato da falsi positivi gravi — 'AS Monaco B' -> 162 (AS Monaco), 'AS Monaco C' -> 162, 'AC Ajaccio B' -> 1147, 'AEK Athens B' -> 2441, 'Académica B' -> 2990: sono squadre RISERVE agganciate alla prima squadra, esattamente ciò che NON_AGGANCIARE esiste per impedire. Rilievo R4 (un'anomalia si dichiara anche quando non è un errore): oggi le riserve restano scollegate PER CASO, perché il token 'b'/'c' finale non è nell'indice — è una protezione accidentale, non progettata, e nessuno l'ha scritta.

### Riparazione proposta

NON scartare i token monocarattere. La modifica va rifiutata esplicitamente e il motivo va scritto nel docstring, altrimenti una sessione futura la rifarà vedendo il +339:

```python
# ⚠️ NON filtrare i token di un solo carattere ('S.p.A.' -> 'p', 'A.G.S' ->
# 'a','g','s'). Misurato l'11/08/2026: farlo porta +339 agganci univoci sulle
# carriere Wikipedia, ma il campione e' dominato da RISERVE agganciate alla
# prima squadra ('AS Monaco B' -> 162, 'AC Ajaccio B' -> 1147, 'AEK Athens B'
# -> 2441). Oggi quelle restano scollegate perche' il token 'b' finale non e'
# nell'indice: e' una protezione ACCIDENTALE, non progettata. Chi vuole quei
# 339 deve prima estendere NON_AGGANCIARE alle riserve in modo sistematico
# (suffisso B/C/II/2/'Jong'/'Castilla'), non allentare il tokenizer.
```

### Guadagno atteso

Nessuno, ed è il punto: la misura serve a chiudere una strada che sembra un guadagno di +339 e sarebbe un peggioramento silenzioso della qualità (una CERTEZZA sbagliata, non un buco). Il lavoro vero, se lo si vuole, è il riconoscimento sistematico delle riserve — un difetto separato e più costoso.

---

## 6. Due club del registro sono invisibili all'indice e nessuno lo dichiara

**categoria** `assenza-a-monte` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `docs/DATI.md`

### Evidenza

`python -c "import sys,pandas as pd; sys.path.insert(0,'.'); from src.data.club_matching import normalizza; reg=pd.read_csv('files/player_scores/club_names.csv.gz'); print([(int(c),n) for c,n in zip(reg.club_id,reg.name) if not normalizza(n)])"` -> [(932, 'Футбольный клуб "Локомотив" Москва'), (121777, 'AC Football Club')]. `Agganciatore.__init__` fa `if not ts: continue`, quindi questi due club_id non entrano né in `_per_id` né in `_inverso`: nessun nome potrà MAI agganciarli, e la cosa non compare da nessuna parte. 932 è il Lokomotiv Mosca scritto in cirillico — la de-confusione del difetto 2 correttamente NON lo tocca (tradurre lettera per lettera un nome interamente cirillico produrrebbe spazzatura); 121777 ha tre token tutti stopward.

### Riparazione proposta

Non è un bug da riparare in silenzio ma un'assenza da dichiarare (R4). Due opzioni, entrambe a rischio nullo:

1. la via ALIAS, coerente col resto del modulo — 'Lokomotiv Moscow': 'Футбольный клуб "Локомотив" Москва' (da verificare a candidato unico prima di inserirlo: al momento della verifica il nome cirillico non ha token, quindi l'alias va scritto come coppia nome-fonte -> club_id, non nome -> nome);
2. la via DICHIARAZIONE — rendere l'esclusione visibile invece che implicita:

```python
        for cid, nome in zip(club_names["club_id"], club_names["name"]):
            ts = normalizza(nome)
            if not ts:
                # Il club esce dall'indice: NESSUN nome potra' mai agganciarlo.
                # Misurati 2 su 3.173 (11/08/2026): 932 'Футбольный клуб
                # «Локомотив» Москва' (nome interamente cirillico) e 121777
                # 'AC Football Club' (tre token, tutte sigle societarie).
                self.senza_token.append((int(cid), nome))
                continue
```

con `self.senza_token: list[tuple[int, str]] = []` inizializzato sopra, così il numero è interrogabile e un test può fissarlo.

### Guadagno atteso

Zero agganci in più; rende contabile un'esclusione oggi invisibile. Serve al momento in cui una fonte russa entrerà nel progetto: senza questa dichiarazione, il Lokomotiv Mosca risulterebbe 'assente' come qualunque club che nel registro non c'è, e nessuno saprebbe che invece c'è.

---

## 7. 13 gruppi di club collassano sullo stesso insieme di token per colpa delle sigle: 6 nomi di coppa restano ambigui

**categoria** `ambiguita-da-decidere` · **rischio** `medio` · **riparabile ora** `False`

**File**: `src/data/club_matching.py`

### Evidenza

`python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/stopword.py`: nel registro 24 gruppi di club distinti condividono lo stesso frozenset (50 club su 3.173); 13 di questi gruppi sono CAUSATI dalle stopword, cioè i token grezzi li distinguerebbero — 'UD Logroñés' vs 'SD Logroñés' (due club diversi), 'CD Ourense' / 'Ourense CF' / 'UD Ourense', 'San Fernando CD' vs 'UD San Fernando', 'CD Extremadura 1924' vs 'Extremadura UD', 'FC Kudrivka' vs 'FK Kudrivka', 'AC Horsens' vs 'FC Horsens'. Effetto a valle misurato: 6 nomi di data/coppe_2526/partite.csv restano AMBIGUI (su 558; univoci 378, assenti 174) e 6 di sofascore. È il comportamento GIUSTO secondo la regola d'oro — un aggancio ambiguo si lascia vuoto — ma sono 12 agganci recuperabili con lavoro manuale.

### Riparazione proposta

Non è riparabile nel tokenizer (vedi difetto 4: togliere 'ud'/'cd'/'sd' sposta il problema su Las Palmas e Levante). La via è quella già collaudata nel modulo: un ALIAS per ciascuno, verificato uno per uno contro l'informazione indipendente (le competizioni che quel club_id gioca davvero in games.csv, come fu per «Brest» e «PAOK»). Elenco esatto dei 12 da istruire, che è il lavoro proposto — non una modifica da fare al buio:

```python
    # --- Club spagnoli che le sigle rendono INDISTINGUIBILI (misurato
    # 11/08/2026): la sigla e' l'unica cosa che li separa, e la sigla e'
    # stopword. Ognuno va verificato in games.csv PRIMA di essere scritto qui.
    # "SD Logroñés": <club_id>,   # NON UD Logroñés: sono due club diversi
    # "UD Logroñés": <club_id>,
    # "UD Ourense": <club_id>,    # e CD Ourense / Ourense CF
    # "UD San Fernando": <club_id>,
    # "CD Extremadura 1924": <club_id>,
```

Nota di forma: `ALIAS` oggi mappa nome -> nome, e per questi casi la mappatura nome -> nome non basta (i due nomi collassano sullo stesso insieme). Serve un secondo dizionario nome -> club_id, letto da `candidati()` prima della normalizzazione. È una modifica strutturale piccola ma reale, ed è la ragione per cui la lascio come proposta e non come patch.

### Guadagno atteso

Fino a +12 agganci univoci (6 in coppe_2526/partite.csv, 6 in sofascore Partite), ma solo dopo verifica caso per caso contro games.csv. Senza quella verifica il guadagno è negativo: sarebbero certezze sbagliate, che è il difetto che l'audit del 01/08/2026 ha già pagato una volta.

---
