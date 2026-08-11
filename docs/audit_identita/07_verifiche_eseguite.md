# Le 11 verifiche che hanno fatto in tempo a girare

> La fase di verifica prevedeva **54 agenti** (uno per reperto). Ne sono partiti
> 11 prima che la sessione esaurisse il limite. Tutti e 11 hanno **confermato**
> il reperto che stavano attaccando — ma erano tutti del dominio *club*, quindi
> il tasso di conferma di questo campione **non** si può estendere agli altri
> cinque domini.

---

## Verifica 1

**Esito**: `confermato = True`

### Motivo

IL DIFETTO E' REALE E RIPRODOTTO, E LA RIPARAZIONE E' CORRETTA E SICURA. MA I NUMERI DEL GUADAGNO SONO SBAGLIATI, E NON PER ARROTONDAMENTO: SONO STATI MISURATI SU UNA PATCH DIVERSA DA QUELLA PROPOSTA.

1) DIFETTO — confermato riga per riga. normalizza('Ħamrun Spartans')->{'amrun','spartans'} mentre il club esiste (17149 'Hamrun Spartans'); normalizza('Zirə FK')->{'zir'} (46710 'Zira FC'); normalizza('Þór Akureyri')->{'akureyri','or'} (21864 'Thór Akureyri'). L'universo dei 320 LATIN alfabetici buttati sotto U+2500 si riproduce esattamente.

2) LA PATCH PROPOSTA, APPLICATA DA SOLA, DA' +6, NON +7. Misurato sulle 8 fonti del repo: sofascore 181->183 (+2, esatto come dichiarato) e carriere/tappe 3.915->3.919 (+4, NON 3.920). Le altre sei fonti invariate. Il settimo aggancio dichiarato — 'FC Taganrog' da AMBIGUO a univoco — NON dipende da questa riparazione: verificato, candidati('FC Taganrog') = [16611, 78749] PRIMA E DOPO la patch proposta. Quel guadagno viene da un SECONDO intervento presente in scripts/.../riparazione.py ma ASSENTE dal testo proposto: la de-confusione degli OMOGLIFI cirillico/greco (il registro contiene 'FС Taganrog (-2015)' con una С CIRILLICA U+0421). Stessa origine per il conteggio '15 nomi cambiano token': con la sola patch proposta sono 10.

3) LA CITAZIONE DEL CENSIMENTO E' STALE. L'evidenza dichiara «22 caratteri BUTTATI, 6 tradotti, 43 decomposti»; lo script citato, eseguito adesso, stampa 37 BUTTATI / 13 tradotti / 96 decomposti. Tutti e tre i numeri sono sbagliati.

4) «LA FAMIGLIA SI CHIUDE» E' UNA SOVRA-AFFERMAZIONE. La tabella derivata cattura 125 caratteri; dei 320 ne restano 191 ancora buttati (ĸ, ŉ, Ɔ, Ɛ, Ɣ, Ǝ, ƕ...): sono i LATIN il cui nome Unicode non contiene «LETTER X WITH». E' vero invece — e questo l'ho misurato — che sui nomi OGGI presenti nelle fonti la famiglia latina si chiude davvero: i caratteri non-ASCII buttati passano da 37 a 34, e i tre che spariscono sono esattamente le uniche tre LETTERE LATINE attive (Ħ, ə, Þ). Il residuo e' tutto cirillico/greco/punteggiatura, cioe' un difetto diverso.

5) REGRESSIONI — cercate attivamente, nessuna trovata. La nuova tabella e' un SOVRAINSIEME stretto della vecchia (0 caratteri persi, 0 traduzioni divergenti). Sul registro club_names.csv.gz: 0 club su 3.173 cambiano token, gruppi in collisione 24->24 (0 nuovi, 0 spariti), club senza token 2->2. Nessuno dei 62 ALIAS cambia esito. NON_AGGANCIARE resta vuoto su tutte le voci. Nessun nome passa da univoco ad ambiguo o cambia club_id: le uniche 6 transizioni sono assente->univoco. Nessun artefatto salvato contiene club_id_agganciato, quindi niente da rigenerare.

6) IDENTITA' DEI 6 NUOVI AGGANCI — verificata con informazione indipendente, non con somiglianza di stringa. 'Ħamrun Spartans FC': sofascore lo da' Paese=Malta, stadi Centenary/Ta' Qali, preliminari CL/EL/Conference 2025-26; il registro 17149 ha 32 partite CLQ/ELQ/ECLQ/UCOL 2022-2025. 'Zirə FK': Paese=Azerbaijan, Neftçi Arena, Baku, Conference 2° preliminare 2025 contro Hajduk Split; il registro 46710 ha ECLQ/ELQ nel 2017/2022/2024/2025. 'Səbail'->57890 (FK Sabail): tappa di Farouk Miya in prestito 2018, e 57890 ha 2 partite ELQ 2019 — coerente per paese ed epoca. 'Þór Akureyri'->21864: 9 tappe, fra cui Aron Gunnarsson (giovanili 2004-06 e ritorno 2024/2026), islandese di Akureyri.

7) IL PUNTO PIU' DEBOLE, DA DICHIARARE (R4): 'Þór' NUDO. E' un nome corto che diventa univoco solo perche' l'altro Þór islandese (Þór Þorlákshöfn) nel registro NON C'E' — la stessa configurazione di «Brest» e «Red Star». Qui pero' l'informazione indipendente regge: le 2 sole righe sono entrambe giovanili dei fratelli Hlynsson (Kristian e Ágúst), e Ágúst Hlynsson ha nella STESSA carriera una tappa esplicita 'Þór Akureyri' (2026). E' un aggancio difendibile, ma va scritto nel commento che e' l'unico dei sei a poggiare su 2 righe e non sul nome completo.

8) TEST E COSTI. Patch applicata davvero al file e poi ripristinata (git status pulito): 93 test verdi su test_careers, test_coppe_aggancio, test_raccolta_coppa_diretta, test_coppe_query. _stroke_e_simili() costa 8,2 ms una volta all'import. Il passaggio da str.maketrans a dict letterale int->str non rompe scripts/registra_raccolta_coppa_diretta.py, che importa _TRADUZIONE e la incatena a .translate(): verificato dal suo test suite.

### Correzione alla riparazione proposta

IL CODICE VA BENE COSI' COM'E' SCRITTO (l'ho applicato verbatim: 142 voci, 125 derivate + 21 esplicite di cui 4 gia' coperte dal generativo). Correggere SOLO le affermazioni e i commenti.

A) Riscrivere il guadagno dichiarato con i valori veri della SOLA patch proposta:
   +6 agganci univoci, non +7.
   sofascore Partite: 181 -> 183 su 212 ('Zirə FK'->46710, 'Ħamrun Spartans FC'->17149).
   carriere_wikipedia/tappe: 3.915 -> 3.919 su 22.410, non 3.920 ('Səbail'->57890, 'Þór'->21864, 'Þór Akureyri'->21864, 'Ħamrun Spartans'->17149).
   5 snapshot di lega, coppe_2526 e smarkets: invariati.
   10 nomi cambiano token, non 15. Registro: 0 club con token cambiati, collisioni 24->24, 0 nuove.
   TOGLIERE 'FC Taganrog' dall'elenco: non e' un effetto di questa riparazione (misurato: candidati = [16611, 78749] prima e dopo).

B) Aggiungere una riga di perimetro onesta, perche' l'affermazione «la famiglia si chiude» vale solo sul dato di oggi:
   «Chiude la famiglia LATINA sui nomi presenti nelle fonti (i caratteri non-ASCII buttati passano da 37 a 34, e i tre che spariscono sono le uniche tre lettere latine attive: Ħ, ə, Þ). Restano fuori 191 dei 320 LATIN dell'universo — quelli il cui nome Unicode non contiene 'LETTER X WITH' (ĸ, ŉ, Ɔ, Ɛ, Ɣ, Ǝ, ƕ...): oggi nessuno compare in una fonte, ma la tabella NON e' esaustiva e va ri-misurata quando entra una fonte nuova.»

C) Correggere la citazione del censimento: lo script stampa 37 BUTTATI / 13 tradotti / 96 decomposti, non 22/6/43.

D) DIFETTO SEPARATO, DA APRIRE COME VOCE A SE' E NON DA NASCONDERE DENTRO QUESTA: gli OMOGLIFI cirillico/greco. Il registro stesso contiene 'FС Taganrog (-2015)' con С CIRILLICA (U+0421) e 'Cherkashchyna Сherkasy'; le carriere contengono 'Οlympiacos Ζacharo' con omicron e zeta GRECHE. E' un finto pieno da manuale (R6): il nome SEMBRA latino, nessun confronto testuale lo vede, e 'FC Taganrog' resta ambiguo per questo. Va misurato e deciso a parte, con la sua evidenza — non incorporato di soppiatto nel conteggio di questa riparazione.

E) Nel commento di _ESPLICITI, aggiungere accanto a Þ la nota che 'Þór' nudo e' l'unico dei sei agganci a non poggiare sul nome completo: e' univoco solo perche' Þór Þorlákshöfn nel registro non esiste (configurazione «Brest»/«Red Star»), ed e' sostenuto da informazione indipendente debole ma coerente — 2 righe, entrambe giovanili dei fratelli Hlynsson, uno dei quali ha nella stessa carriera una tappa esplicita 'Þór Akureyri'. Se un domani il registro acquisisse Þór Þorlákshöfn, quell'aggancio deve tornare vuoto da solo (e lo fa: diventerebbe ambiguo).

### Prove eseguite

- Riprodotta l'evidenza al codice di HEAD: normalizza('Ħamrun Spartans')->['amrun','spartans'], normalizza('Zirə FK')->['zir'], normalizza('Þór Akureyri')->['akureyri','or'], normalizza('Brøndby')->['brondby'] (controllo che la tabella vecchia funzioni)
- Riprodotto l'universo: 320 caratteri LATIN alfabetici in U+0020..U+24FF che normalizza() butta (scratchpad/universo.py), + 342 GREEK e 306 CYRILLIC
- Verificata l'esistenza dei club nel registro files/player_scores/club_names.csv.gz (3.173 righe): 17149 'Hamrun Spartans', 46710 'Zira FC', 57890 'FK Sabail', 21864 'Thór Akureyri'
- Implementata la riparazione PROPOSTA ALLA LETTERA (senza gli omoglifi di riparazione.py) e misurato l'aggancio prima/dopo su tutte le 8 fonti del repo: +6 univoci totali (sofascore 181->183, carriere 3.915->3.919, tutte le altre +0)
- Verificato che 'FC Taganrog' resta AMBIGUO [16611, 78749] prima e dopo la patch proposta: il +7 dichiarato include un guadagno prodotto dalla de-confusione degli omoglifi, che nella patch proposta non c'e'
- Contati i nomi con token cambiati con la sola patch proposta: 10 (non 15), tutti verso la forma corretta ('Səbail' ['bail','s']->['sabail'], 'Þróttur' ['rottur']->['throttur'], ecc.)
- Diff della tabella vecchia contro la nuova: 0 caratteri persi, 0 traduzioni divergenti (la nuova e' un sovrainsieme stretto)
- Dump integrale delle 125 voci derivate da _stroke_e_simili() con nome Unicode, ispezionate una per una: nessuna mappatura assurda (le uniche discutibili sono Ŀ/ŀ L WITH MIDDLE DOT -> 'l', corretta per il catalano)
- Verificato che il regex del testo ([a-z0-9]+, senza spazio) e quello di universo.py ([a-z0-9 ]+) producono la STESSA tabella di 125 voci: la differenza e' innocua
- Regressione sul registro: 0 club su 3.173 con token cambiati; gruppi in collisione 24->24, 0 nuovi e 0 spariti; club senza token 2->2
- Regressione sugli ALIAS: 0 su 62 cambiano esito di candidati()
- Regressione su NON_AGGANCIARE: tutte le voci restano senza candidati
- Censimento dei caratteri non-ASCII ATTIVI nelle fonti, prima e dopo: buttati 37 -> 34; i tre che spariscono sono Ħ (U+0126), ə (U+0259), Þ (U+00DE), cioe' TUTTE le lettere latine attive. Il residuo e' cirillico, greco, en-dash, apostrofo tipografico, ZWNJ
- Ri-eseguito lo script censimento.py citato nell'evidenza: stampa 37/13/96, non i 22/6/43 dichiarati
- Prova d'identita' indipendente su 'Zirə FK' e 'Ħamrun Spartans FC' dal foglio sofascore (Paese, citta', stadio, competizione, avversari, date) incrociata con games.csv: 46710 ha 16 partite ECLQ/ELQ incl. 2025, 17149 ne ha 32 incl. UCOL
- Prova d'identita' su 'Þór'/'Þór Akureyri'/'Səbail' leggendo le righe vere di data/carriere_wikipedia/tappe.csv.gz (giocatori, anni, source_url): Aron Gunnarsson e i fratelli Hlynsson per Akureyri, Farouk Miya in prestito 2018 per Sabail
- Patch applicata FISICAMENTE a src/data/club_matching.py e test eseguiti: 93 verdi su test_careers.py, test_coppe_aggancio.py, test_raccolta_coppa_diretta.py, test_coppe_query.py; poi file ripristinato, git status pulito
- Misurato il costo: _stroke_e_simili() 8,2 ms; import totale del modulo 0,42 s

---

## Verifica 2

**Esito**: `confermato = True`

### Motivo

Il difetto e' REALE e l'evidenza si riproduce esattamente. Il comando dichiarato restituisce Œ (U+0152), Ð (U+00D0), Þ (U+00DE) come controparti maiuscole assenti (piu' 'I' per 'ı', ASCII e innocua perche' .lower() lo gestisce comunque); ẞ (U+1E9E) e' effettivamente assente ma il comando NON lo vede, perche' 'ß'.upper() == 'SS' ha lunghezza 2 e la condizione len(alt)==1 lo scarta. Nessuno dei 4 caratteri e' decomposto da NFKD (verificato: unicodedata.normalize('NFKD', c) == c per tutti e quattro), quindi finiscono nel filtro [^a-z0-9 ] e diventano spazio: e' lo stesso meccanismo di ø/ł/đ della riga 29 del docstring.

Su data/carriere_wikipedia/tappe.csv.gz (22.410 nomi di club unici) Þ compare in 6 nomi ('Þróttur', 'Þróttur Reykjavík', 'Þróttur Vogum', 'Þór', 'Þór A.', 'Þór Akureyri') e i token spazzatura sono esattamente quelli dichiarati. Ð, Œ, ẞ compaiono ZERO volte in tutti i dati del repo (tappe + registro + 5 snapshot + coppe): la loro aggiunta e' profilattica, non misurata, e va dichiarata come tale (R4).

Guadagno: MISURATO E CONFERMATO. Prima/dopo con la tabella riparata su tutti i 22.410 nomi: 2 soli cambiamenti, entrambi 'assente' -> 'univoco' verso club_id 21864 ('Þór' e 'Þór Akureyri'); zero univoco->ambiguo, zero univoco->assente, zero cambi di club_id. Gli altri 4 nomi con Þ restano 'assente' ma con token sensati ('rottur' -> 'throttur'): 2 agganci + 4 nomi riparati = i 6 dichiarati.

Regressioni: cercate attivamente e NON trovate. Il registro club_names.csv.gz non contiene nessuno dei quattro caratteri (0 occorrenze di Þ/Ð/Œ/ẞ; ß in 10 nomi, gia' tradotto), quindi l'indice _per_id/_inverso non si muove e la traduzione puo' agire solo sul lato input, sui soli nomi che contengono quei caratteri. Su registro + 5 snapshot di lega + tutte le raccolte di coppa 2025-26 (3.318 nomi unici): 0 cambiamenti. tests/test_coppe_aggancio.py + tests/test_careers.py: 50 passed.

Prova d'identita' dei 2 agganci guadagnati (informazione INDIPENDENTE, non somiglianza di stringa): Ágúst Hlynsson (player_id 396936) ha nella stessa carriera sia 'Þór' (ordine 1, giovanili, ->2011) sia 'Þór Akureyri' (ordine 13, 2026), e la sua pagina Wikipedia lo da' nato ad AKUREYRI; suo fratello Kristian Hlynsson (694186) ha la stessa tappa giovanile 2000-2011 e la sua infobox la scrive per esteso 'Þór Akureyri'. Le due righe vanno davvero a 21864.

PERCHE' 'INCOMPLETA' E NON 'GIUSTA': il test-guardia proposto e' sbagliato e FALLIREBBE sulla tabella appena riparata. Con c='ı', c.upper()='I' ha lunghezza 1 e ord('I')=73 non e' in _TRADUZIONE -> KeyError. Verificato: applicando la guardia proposta alla tabella riparata, l'unico fallimento e' ('ı','I','ASSENTE'). In piu' la guardia NON copre ẞ — cioe' proprio il caso che dovrebbe proteggere — perche' 'ß'.upper() ha lunghezza 2 e viene saltato dal filtro len==1. Una guardia che boccia la tabella corretta e assolve il buco che le si chiede di sorvegliare va riscritta (vedi 'correzione').

### Correzione alla riparazione proposta

La TABELLA proposta e' giusta e va adottata cosi' (le voci si fondono con quelle esistenti; i duplicati letterali hanno lo stesso valore, quindi sono innocui ma meglio scrivere il dict una volta sola):

```python
_TRADUZIONE = str.maketrans({
    "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
    "ß": "ss", "ẞ": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe",
    "ð": "d", "Ð": "d", "þ": "th", "Þ": "th", "ı": "i",
})
```

Va invece RISCRITTA la guardia: quella proposta fallisce sulla tabella corretta (KeyError su 'ı'.upper()=='I') e non copre ẞ ('ß'.upper()=='SS', len 2 -> saltato). Versione che passa sulla tabella riparata e che, sulla tabella attuale, segnala esattamente i 4 buchi veri:

```python
def test_la_traduzione_e_simmetrica_fra_maiuscole_e_minuscole():
    """Ogni carattere della tabella porta con se' la sua controparte di caso.

    Le controparti ASCII (es. 'ı'.upper() == 'I') sono escluse: le gestisce
    gia' il .lower() di `normalizza`. La coppia ß/ẞ va vincolata a mano perche'
    'ß'.upper() vale 'SS' (due caratteri) e sfugge a un controllo su len == 1.
    """
    mancanti = []
    for cp, val in _TRADUZIONE.items():
        c = chr(cp)
        for v in (c.upper(), c.lower()):
            if len(v) != 1 or v == c or v.isascii():
                continue
            if _TRADUZIONE.get(ord(v)) != val:
                mancanti.append((c, v))
    for a, b in [("ß", "ẞ")]:          # case-folding non di lunghezza 1
        if _TRADUZIONE.get(ord(a)) != _TRADUZIONE.get(ord(b)):
            mancanti.append((a, b))
    assert not mancanti, f"controparti di caso mancanti o divergenti: {mancanti}"
```

Piu' un test di comportamento che ancori il guadagno misurato, altrimenti la guardia protegge la tabella ma non l'effetto:

```python
def test_thorn_maiuscolo_aggancia_thor_akureyri():
    assert normalizza("Þór Akureyri") == frozenset({"thor", "akureyri"})
    assert Agganciatore().aggancia("Þór Akureyri") == 21864
```

Due precisazioni da scrivere nel commento della tabella (R4, un'anomalia si dichiara anche quando non e' un errore):
1. il guadagno MISURATO riguarda solo Þ: Ð, Œ e ẞ compaiono zero volte in tutti i dati del repo, quindi sono profilattici — non spacciarli per agganci recuperati;
2. ⚠️ 'Þór' NUDO e' un candidato al caso «Brest» (R6): in Islanda esiste anche Þór Þorlákshöfn, che nel registro NON c'e', quindi un domani un 'Þór' riferito a quel club diventerebbe una CERTEZZA sbagliata invece di un vuoto. Oggi le due sole righe con quel nome sono verificate come Akureyri (Ágúst Hlynsson nato ad Akureyri e oggi in quel club; suo fratello Kristian scrive la stessa tappa per esteso), quindi l'aggancio va tenuto — ma la nota va lasciata accanto, perche' e' informazione che la prossima sessione non ricostruira' da sola.

### Prove eseguite

- Ri-calcolo dell'evidenza: `python -c "...from src.data.club_matching import _TRADUZIONE..."` -> Œ U+0152, Ð U+00D0, Þ U+00DE assenti (+ 'I' per 'ı', ASCII). Confermato che ẞ U+1E9E manca ma NON e' visto dal comando dichiarato, perche' 'ß'.upper()=='SS' (len 2).
- Verifica del meccanismo: unicodedata.normalize('NFKD', c) == c per Þ, Ð, Œ, ẞ, ı, ß -> nessuno e' decomposto, quindi cadono davvero nel filtro [^a-z0-9 ].
- Conteggio reale su data/carriere_wikipedia/tappe.csv.gz (209.809 righe, 22.410 club unici): Þ in 6 nomi, þ in 1, ð in 6, œ in 4, ß in 74, ı in 153; Ð/Œ/ẞ in 0. Il '6 club islandesi' dichiarato e' esatto.
- Token attuali: normalizza('Þór')={'or'}, normalizza('Þór Akureyri')={'akureyri','or'}, normalizza('Þróttur Reykjavík')={'reykjavik','rottur'} — identici ai valori dichiarati.
- Registro: files/player_scores/club_names.csv.gz contiene 'Thór Akureyri' con club_id 21864 (unica riga), gia' traslitterato.
- Prima/dopo su TUTTI i 22.410 nomi di tappe.csv.gz con la tabella riparata: 2 cambiamenti, entrambi assente->univoco verso 21864; 0 univoco->ambiguo, 0 univoco->assente, 0 cambi di club_id. Totali: univoco 3.916 -> 3.918, ambiguo 277 -> 277, assente 18.217 -> 18.215.
- Regressione su altre fonti: prima/dopo su registro + data/{5 leghe}_matches.csv (home_team/away_team) + tutti i CSV di data/coppe_2526 = 3.318 nomi unici -> 0 cambiamenti.
- Raggio d'azione: 0 occorrenze di Þ/Ð/Œ/ẞ in club_names.csv.gz -> l'indice _per_id/_inverso e' invariato, la patch puo' agire solo sui nomi in input che contengono quei caratteri.
- Test esistenti: python -m pytest tests/test_coppe_aggancio.py tests/test_careers.py -q -> 50 passed.
- Prova d'identita' indipendente (R5 passo 2) via Wikipedia: Ágúst Hlynsson nato ad Akureyri, giovanili 'Þór' 2000-2011, oggi a 'Þór Akureyri'; Kristian Hlynsson (stessa tappa 2000-2011) la scrive per esteso 'Þór Akureyri'. Entrambe le righe guadagnate = 21864.
- Verifica avversariale della GUARDIA proposta, applicata alla tabella gia' riparata: fallisce su ('ı','I','ASSENTE') -> il test boccerebbe la riparazione stessa. E salta ẞ, perche' 'ß'.upper() ha len 2.
- Verifica della guardia CORRETTA (due direzioni, controparti ASCII escluse, coppia ß/ẞ vincolata a mano): 0 mancanti sulla tabella riparata, e sulla tabella ATTUALE segnala esattamente [('œ','Œ'),('ð','Ð'),('þ','Þ'),('ß','ẞ')] — cioe' cattura il difetto e non il falso allarme.

---

## Verifica 3

**Esito**: `confermato = True`

### Motivo

IL DIFETTO E' REALE E RIPRODOTTO, LA DIREZIONE DELLA RIPARAZIONE E' GIUSTA, MA LA REGOLA CHE LA INNESCA E' SBAGLIATA E VA STRETTA.

1) DIFETTO CONFERMATO (ri-calcolato da zero, non fidandomi dello script fornito).
Scansione larga: 750 colonne di tutti i CSV/CSV.GZ/JSON sotto data/ e files/, 244.502 stringhe distinte. Nomi a scrittura mista LATIN + CIRILLICO/GRECO: 12, di cui 5 sono nomi di club con un omoglifo vero (gli altri 4 sono 'Juventus Next Gen [ α ]' e varianti, dove α e' un marcatore, e 3 sono nomi di PERSONA). I 5:
  files/player_scores/club_names.csv.gz  16611 'FС Taganrog (-2015)'  -> {'f','taganrog'}
  files/player_scores/club_names.csv.gz  40427 'FС Vologda (-2014)'   -> {'f','vologda'}
  data/carriere_wikipedia/tappe.csv.gz  'Cherkashchyna Сherkasy'      -> {'cherkashchyna','herkasy'}
  data/carriere_wikipedia/tappe.csv.gz  'Οlympiacos Ζacharo'          -> {'acharo','lympiacos'}
  data/carriere_wikipedia/tappe.csv.gz  'BRW-ВІК Volodymyr-Volynskyi' -> perde 'ВІК'
Code point verificati uno per uno: U+0421 CYRILLIC CAPITAL ES (x2), U+039F GREEK CAPITAL OMICRON, U+0396 GREEK CAPITAL ZETA, U+0412/U+0406/U+041A. E' finto pieno da manuale (R6).

2) IL DANNO DICHIARATO E' VERO, E L'IDENTITA' REGGE SU INFORMAZIONE INDIPENDENTE (non su somiglianza di stringa). Applicando la patch proposta e ri-calcolando `candidati()` su 74.637 nomi reali di tutto il repo, cambia ESATTAMENTE UNA riga: 'FC Taganrog' passa da ambiguo (16611, 78749) a univoco (16611). Che 16611 sia il club giusto lo dice il TEMPO, non il nome: in tappe.csv.gz le tre righe 'FC Taganrog' sono 2010-2011, 2012-2015 e 2014 (tutte <=2015, coerenti con 'FC Taganrog (-2015)'), mentre le 21 righe 'Forte Taganrog'/'FC Forte Taganrog' sono 2020-2025 e vanno a 78749. Nessuna sovrapposizione.
Collisioni nel registro 24 -> 24 (nessuna nuova, nessuna persa); token distinti nell'indice 4.164 -> 4.164; `pytest` intero 1.608 verdi con la patch applicata; costo 1,8x su `normalizza` (0,156s -> 0,284s su 31.730 nomi), accettabile.

3) IL DIFETTO DELLA RIPARAZIONE: «scrittura mista» NON e' «omoglifo». La condizione d'innesco proposta e' a livello di NOME INTERO: basta un carattere latino in tutta la stringa perche' OGNI carattere cirillico/greco di forma latina venga tradotto — anche quando e' testo autentico. Due conseguenze misurate:
  (a) INVENTA UN TOKEN. 'BRW-ВІК Volodymyr-Volynskyi' diventa 'bik'. Ma «ВІК» e' una parola cirillica vera, non un impostore, e la stessa fonte la scrive in tre modi latini diversi: in tappe.csv.gz ci sono 10 righe 'BRW-VIK', 8 'BRW-BIK', 2 'BRW-WIK' e 1 'BRW-ВІК'. La patch sceglie una delle tre per FORMA. Oggi e' innocuo (0 club con token 'brw' nel registro), ma e' esattamente il finto pieno che la riparazione dice di combattere: 'bik' sembra un token e non lo e'.
  (b) CREA UN FALSO POSITIVO DELLA CLASSE «BREST». Con la patch, 'ΠΑΟΚ FC' — la grafia greca vera del PAOK — diventa {'aok'} e aggancia UNIVOCO al club 5219 'AOK Kerkyra', che e' un altro club. Senza la patch resta vuoto (esito onesto). Simmetricamente 'ΠΑΣ Giannina' oggi aggancia univoco a 2671 'PAS Giannina' e con la patch diventa ASSENTE. Su 6.242 nomi misti sintetici (nome del registro + una parola cirillica autentica) 6.242 su 6.242 passano da univoco ad assente, con token spuri 'a','c','o','ap' che nel registro ESISTONO davvero.
Nessuna di queste stringhe e' oggi nel repo (per questo il diff reale e' pulito), ma la fonte da cui vengono i 5 casi e' proprio lo scraping di Wikipedia, che continuera'. La regola sarebbe una mina prospettica in entrambe le direzioni.

4) COSA NON RISOLVE (incompletezza, non errore). Lo stesso finto pieno vive fuori da club_matching e la patch non lo tocca: `src/data/player_identity.normalizza_nome('Αbdul Razak')` -> {'bdul','razak'} (players.csv.gz ha 177321 'Abdul Razak' e 339560 'Αbdul Razak', due player_id distinti) e `src/data/allenatori.normalizza_nome('Αlexandros Maniatoglou')` -> 'αlexandros maniatoglou', che non potra' mai uguagliare la forma latina.

5) ANOMALIE DA DICHIARARE COMUNQUE (R4). 'Ολυμπιακός Piraeus FC' aggancia univoco a 2670 'Ethnikos Piraeus' — falso positivo PREESISTENTE del modulo, non introdotto ne' risolto da questa riparazione. E i due nomi interamente cirillici ('Сокол Обручище' e 'Футбольный клуб "Локомотив" Москва' — nel file ha virgolette ASCII, non le caporali citate nell'evidenza) restano correttamente vuoti in tutte e tre le versioni.

VERDETTO: confermato, ma la patch va sostituita con la versione ristretta del campo 'correzione', che sui dati reali dà lo STESSO identico guadagno (+1, 'FC Taganrog' -> 16611), 0 regressioni su 74.637 nomi, collisioni 24 -> 24, e in piu' non inventa 'bik', non pesca AOK Kerkyra e non perde PAS Giannina. Verificata con i 110 test delle suite d'aggancio verdi.

### Correzione alla riparazione proposta

De-confondere PAROLA per PAROLA, non nome per nome. La diagnosi non e' «il nome mescola due alfabeti» ma «dentro una parola altrimenti latina c'e' un carattere straniero di forma latina». Una parola interamente cirillica o greca ('ВІК', 'ΠΑΟΚ', 'Динамо') e' TESTO: tradurla per forma inventa un token, ed e' lo stesso finto pieno (R6) che si vuole togliere. In piu': si traduce solo se TUTTI i caratteri stranieri della parola sono omoglifi noti — se ne resta uno fuori mappa, la parola non e' un impostore travestito e si lascia stare.

```python
# Omoglifi: caratteri che RENDERIZZANO come un ASCII senza esserlo. Nessun
# confronto snapshot-contro-fonte li vede, perche' il dato COINCIDE con la
# fonte: e' un finto pieno (R6).
# ⚠️ La diagnosi e' la PAROLA MISTA, non il nome misto. «BRW-ВІК» e «ΠΑΟΚ FC»
# mescolano due alfabeti ma il pezzo straniero e' una parola VERA: tradurla
# lettera per lettera fabbrica token inesistenti ('bik', 'aok') e 'aok' aggancia
# univoco al club sbagliato (5219 AOK Kerkyra). Restare vuoti e' l'esito onesto.
_OMOGLIFI = {
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
}
_OMOGLIFI_TAB = str.maketrans(_OMOGLIFI)


def _scrittura(c: str) -> str:
    try:
        return unicodedata.name(c).split()[0]
    except ValueError:
        return "?"


def _deconfondi(nome: str) -> str:
    """Traduce solo le PAROLE miste in cui ogni carattere straniero e' un omoglifo noto."""
    def f(m: "re.Match[str]") -> str:
        p = m.group(0)
        if "LATIN" not in {_scrittura(c) for c in p}:
            return p                     # parola straniera vera: non si tocca
        est = [c for c in p if _scrittura(c) in {"CYRILLIC", "GREEK"}]
        if not est or any(c not in _OMOGLIFI for c in est):
            return p                     # niente omoglifi, o non tutti noti
        return p.translate(_OMOGLIFI_TAB)
    return re.sub(r"[^\W\d_]+", f, nome)   # parole = run alfabetici, cosi' «BRW-ВІК» si spezza
```

e in `normalizza` la stessa unica riga della proposta:

```python
    s = _deconfondi(nome).translate(_TRADUZIONE)   # era: nome.translate(...)
```

Esito misurato di QUESTA versione (comandi ri-eseguibili in scratchpad: VA_corretta.py + VB_confronto.py):
- 'FС Taganrog (-2015)' -> {'taganrog'}, 'FС Vologda (-2014)' -> {'vologda'}, 'Cherkashchyna Сherkasy' -> {'cherkashchyna','cherkasy'}, 'Οlympiacos Ζacharo' -> {'olympiacos','zacharo'}: identici alla proposta;
- 'BRW-ВІК Volodymyr-Volynskyi' -> {'brw','volodymyr','volynskyi'}: NON inventa 'bik';
- diff su 74.637 nomi reali: 1 solo cambio, 'FC Taganrog' ambiguo(16611,78749) -> univoco(16611) — stesso identico guadagno della proposta;
- collisioni registro 24 -> 24; 'ΠΑΟΚ FC' resta assente (la proposta lo agganciava a AOK Kerkyra); 'ΠΑΣ Giannina' resta univoco 2671 (la proposta lo perdeva); 'Динамо Kyiv' e 'Шахтар Donetsk' invariati;
- 110 test verdi su tests/test_careers.py, test_coppe_aggancio.py, test_aggancio_coppe.py, test_coppe_2526.py, test_raccolta_coppa_diretta.py.

DUE COSE DA AGGIUNGERE ALLA RIPARAZIONE, oltre al codice:
1. un TEST di guardia che fissi i due lati della regola, perche' e' il lato negativo quello che si perde per strada:
   `assert normalizza('FС Taganrog (-2015)') == normalizza('FC Taganrog (-2015)')` (omoglifo riparato)
   `assert 'bik' not in normalizza('BRW-ВІК Volodymyr-Volynskyi')` (parola vera non tradotta)
   `assert Agganciatore().candidati('ΠΑΟΚ FC') == []` (nessun falso positivo AOK Kerkyra)
   `assert Agganciatore().aggancia('ΠΑΣ Giannina') == 2671` (nessuna regressione)
2. la dichiarazione, in docs/DATI.md, che lo stesso finto pieno resta APERTO fuori da questo modulo: `player_identity.normalizza_nome('Αbdul Razak')` -> {'bdul','razak'} (player_id 339560 contro 177321 'Abdul Razak') e `allenatori.normalizza_nome('Αlexandros Maniatoglou')` -> 'αlexandros maniatoglou'. Non e' compito di questa riparazione risolverli, ma lasciarli non dichiarati sarebbe far credere che il problema sia chiuso.

### Prove eseguite

- Ri-calcolo indipendente dell'evidenza: scansione di 750 colonne su tutti i CSV/CSV.GZ/JSON sotto data/ e files/ (244.502 stringhe distinte). Nomi a scrittura mista LATIN+CIRILLICO/GRECO: 12, di cui 5 club con omoglifo vero. Confermati i 5 dichiarati; scoperti in piu' 3 nomi di PERSONA con Alpha greca e 4 varianti 'Juventus Next Gen [ α ]' dove α non e' un omoglifo. Script: scratchpad/V2_scan.py
- Verifica code point uno per uno con unicodedata.name: U+0421 CYRILLIC CAPITAL ES in 16611 e 40427 e in 'Cherkashchyna Сherkasy'; U+039F GREEK OMICRON e U+0396 GREEK ZETA in 'Οlympiacos Ζacharo'; U+0412/U+0406/U+041A in 'BRW-ВІК'
- Applicazione della patch PROPOSTA e diff completo di candidati() prima/dopo su 74.637 nomi unici di tutto il repo: 1 solo cambio, 'FC Taganrog' ambiguo(16611,78749) -> univoco(16611). Conteggi complessivi: assente 67.035 invariato, univoco 7.238->7.239, ambiguo 364->363. Script: scratchpad/V7_nomi.py + V8_diff.py
- Collisioni nel registro (due club_id con lo stesso insieme di token): 24 prima, 24 dopo, nessuna nuova e nessuna persa. Token distinti nell'indice 4.164 -> 4.164. Script: scratchpad/V4_effetto.py
- Prova d'identita' INDIPENDENTE (temporale, non di stringa) per 16611: in tappe.csv.gz le 3 righe 'FC Taganrog' coprono 2010-2011, 2012-2015 e 2014 (tutte <=2015, coerenti con 'FC Taganrog (-2015)'), mentre le 21 righe 'Forte Taganrog'/'FC Forte Taganrog' coprono 2020-2025 e vanno a 78749. Nessuna sovrapposizione
- Verifica che il club BRW non esista nel registro (0 nomi con 'brw') e conteggio delle grafie latine attestate nella stessa fonte: 10 righe 'BRW-VIK', 8 'BRW-BIK', 2 'BRW-WIK', 1 'BRW-ВІК' -> la patch sceglie 'bik' per pura forma visiva
- Suite completa `python -m pytest -q` con la patch proposta applicata: 1.608 verdi in 394s
- Costo: `normalizza` 0,156s -> 0,284s su 31.730 nomi (fattore 1,8x)
- CONTROPROVA DI FALSO POSITIVO: con la patch proposta 'ΠΑΟΚ FC' (grafia greca vera del PAOK) diventa {'aok'} e aggancia UNIVOCO a 5219 'AOK Kerkyra' (senza patch: vuoto). Simmetricamente 'ΠΑΣ Giannina' passa da univoco 2671 'PAS Giannina' ad ASSENTE
- CONTROPROVA DI REGRESSIONE SU SCALA: 6.242 nomi misti sintetici (ogni nome del registro che aggancia univoco + una parola cirillica autentica) -> 6.242 su 6.242 passano da univoco ad assente. I token spuri prodotti ('a','c','o','ap') esistono davvero nell'indice del registro. Script: scratchpad/V9_regressione.py
- Verifica dei consumatori a valle di normalizza(): src/data/coppe_aggancio.py la usa per chiave_squadra()/chiave_partita() e per il punteggio di sovrapposizione token; le chiavi sono calcolate a runtime su entrambi i lati e non persistite, quindi non si rompono. Nessun nome di coppa e' a scrittura mista
- Verifica che gli alias non collidano: nessuna chiave di ALIAS e' a scrittura mista, quindi il dizionario self._alias e' identico prima e dopo
- Formulazione CORRETTA (de-confusione per parola) implementata e misurata: stesso identico guadagno (+1, 'FC Taganrog' -> 16611), 1 solo cambio su 74.637 nomi, collisioni 24->24, 'ВІК' non tradotto, 'ΠΑΟΚ FC' resta assente, 'ΠΑΣ Giannina' resta 2671, 110 test verdi sulle 5 suite d'aggancio. Script: scratchpad/VA_corretta.py + VB_confronto.py
- Residuo fuori perimetro misurato: player_identity.normalizza_nome('Αbdul Razak') -> {'bdul','razak'} con player_id 339560 distinto da 177321 'Abdul Razak'; allenatori.normalizza_nome('Αlexandros Maniatoglou') -> 'αlexandros maniatoglou'. La patch non li tocca
- Repo riportato pulito: `git status --short` vuoto, nessuna modifica lasciata sul disco

---

## Verifica 4

**Esito**: `confermato = True`

### Motivo

Il DIFETTO e' confermato e la conclusione «non toccare le stopword» regge (anzi, con margine piu' ampio del dichiarato). Ma la RIPARAZIONE proposta e' sbagliata nel suo punto principale, e tre numeri dell'evidenza non si riproducono.

RIPRODOTTO. (1) Nomi che perdono tutti i token: 0 nelle 8 fonti principali; 11 su 22.410 in carriere_wikipedia. (2) normalizza('Sport'/'Club'/'US'/'Calcio'/'AFC') = frozenset(). (3) LEAVE-ONE-OUT sulle 8 fonti: riferimento 804/1.019 univoci, e 'fc' -18, 'fk' -5, 'de' -4, 'ac' -3, 'sk' -3, 'ud' +3, 'cd' +2, 'sd' +2 — identici. (4) Il fallback rende ~zero: nella variante SIMMETRICA (token grezzi anche nell'indice) cambia 1 nome su 23.429 coppie ('AC Football Club' si aggancia a se stesso); 'Sport' resta assente perche' 'sport' non e' un token dell'indice nemmeno cosi'. (5) I conteggi 16/100/53/17/22 per sport/club/calcio/us/afc sono esatti.

⛔ IL DIFETTO DELLA RIPARAZIONE (misurato, non ipotizzato). La riparazione raccomandata — «un ALIAS caso per caso, come gia' fatto per 'sporting'» — e' IRREALIZZABILE E PERICOLOSA proprio per la classe di nomi che dovrebbe curare. `Agganciatore.__init__` costruisce `self._alias = {normalizza(k): normalizza(v) ...}`: per 'Sport' la chiave e' `frozenset()`, e `candidati()` fa il lookup PRIMA di controllare `if not ts`. Aggiungendo l'alias suggerito `ALIAS['Sport'] = 'Sport Club do Recife'` ho misurato: 'Sport', 'Club', 'US', 'Calcio', 'AFC', 'FC 92', 'AC Football Club', il nome cirillico del Lokomotiv, e persino `None` e `12345` tornano TUTTI [8718], etichettati «univoco» da aggancia_serie. E' esattamente la certezza sbagliata (R6) che il modulo dichiara di combattere, moltiplicata per ogni nome vuoto presente e futuro. Simmetricamente un alias il cui VALORE normalizza a vuoto non funziona affatto (ts diventa vuoto -> []). Oggi la mina e' disinnescata solo perche' nessuna chiave ALIAS normalizza a vuoto: la riparazione proposta la arma.

❌ NUMERI SBAGLIATI. (a) «987 nomi nelle 8 fonti»: misurati 896 unici (1.019 coppie fonte-nome). (b) «1 su 3.173 nel registro»: sono 2 — 'AC Football Club' (121777) e 'Футбольный клуб "Локомотив" Москва' (932). Il secondo NON e' causato dalle stopword ma dalla scrittura cirillica, ed e' l'unico caso che costa agganci VERI oggi: il club 932 non entra affatto nell'indice (`if not ts: continue`), quindi 'Lokomotiv Moscow' (250 righe), 'FC Lokomotiv Moscow' (44) e 'Lokomotiv Moskva' (1) — 295 righe di carriere_wikipedia, che passano davvero per Agganciatore in src/data/careers.py:336 — risultano «assente» mentre il club nel registro C'E'. Ne' un ALIAS ne' il fallback lo salvano. (c) L'elenco dei carriere e' invertito: 'US' NON c'e', 'Sport' SI' (la frase dice il contrario), e manca 'Сокол Обручище'. (d) «gli unici Delta positivi sono ud/cd/sd»: sono cinque, anche 'club' +1 e 'ss' +1. (e) Il comando dichiarato non riproduce i numeri dichiarati: loo.py com'e' salvato include carriere e stampa 4.720/23.429 con 'fc' a -279, non -18.

❌ IL TEST-GUARDIA, COSI' COM'E' SCRITTO, E' ROSSO AL PRIMO GIRO se `nomi_di_tutte_le_fonti()` significa davvero tutte le fonti (11 nomi in carriere + 2 nel registro); se invece si restringe alle 8 fonti principali e' vacuo oggi e non copre l'unica fonte su cui il difetto e' ATTIVO. Inoltre guarda il lato sbagliato: il costo misurato sta nel REGISTRO (club 932), che il test non tocca.

Nota d'ambiente: durante la verifica l'albero di lavoro conteneva per qualche minuto una patch di un'altra sessione (_deconfondi/_OMOGLIFI) poi ritirata; tutti i numeri qui sopra sono stati ri-misurati sul file di HEAD (md5 89efb9ea831fb9a278780577761a5e56, `git status` pulito).

### Correzione alla riparazione proposta

Tenere la conclusione («non si tocca _STOPWORD»: confermata) e buttare la ricetta ALIAS. Nell'ordine:

1. PRIMA di tutto, la GUARDIA nel codice — senza questa, il consiglio «aggiungi un ALIAS» e' una bomba a orologeria in src/data/club_matching.py:
   in `Agganciatore.__init__`:
       self._alias = {}
       for k, v in ALIAS.items():
           kt, vt = normalizza(k), normalizza(v)
           if not kt or not vt:      # 'Sport', 'Club', 'US'... -> chiave frozenset()
               raise ValueError(f"ALIAS inservibile: {k!r} -> {v!r} normalizza a vuoto: "
                                "servirebbe un token, non un alias")
           self._alias[kt] = vt
   e in `candidati`, spostare il controllo prima del lookup:
       ts = normalizza(nome)
       if not ts:
           return []
       ts = self._alias.get(ts, ts)
   con il test che rende esplicita la ragione:
       def test_un_alias_con_chiave_vuota_non_passa_in_silenzio():
           """'Sport' normalizza a frozenset(): usato come chiave, aggancerebbe
           A QUEL CLUB ogni nome che perde tutti i token (misurato 11/08/2026:
           'Club', 'US', 'AFC', il nome cirillico del Lokomotiv, e persino None)."""
           with pytest.raises(ValueError):
               Agganciatore(REGISTRO_finto_con_alias_vuoto)

2. Il test-guardia va scritto come REGRESSIONE con lista dichiarata (R4), non come assert universale — altrimenti nasce rosso — e deve coprire ANCHE il registro, dove sta l'unico costo vero:
       VUOTI_NOTI_CARRIERE = {"AFC", "AFC '34", "AFC 2", "FC 92", "FC 93", "HK",
                              "SL 16", "SL 16 FC", "Sport", "ÍF", "Сокол Обручище"}
       VUOTI_NOTI_REGISTRO = {121777: "AC Football Club",      # tre token, tutti stopword
                              932: 'Футбольный клуб "Локомотив" Москва'}  # nessuna lettera latina
       def test_nessun_NUOVO_nome_perde_tutti_i_token():
           """Un nome azzerato oggi e' indistinguibile da un nome senza aggancio.
           La lista e' l'elenco dichiarato: se cresce, serve un token, non un alias."""
       def test_ogni_club_del_registro_entra_nell_indice():
           mancanti = {cid for cid in reg.club_id} - set(Agganciatore()._per_id)
           assert mancanti == set(VUOTI_NOTI_REGISTRO)
   Le due categorie vanno tenute separate: le stopword sono UNA delle due cause, l'altra e' la scrittura non latina.

3. Aprire il caso club 932 come difetto ATTIVO, non latente: 295 righe di carriere_wikipedia ('Lokomotiv Moscow' 250, 'FC Lokomotiv Moscow' 44, 'Lokomotiv Moskva' 1) escono «assente» — cioe' dichiarano «il club non c'e' nel registro» quando c'e'. E' uno stato SBAGLIATO, non un vuoto onesto, e ne' l'ALIAS ne' il fallback lo risolvono: serve una traslitterazione del cirillico in `normalizza` (o una riga di aggancio per club_id, non per nome). Da misurare a parte, con le sue regressioni.

4. Il commento in _STOPWORD si tiene, ma con i numeri veri e il PERIMETRO dichiarato (§1.10):
   - «togliere 'fc' costa -18 univoci» -> «-18 sulle 8 fonti principali (1.019 coppie, 804 univoci di riferimento); -279 sulle 23.429 coppie che includono carriere_wikipedia — misura dell'11/08/2026, scripts di riferimento in scratchpad/VER_loo8.py»;
   - Delta positivi: cinque, non tre ('ud' +3, 'cd' +2, 'sd' +2, 'club' +1, 'ss' +1), tutti con regressioni proprie;
   - gli esempi vanno corretti: 'Sport Boys' e 'Sport Huancayo' NON esistono in club_names.csv.gz. I 16 club col token 'sport' sono Sport Club do Recife, Sport Club Internacional, Sport Club Corinthians Paulista, Football Club Lausanne-Sport, Helmond Sport, ecc.;
   - aggiungere la riga che manca e che e' l'unica azionabile: «un nome corto uguale a una di queste NON si ripara con un ALIAS — la chiave normalizzerebbe a vuoto (vedi la guardia in __init__)».

### Prove eseguite

- Ri-conteggio dei nomi vuoti: 0 su 896 unici (1.019 coppie) nelle 8 fonti principali, 11 su 22.410 in carriere_wikipedia, 2 su 3.173 nel registro — `python -c "from fonti import fonti; ..."` con src.data.club_matching di HEAD (il dichiarato diceva 987 e 1)
- Identificazione del secondo vuoto del registro: club_id 932 'Футбольный клуб \"Локомотив\" Москва', unico nome del registro senza alcuna lettera latina (`re.search('[A-Za-z]', name)`), scartato dall'indice da `if not ts: continue`
- Costo misurato del club 932: `Agganciatore().candidati('Lokomotiv Moscow'/'FC Lokomotiv Moscow'/'Lokomotiv Moskva')` = [] e 295 righe corrispondenti in data/carriere_wikipedia/tappe.csv.gz (250+44+1), fonte che passa davvero per Agganciatore (src/data/careers.py:336)
- LEAVE-ONE-OUT rifatto da zero sulle sole 8 fonti (scratchpad/VER_loo8.py): riferimento 804/1.019, 'fc' -18, 'fk' -5, 'de' -4, 'ac' -3, 'sk' -3, 'ud' +3, 'cd' +2, 'sd' +2 — riprodotti; trovati due Delta positivi NON dichiarati ('club' +1, 'ss' +1)
- Verifica che il comando dichiarato non riproduce i numeri dichiarati: `python scratchpad/loo.py` com'e' salvato stampa 4.720/23.429 univoci e 'fc' a -279 (include carriere_wikipedia)
- PROVA DECISIVA sulla riparazione: aggiunto `ALIAS['Sport']='Sport Club do Recife'` e misurato `candidati()` — 'Sport', 'Club', 'US', 'Calcio', 'AFC', 'FC 92', 'AC Football Club', il nome cirillico, None e 12345 tornano tutti [8718] «univoco», perche' la chiave dell'alias e' frozenset()
- Verifica che oggi la mina e' disinnescata: nessuna chiave ne' valore di ALIAS normalizza a vuoto, nessuna collisione fra chiavi normalizzate (misurato su tutte le 60 voci)
- Misura della variante fallback SIMMETRICA (token grezzi anche nell'indice, scratchpad/VER_fallback): 1 solo cambiamento su 23.429 coppie ('AC Football Club' -> univoco 121777); 'Sport' resta assente e il club 932 non viene salvato
- Conteggi dei token nel registro: sport 16, club 100, calcio 53, us 17, afc 22 — riprodotti esatti; ma 'Sport Boys' e 'Sport Huancayo' citati nel commento proposto NON esistono in club_names.csv.gz
- Controllo di fattibilita' del test proposto: caricare tutte le fonti costa 1,2 s (accettabile), ma su carriere+registro l'assert nascerebbe ROSSO su 13 nomi
- Controllo dell'ambiente: `git status` pulito, HEAD b9e3648, md5 del file 89efb9ea831fb9a278780577761a5e56 — una patch transitoria di un'altra sessione (_deconfondi/_OMOGLIFI) era presente durante la prima lettura ed e' stata ritirata; tutte le misure finali sono su HEAD

---

## Verifica 5

**Esito**: `confermato = True`

### Motivo

IL DIFETTO È REALE E RIPRODOTTO ESATTAMENTE. `files/player_scores/club_names.csv.gz` ha 3.173 righe e 3.173 `club_id` distinti; `Agganciatore()._per_id` ne contiene 3.171. I due esclusi sono esattamente quelli dichiarati: 932 `Футбольный клуб "Локомотив" Москва` e 121777 `AC Football Club` (`normalizza` torna `frozenset()` su entrambi: il primo perché il regex `[^a-z0-9 ]` cancella tutto il cirillico, il secondo perché ac/football/club sono tutti in `_STOPWORD`). Verificato che 932 e 121777 non sono né in `_per_id` né in `_inverso`: nessun nome può agganciarli, e la cosa non compare da nessuna parte.

L'IDENTITÀ DI 932 REGGE, e non per somiglianza di stringa (prova 4): `clubs.csv.gz` dà informazione indipendente e latina — `club_code = lokomotiv-moskau`, `url = transfermarkt.co.uk/lokomotiv-moskau/startseite/verein/932`, `stadium_name = RZD Arena` (27.084 posti), `domestic_competition_id = RU1`; in `games.csv.gz` il 932 gioca 537 partite fra RU1/RUP/RUSS/CL/EL/ELQ dal 2012 al 2025. È il Lokomotiv Mosca, non c'è dubbio. Prova 5 (è davvero assente o solo scritto diverso?): cercato con tre metodi — substring latina, substring cirillica, filtro sui nomi non-ASCII — il registro ha UNA sola riga per il Lokomotiv Mosca ed è quella cirillica; le uniche righe latine vicine sono `Lokomotiv 2 Moskow` (21507, riserve), `Lokomotiv Plovdiv` (2259), `Lokomotiv Liski` (16612), `Lokomotyv Kyiv` (27227). Anche 121777 non è una riga fantasma: gioca 2 partite di Coppa di Danimarca 2024 (game_id 4424482, 4430810).

LA VIA 2 (dichiarazione) FUNZIONA ED È SICURA: aggiunge un attributo, non tocca `candidati`/`aggancia`, zero agganci in più o in meno. Baseline verde ri-misurata: `pytest tests/test_aggancio_coppe.py tests/test_coppe_aggancio.py` → 29 passed.

MA LA PROPOSTA È INCOMPLETA SU DUE PUNTI MISURATI, ed è per questo che scrivo una correzione.

(a) La via 1 è dichiarata «a rischio nullo»: NON lo è, è un NO-OP silenzioso. Misurato: inserendo `ALIAS['Lokomotiv Moscow'] = 'Футбольный клуб "Локомотив" Москва'`, `__init__` costruisce `_alias[frozenset({'lokomotiv','moscow'})] = frozenset()`, e `candidati` esce su `if not ts: return []`. Risultato: `candidati('Lokomotiv Moscow') -> []`, identico a prima. Un alias che sembra scritto e non fa nulla è esattamente un finto pieno (R6). La proposta lo accenna in una parentesi ma lo lascia fra le opzioni sicure e non fornisce il meccanismo.

(b) Il guadagno dichiarato è FALSO in un caso misurato. La proposta dice: «senza questa dichiarazione il Lokomotiv Mosca risulterebbe assente come qualunque club che nel registro non c'è». No: con la grafia `Moskow` — che è la convenzione del registro stesso (`Lokomotiv 2 Moskow`, `Ararat Moskow`) — `aggancia('Lokomotiv Moskow')` torna **21507**, cioè la squadra RISERVE, con stato **univoco**. Non è un'assenza, è una CERTEZZA SBAGLIATA (R6), il difetto che il modulo dichiara peggiore di tutti e che `NON_AGGANCIARE` non può fermare, perché quel filtro guarda il nome IN INGRESSO, non quello nel registro. La prima squadra è invisibile mentre la sua riserva intercetta il nome della prima squadra. Le altre grafie sono innocue (misurate a vuoto: Moskau, Moskva, Mosca, Moskwa, «Loko Moscow» → tutte `[]`), ma «Moskow» no.

(c) Trappola aggiuntiva che chiude la via 1 così com'è pensata: `normalizza` scarta i token numerici (`not t.isdigit()`), quindi `Lokomotiv Moskow` e `Lokomotiv 2 Moskow` collassano sullo STESSO frozenset `{lokomotiv, moskow}`. Siccome `_alias` è indicizzato per token-set, un alias su quella chiave dirotterebbe su 932 anche il nome proprio della riserva — la stessa classe di errore in direzione opposta. Un alias per il Lokomotiv deve quindi essere chiavato sulla STRINGA GREZZA (come fa `NON_AGGANCIARE` con `nome.strip().lower()`), mai sul token-set.

### Correzione alla riparazione proposta

Adottare la via 2 (dichiarazione) COME BASE, ma corretta su tre punti; e NON adottare la via 1 nella forma proposta.

1) DICHIARAZIONE (accettata, con commento ri-calcolabile e onesto):

```python
        self.senza_token: list[tuple[int, str]] = []
        for cid, nome in zip(club_names["club_id"], club_names["name"]):
            ts = normalizza(nome)
            if not ts:
                # Il club esce dall'indice: NESSUN nome potra' mai agganciarlo.
                # Misurati 2 su 3.173 club_id del registro (3.171 in _per_id,
                # 11/08/2026):
                #  - 932  'Футбольный клуб "Локомотив" Москва': il regex
                #    [^a-z0-9 ] cancella tutto il cirillico. E' il Lokomotiv
                #    Mosca (clubs.csv.gz: club_code lokomotiv-moskau, RZD
                #    Arena, RU1; 537 partite in games.csv, 2012-2025).
                #    ⚠️ NON e' "assente": una fonte che scrive «Lokomotiv
                #    Moskow» oggi aggancia 21507 = 'Lokomotiv 2 Moskow', le
                #    RISERVE, con stato «univoco» (R6). Vedi il punto 2.
                #  - 121777 'AC Football Club': tre token, tutte sigle
                #    societarie. Club vero, 2 partite di Coppa di Danimarca
                #    2024 (game_id 4424482, 4430810), fuori dal nostro
                #    perimetro.
                self.senza_token.append((int(cid), nome))
                continue
```

2) IL PEZZO MANCANTE — chiudere il falso positivo sulle riserve, che è il rischio vero. `normalizza` scarta il '2', quindi token-set e alias NON possono separare prima squadra e riserva: la separazione deve avvenire sulla stringa grezza. Meccanismo minimo, coerente con `NON_AGGANCIARE`:

```python
# Nome (in minuscolo, grezzo) -> club_id, per i club che l'indice non puo'
# raggiungere. Si chiava sulla STRINGA, non sui token: `normalizza` scarta le
# cifre, quindi «Lokomotiv Moskow» e «Lokomotiv 2 Moskow» danno lo stesso
# insieme e un alias sui token li confonderebbe.
ALIAS_DIRETTI: dict[str, int] = {
    "lokomotiv moscow": 932,
    "lokomotiv moskow": 932,   # ⚠️ oggi va a 21507 (le RISERVE): e' il fix
    "lokomotiv moskva": 932,
    "lokomotiv moskau": 932,   # la grafia del club_code di transfermarkt
}
```
da consultare in `candidati()` SUBITO DOPO il filtro `NON_AGGANCIARE` e PRIMA di `normalizza`, tornando `[cid]`. Nessuna regressione: le quattro stringhe oggi danno `[]` tranne «lokomotiv moskow», che oggi dà una risposta SBAGLIATA (21507); `Lokomotiv 2 Moskow` non è nella mappa e continua ad agganciare correttamente 21507.
⚠️ Prima di attivarlo va deciso, e scritto, se il 932 lo vogliamo agganciabile: se la scelta è NO (nessuna fonte russa nel perimetro), allora la riga giusta è `"lokomotiv moskow"` dentro `NON_AGGANCIARE` — che comunque chiude il falso positivo, che è il punto.

3) NON inserire la coppia in `ALIAS` (via 1 come proposta): misurato, è un no-op — `_alias` mappa a `frozenset()` e `candidati` esce a mani vuote. Se si vuole tenere `ALIAS` a prova di questo, aggiungere in `__init__` una guardia esplicita:

```python
        self._alias = {}
        for k, v in ALIAS.items():
            tv = normalizza(v)
            if not tv:
                raise ValueError(f"ALIAS[{k!r}]: il valore {v!r} non ha token "
                                 "-> l'alias sarebbe un no-op silenzioso")
            self._alias[normalizza(k)] = tv
```

4) TEST da aggiungere (fissano i due numeri e il fix):
   - `len(Agganciatore().senza_token) == 2` e i due `club_id` sono `{932, 121777}`;
   - `aggancia("Lokomotiv Moskow")` NON deve tornare 21507;
   - `aggancia("Lokomotiv 2 Moskow") == 21507` (guardia contro la regressione opposta).

5) `docs/DATI.md`: la voce va scritta come «2 club_id su 3.173 non entrano nell'indice degli agganci», con i due casi, la loro identità provata e la nota che il 932 NON è un'assenza ma una trappola R6 finché la grafia «Moskow» non è chiusa.

### Prove eseguite

- Ri-calcolata l'evidenza: `normalizza` vuota su 2 nomi di 3.173 -> [(932, 'Футбольный клуб "Локомотив" Москва'), (121777, 'AC Football Club')]. Identica alla dichiarazione.
- Contati registro e indice: 3.173 righe, 3.173 club_id distinti (nessun duplicato che possa sovrascrivere `_per_id`), `len(_per_id) == 3171`. La differenza è esattamente 2. Verificato `932 in _per_id -> False`, `121777 in _per_id -> False`.
- Prova d'identità di 932 con informazione INDIPENDENTE (non somiglianza di stringa): `clubs.csv.gz` dà club_code `lokomotiv-moskau`, url transfermarkt `/verein/932`, stadio `RZD Arena` 27.084 posti, RU1; `games.csv.gz` dà 537 partite in RU1/RUP/RUSS/CL/EL/ELQ dal 2012 al 2025.
- Prova 5 ('è davvero assente o solo scritto diverso?') con tre metodi: substring latina su 'okomot|oko', substring cirillica su 'Локо|Моск', e filtro su tutti i nomi non-ASCII del registro (7 righe). Una sola riga per il Lokomotiv Mosca, ed è quella cirillica. Le vicine latine sono Lokomotiv Plovdiv (2259), Lokomotiv Liski (16612), Lokomotyv Kyiv (27227) e Lokomotiv 2 Moskow (21507, riserve).
- Identità di 121777: `games.csv.gz` -> 2 partite di Coppa di Danimarca 2024 (LKB/Gistrup 2-3 AC Football Club; AC Football Club 1-10 Naesby Boldklub). Club reale, fuori perimetro. Verificato che i suoi tre token (ac, football, club) sono tutti in `_STOPWORD`.
- PROVA 2 (la riparazione risolve o sposta il sintomo?) — la via 1 misurata sul campo: inserito `ALIAS['Lokomotiv Moscow'] = <nome cirillico>` e ricostruito l'Agganciatore. `_alias` contiene `frozenset({'lokomotiv','moscow'}) -> frozenset()`, e `candidati('Lokomotiv Moscow')` resta `[]`. La via 1 come scritta è un no-op silenzioso.
- PROVA 3 (regressione attiva) — `aggancia('Lokomotiv Moskow') -> 21507` = 'Lokomotiv 2 Moskow', le RISERVE, con stato «univoco». Idem 'Lokomotiv Moskow FC' e 'FK Lokomotiv Moskow'. Il falso positivo R6 esiste GIÀ e la dichiarazione da sola non lo tocca: smentisce il guadagno dichiarato («risulterebbe assente»).
- Misurate a vuoto le altre grafie plausibili: 'Lokomotiv Moskau', 'Lokomotiv Moskva', 'Lokomotiv Mosca', 'Lokomotiv Moskwa', 'Loko Moscow', 'FK Lokomotiv Moskau' -> tutte `[]`. Solo la grafia 'Moskow' morde.
- Verificata la trappola che chiude la via 1: `normalizza` scarta i token numerici, quindi 'Lokomotiv Moskow' e 'Lokomotiv 2 Moskow' danno lo stesso frozenset {lokomotiv, moskow}; `_alias` è indicizzato per token-set, quindi un alias lì dirotterebbe anche il nome proprio della riserva. Confermato: `candidati('Lokomotiv 2 Moskow') -> [21507]`.
- Verificato che `NON_AGGANCIARE` non può risolvere il caso: il filtro confronta `nome.strip().lower()` del nome IN INGRESSO, quindi non può impedire che un nome di prima squadra atterri sul club_id della riserva.
- Baseline dei test verde prima della modifica: `pytest tests/test_aggancio_coppe.py tests/test_coppe_aggancio.py -q` -> 29 passed. Nessun test o codice a valle legge `_per_id` per intero o conta le righe del registro (grep su tests/, src/, scripts/, docs/DATI.md): l'aggiunta dell'attributo `senza_token` è additiva e non rompe i 5 chiamanti di `Agganciatore` (careers.py, coppe_aggancio.py, aggancia_coppe.py, build_coppe_2526.py, registra_raccolta_coppa_diretta.py, fetch_wikipedia_careers.py).

---

## Verifica 6

**Esito**: `confermato = True`

### Motivo

Il difetto e' REALE e la riparazione e' GIUSTA, ma la sua motivazione scritta va corretta in due punti (vedi 'correzione').

1) EVIDENZA RIPRODOTTA IN PROPRIO (senza riusare i moduli dell'accusa).
   - `normalizza('Espanol')` = {espanol}; nel registro l'unico club che contiene il token `espanol` e' «Jove Español San Vicente» (25462) — «RCD Espanyol Barcelona» (714) normalizza a {espanyol, barcelona}, con la **y**, quindi non e' nemmeno candidato. `candidati('Espanol')` = [25462]: FINTO PIENO da manuale (R6), esito «univoco» e club sbagliato.
   - 25462 in games.csv ha **1 sola partita** (Copa del Rey); 714 ne ha 525 (456 ES1, 55 CDR, 8 EL, 6 ELQ).
   - Ricomposizione indipendente snapshot↔games.csv per (data, home_club_id, away_club_id): 16.111 partite, **15.837 ricomposte (98,30%)**, **272 coppie inesistenti**, 2 scarti di punteggio. Le 272 sono 268 La Liga + 4 Ligue 1; per squadra: 'Espanol' compare **266 volte**, tutte le altre 1-2 volte. Numeri identici a quelli dichiarati.

2) LA RIPARAZIONE RISOLVE, NON SPOSTA IL SINTOMO.
   Con l'alias: `candidati('Espanol')` = [714] e la ricomposizione passa da 15.837 a **16.103 (99,95%)**; le coppie inesistenti scendono **272 → 6**, e i 6 residui sono verificati uno per uno come slittamenti di ±1 giorno (stesse due squadre, **stesso punteggio**) — non un aggancio sbagliato. Gli scarti di punteggio restano 2 e sono i due casi R1 gia' dichiarati (Verona-Roma 19/09/2020, Union Berlin-Bochum 14/12/2024).

3) LA PROVA D'IDENTITA' NON E' UNA SOMIGLIANZA DI STRINGA (anzi: le stringhe NON si somigliano abbastanza, e' proprio quello il bug). Tre informazioni indipendenti:
   - tutte e **266** le partite ricompongono contro games.csv per data + club_id dell'avversario + **punteggio esatto**;
   - il **profilo di presenza/assenza** coincide: nello snapshot 'Espanol' c'e' in 7 stagioni su 9 (manca 2020-21 e 2023-24, retrocessione) e games.csv per il club 714 in ES1 elenca esattamente 2012-2019, 2021, 2022, 2024, 2025 — stessi due buchi;
   - una **fonte diversa** gia' agganciata (data/coppe_2526/partite.csv) scrive «RCD Espanyol Barcelona» → club_id **714** in due partite di Copa del Rey.

4) NESSUNA REGRESSIONE TROVATA, cercandola attivamente.
   - Universo di **3.637 nomi** (5 snapshot + coppe 2025-26 + squadre Smarkets + SofaScore coppe europee + registro): applicando l'alias cambia esito **1 solo nome**, 'Espanol' ([25462]→[714]). Zero nomi passano da univoco a ambiguo/assente.
   - «Jove Español San Vicente» resta correttamente [25462] (normalizza a {espanol, jove, san, vicente}, l'alias e' su token-set esatto e non lo intercetta). «Espanyol», «RCD Espanyol», «RCD Espanyol Barcelona» erano e restano [714].
   - Autotest sul registro (3.173 nomi): se-stesso 3.121 (98,36%), ambigui 50, assenti 2 — **identico** prima e dopo.
   - Nessuna collisione di chiave: le 62 chiavi ALIAS restano 62 distinte, {espanol} non era gia' presente.
   - Test con la patch **applicata al file** (poi ripristinato, repo pulito): tests/test_coppe_aggancio.py + test_careers.py + test_aggancio_coppe.py + test_player_scores.py + test_smarkets_matches.py → **141 passed**.
   - Direzione dell'alias coerente col progetto: 'Espanol' e' il nome canonico INTERNO (src/data/sources.py:164 mappa "Espanyol" → "Espanol"), quindi la mappa interno→registro sta al posto giusto, accanto alle altre abbreviazioni football-data gia' presenti.

DIFETTI TROVATI (non invalidano la riparazione, ma vanno corretti prima di scriverla):
   a) «20 squadre-stagione di Espanyol rientrano nel perimetro» **non e' ri-calcolabile ed e' falso**: nello snapshot La Liga l'Espanyol ha **7** squadre-stagione (7 × 38 = 266 partite). Il 20 non corrisponde a nessun conteggio che sia riuscito a riprodurre.
   b) il commento proposto («football-data scrive Espanyol senza la y») e' ambiguo e non nomina la vera catena: e' il nome canonico interno del progetto a essere 'Espanol'.
   c) manca dalla riparazione la nota R4 sui 6 residui: dopo il fix restano 6 coppie non ricomposte, tutte slittamenti di data — vanno dichiarate, altrimenti la sessione dopo le «ripara».

### Correzione alla riparazione proposta

La riga di codice e' GIUSTA COSI' COM'E'; vanno corretti il commento e il guadagno dichiarato.

In `src/data/club_matching.py`, dentro il blocco «Nomi ABBREVIATI di football-data per la PRIMA divisione 2025-26» (accanto a "Inter"/"Verona"):

    # ⚠️ FINTO PIENO (R6), trovato il 11/08/2026. Il nome canonico interno del
    # progetto e' «Espanol» senza la y (src/data/sources.py, TEAM_ALIASES:
    # "Espanyol" -> "Espanol"), mentre il registro scrive «RCD Espanyol
    # Barcelona»: {espanol} non pescava il club giusto ma «Jove Español San
    # Vicente» (25462, Tercera Division, UNA partita in games.csv), ed usciva
    # etichettato «univoco». Non un aggancio mancato: una certezza sbagliata.
    # Verificato con informazione indipendente, non per somiglianza di stringa:
    # (a) tutte e 266 le partite dello snapshot La Liga ricompongono contro
    #     games.csv per data + club_id avversario + punteggio esatto;
    # (b) il profilo di presenza coincide — 7 stagioni su 9, assente 2020-21 e
    #     2023-24 (retrocessione), esattamente come il club 714 in games.csv;
    # (c) data/coppe_2526/partite.csv, fonte diversa e gia' agganciata, scrive
    #     «RCD Espanyol Barcelona» -> 714.
    "Espanol": "RCD Espanyol Barcelona",

GUADAGNO, riformulato con i numeri veri:
«266 partite di La Liga (1,65% delle 16.111) smettono di puntare a un club di Tercera Division; **7** squadre-stagione dell'Espanyol (non 20) rientrano nel perimetro. Misura di controllo: la ricomposizione snapshot↔games.csv passa da 15.837/16.111 (98,30%) a 16.103/16.111 (99,95%).»

DA DICHIARARE INSIEME AL FIX (R4 — un'anomalia si dichiara anche quando NON e' un errore), altrimenti la sessione dopo prova a «ripararla»:
«Dopo l'alias restano 6 coppie non ricomposte su 16.111: sono slittamenti di +/-1 giorno fra snapshot e games.csv, con squadre e punteggio identici (Ath Madrid-Elche 29 vs 30/12/2022; Granada-Ath Bilbao 11 vs 10/12/2023; quattro partite di Ligue 1 2019-20). E restano i 2 scarti di punteggio gia' noti e gia' spiegati dalla regola R1 (Verona-Roma 19/09/2020, Union Berlin-Bochum 14/12/2024).»

ADEMPIMENTI DI CHECKLIST (§2 del CLAUDE.md) che la riparazione proposta non nomina: oltre a `docs/DATI.md`, serve un test di guardia in `tests/` che fissi il comportamento — minimo `candidati('Espanol') == [714]` e `candidati('Jove Español San Vicente') == [25462]`, perche' senza il secondo un futuro alias troppo largo passerebbe inosservato — e una voce in `docs/DIARIO.md`. NON serve nessuna correzione ai dati: gli snapshot restano intatti, quindi `data/correzioni_dichiarate.csv` (R3) non e' coinvolto.

### Prove eseguite

- Riproduzione diretta del finto pieno: `python -c "from src.data.club_matching import Agganciatore, normalizza; A=Agganciatore(); print(set(normalizza('Espanol')), A.candidati('Espanol'))"` -> {'espanol'} [25462] = «Jove Español San Vicente»; il registro scrive «RCD Espanyol Barcelona» (714), che normalizza a {espanyol, barcelona}
- Peso dei due club in files/player_scores/games.csv.gz: 25462 -> 1 partita (CDR); 714 -> 525 (ES1 456, CDR 55, EL 8, ELQ 6)
- Ricomposizione indipendente dei 5 snapshot contro games.csv per (data, home_club_id, away_club_id): PRIMA tot 16.111, ricomposte 15.837 (98,30%), coppie inesistenti 272, scarti di punteggio 2. Ripartizione: la_liga 268, ligue_1 4; 'Espanol' compare 266 volte fra le squadre coinvolte, tutte le altre 1-2
- Stessa ricomposizione con l'alias attivo: tot 16.111, ricomposte 16.103 (99,95%), coppie inesistenti 6, scarti 2 (i due casi R1 gia' noti: Verona-Roma 19/09/2020 3-0 vs 0-0, Union Berlin-Bochum 14/12/2024 0-2 vs 1-1)
- I 6 residui verificati uno per uno: sono slittamenti di +/-1 giorno con punteggio identico (Ath Madrid-Elche 29 vs 30/12/2022 2-0; Granada-Ath Bilbao 11 vs 10/12/2023 1-1; Brest-Toulouse, Marseille-Brest, Nantes-Toulouse, Rennes-St Etienne in Ligue 1 2019). Non sono agganci sbagliati
- Prova d'identita' indipendente 1 — profilo di presenza: snapshot la_liga, 'Espanol' presente in 7 stagioni su 9 (1718,1819,1920,2122,2223,2425,2526; assente 2021 e 2324, retrocessione), 38 partite ciascuna = 266; games.csv per il club 714 in ES1 elenca 2012-2019, 2021, 2022, 2024, 2025 — stessi due buchi
- Prova d'identita' indipendente 2 — fonte diversa gia' agganciata: data/coppe_2526/partite.csv contiene «RCD Espanyol Barcelona» con away_club_id = 714 in due partite di Copa del Rey
- Caccia alla regressione su un universo di 3.637 nomi (5 snapshot + coppe 2025-26 + data/squadre_smarkets_2026_27.json + SofaScore coppe europee + club_names.csv.gz): con l'alias cambia esito **1 solo nome**, ('Espanol', [25462] -> [714]); zero nomi passano da univoco a non-univoco
- Controllo di non-cattura: «Jove Español San Vicente» resta [25462] (token-set {espanol, jove, san, vicente}, l'alias e' su insieme esatto); «Espanyol» / «RCD Espanyol» / «RCD Espanyol Barcelona» restano [714] prima e dopo
- Autotest sul registro (3.173 nomi, candidati(nome) == [suo club_id]): 3.121 se-stesso (98,36%), 50 ambigui, 2 assenti — identico prima e dopo l'alias
- Collisione di chiavi ALIAS: 62 chiavi normalizzate distinte su 62 voci; frozenset({'espanol'}) non era gia' una chiave
- Test con la patch APPLICATA al file src/data/club_matching.py: `python -m pytest tests/test_coppe_aggancio.py tests/test_careers.py tests/test_aggancio_coppe.py tests/test_player_scores.py tests/test_smarkets_matches.py -q` -> 141 passed. File poi ripristinato con `git checkout`, `git status --porcelain` vuoto e candidati('Espanol') tornato [25462]
- Coerenza della direzione dell'alias: `grep -rn 'Espanol\|Espanyol' src/` mostra src/data/sources.py:164 «"Espanyol": "Espanol"» — 'Espanol' e' il nome canonico interno, quindi la mappa interno->registro va in ALIAS come le altre abbreviazioni football-data
- Verifica del guadagno dichiarato: le squadre-stagione dell'Espanyol nello snapshot sono **7**, non 20 (266 partite = 7 x 38). Il numero 20 non e' ri-calcolabile

---

## Verifica 7

**Esito**: `confermato = True`

### Motivo

Il difetto e' REALE e l'evidenza si riproduce alla cifra: su 212 nomi SofaScore, 181 univoci (85,4%), 25 assenti e 6 ambigui = 31; 677/912 partite con entrambe le squadre agganciate; 29.691/40.067 righe-giocatore. Anche le IDENTITA' sono tutte giuste: ricostruite da me indipendentemente (data +-1g + avversario gia' agganciato + punteggio esatto, in due giri perche' Aris e Radnicki hanno come avversari altri due ignoti), 31/31 con UN SOLO candidato, e il controllo pieno sui 212 nomi da' 1.818 conferme su 1.824 partite-squadra (99,7%), 0 discordi. I 6 non confermati sono esattamente le 3 finali 2026: games.csv di player-scores si ferma alle semifinali (ultima data CL 2026-05-06, EL/UCOL 2026-05-07) - R4, va dichiarato, non e' un difetto dell'aggancio. Corroborazione con informazione indipendente sui casi difficili, via stadio: SS Virtus = San Marino Stadium/Serravalle (10613 gioca CLQ+ECLQ li', NON e' Virtus Entella), Radnicki 1923 = Cika Daca (4645, non Nis), Hapoel Be'er Sheva = Varosi/Nagyerdei in Ungheria (2976, stessi stadi in games.csv), Oleksandria = Katowice/Polonia (18303), Aris = Kleanthis Vikelidis/Salonicco (605, non Limassol), Zalgiris = Vilnius (602, non Kauno). Regressione cercata attivamente e NON trovata sul grosso: su 1.273 nomi delle altre fonti del repo (5 snapshot, coppe nazionali, Smarkets, fixtures) e su 22.410 nomi-club di data/carriere_wikipedia/tappe.csv.gz, ZERO nomi oggi univoci cambiano o si perdono; pytest tests/test_careers.py tests/test_coppe_aggancio.py resta verde (50 passed) con la patch applicata. MA la riparazione e' INCOMPLETA e in un punto DANNOSA, e il guadagno dichiarato e' falso. (1) 'Feyenoord'->'Feyenoord Rotterdam' NON funziona: il registro ha DUE club che normalizzano allo stesso insieme di token, 234 'Feyenoord Rotterdam' e 2826 'SC Feyenoord Rotterdam' ('sc' e' stopword), quindi candidati('Feyenoord') resta [234, 2826] = ambiguo. (2) 'Athletic Club'->'Athletic Bilbao' crea 4 CERTEZZE SBAGLIATE (R6): la chiave dell'alias e' l'insieme normalizzato e 'club' e' stopword, quindi la chiave e' {'athletic'} e cattura anche il nome nudo 'Athletic', che in tappe.csv.gz compare 4 volte ed e' l'Athletic Club BRASILIANO (Sao Joao del-Rei) - contesto di carriera inequivocabile: Botafogo/Atl. Goianiense->Athletic, Cruzeiro->Athletic->Avai, Leixoes->Athletic, Fortuna Sittard->Athletic->Anorthosis. Quel club nel registro non esiste affatto: oggi quelle righe sono vuote (21 candidati -> None), che e' il comportamento GIUSTO secondo la regola d'oro; dopo la patch diventano Athletic Bilbao (621). (3) Di conseguenza il GUADAGNO ATTESO e' falso: i 29 alias da soli danno 209/212 nomi, 886/912 partite, 38.903/40.067 righe; con anche il fix caratteri (difetto separato) 211/212, 902/912, 39.627/40.067. Il 100% NON e' raggiungibile senza sciogliere Feyenoord.

### Correzione alla riparazione proposta

Adottare i 29 alias MENO 'Athletic Club', piu' due interventi misurati.

A) FEYENOORD - l'alias non basta, serve escludere l'omografo dal REGISTRO.
   Ne' 'Feyenoord Rotterdam' ne' 'SC Feyenoord Rotterdam' come valore risolvono:
   normalizza li porta entrambi a {'feyenoord','rotterdam'}. Aggiungere in
   club_matching.py un elenco lato-registro, gemello di NON_AGGANCIARE ma per i
   club_id (le RISERVE/AMATORI omografe della prima squadra, che il docstring del
   modulo gia' dichiara da non agganciare):
     ESCLUSI_DAL_REGISTRO: frozenset[int] = frozenset({
         2826,   # SC Feyenoord Rotterdam - la squadra amatoriale: 3 partite in
                 # tutto, tutte NLP 2014-15, contro le 629 del 234 (CL/CLQ/EL/
                 # ELQ/ECLQ/NL1/NLP/NLSC). Senza questo, 'Feyenoord' resta ambiguo
                 # perche' 'sc' e' stopword e i due nomi collassano.
         11495,  # Ajax Amateurs - stesso motivo (15 partite, solo NLP)
     })
   e filtrarlo in Agganciatore.__init__ prima di costruire l'indice.
   MISURATO: 0 regressioni su 22.410 nomi Wikipedia + 1.273 nomi delle altre
   fonti; 'Feyenoord' -> [234]. Con questo + i 28 alias + il fix caratteri si
   arriva davvero a 212/212 nomi, 912/912 partite, 40.067/40.067 righe.

B) ATHLETIC CLUB - NON metterlo nel dizionario ALIAS globale.
   La chiave e' {'athletic'} (perche' 'club' e' stopword) e vale per QUALUNQUE
   fonte: cattura le 4 righe 'Athletic' di tappe.csv.gz che sono l'Athletic Club
   brasiliano, assente dal registro. Va agganciato con un alias di FONTE, applicato
   solo ai nomi SofaScore (es. ALIAS_SOFASCORE nel loader della raccolta, oppure un
   parametro alias_extra di Agganciatore), non nel dizionario condiviso.
   Costo se lo si toglie e basta: 211/212 nomi, 904/912 partite, 39.712/40.067
   righe (l'Athletic Bilbao gioca 8 partite).

C) NUMERI DEI COMMENTI - tre conteggi dichiarati non sono ri-calcolabili
   (§2-bis pt.4): 'Sporting Braga' e' 20/20 non 19/19; 'SK Slavia Praha' 8/8 non
   7/7; 'Klaksvikar Itrottarfelag' 4/4 non 2/2. I numeri bassi sono quelli del
   PRIMO giro, prima che Feyenoord/Crvena Zvezda/Ferencvaros/Radnicki fossero
   sciolti a loro volta. Usare i conteggi a mappa completa.

D) DA DICHIARARE (R4, nel README della raccolta e in docs/DATI.md):
   - le 3 finali 2026 (PSG-Arsenal, Freiburg-Aston Villa, Crystal Palace-Rayo)
     non hanno riscontro perche' games.csv si ferma alle semifinali: sono i 6
     buchi su 1.824, non un difetto dell'aggancio;
   - nel registro il nome del 44360 e' 'Araz-Nakhchivan ' con SPAZIO FINALE
     (innocuo, normalizza fa split, ma va detto);
   - le chiavi che collassano su un token generico ({'ajax'}, {'virtus'},
     {'zalgiris'}, {'radnicki'}, {'aik'}, {'oleksandria'}, {'feyenoord'}) NON sono
     alias "di SofaScore": valgono ovunque. Effetto collaterale misurato su
     Wikipedia: 25 nomi nuovi agganciati, fra cui 'Ajax' (564 righe), 'Feyenoord'
     (399), 'AIK' (135), 'Zalgiris' (51), 'Virtus' (4). Quelli di Ajax/AIK sono
     corretti; 'Virtus'->AC Virtus Acquaviva e 'Zalgiris'->Vilnius sono
     plausibili ma NON verificati riga per riga: o si verificano, o il commento
     deve dichiarare che l'alias e' globale e non ristretto alle coppe europee.

### Prove eseguite

- Ri-calcolo dell'evidenza contro HEAD: 212 nomi distinti (Squadra+Avversario di giocatori.csv.gz), Agganciatore().candidati() -> 181 univoci (85,4%), 25 assenti, 6 ambigui. Gli elenchi coincidono nome per nome con quelli dichiarati.
- Guadagno di partenza ri-misurato: 677/912 partite con ENTRAMBE le squadre univoche e 29.691/40.067 righe-giocatore. Identici ai dichiarati.
- Ricostruzione INDIPENDENTE dell'identita' (senza usare la stringa): per ogni partita SofaScore del nome ignoto, ricerca in games.csv (season 2025, competition_id in CL/CLQ/EL/ELQ/UCOL/ECLQ) della gara a data +-1g che coinvolge l'avversario gia' agganciato DAL LATO GIUSTO e con punteggio identico -> altro club. Giro 1: 29 nomi sciolti, 1 candidato ciascuno. Giro 2 (Aris e Radnicki, i cui avversari erano a loro volta ignoti): sciolti, 1 candidato. 31/31, e i target coincidono uno per uno con quelli proposti.
- Controllo pieno sui 212 nomi con la mappa completa: 1.818 conferme su 1.824 partite-squadra (99,7%), 0 discordi. I 6 senza riscontro sono le 3 finali 2026 x 2 squadre; verificato che games.csv si ferma alle semifinali (max date CL 2026-05-06, EL e UCOL 2026-05-07).
- Corroborazione con informazione indipendente (stadio/paese) sui casi a rischio: SS Virtus -> San Marino Stadium, Serravalle (10613 ha li' le sue CLQ/ECLQ) e NON Virtus Entella; FK Radnicki 1923 -> Cika Daca (4645, non il 7567 di Nis); Hapoel Be'er Sheva -> Varosi Stadion e Nagyerdei Stadion in Ungheria, gli stessi nomi che games.csv da' al 2976; Oleksandria -> Katowice, Polonia (18303, ECLQ allo Stadion GKS Katowice); Aris Thessaloniki -> Kleanthis Vikelidis (605, GR1); FK Zalgiris -> Vilnius (602, non Kauno 40090). L'unico che lo stadio NON corrobora e' Araz Naxcivan (SofaScore 'Dalga Arena' contro 'Liv Bona Dea Arena'): li' regge solo la prova data+avversario+punteggio, 4/4.
- Applicazione della patch (29 alias) e ri-esecuzione di candidati() su ognuno: 28 danno 1 candidato, 'Feyenoord' ne da' 2 -> [234 'Feyenoord Rotterdam', 2826 'SC Feyenoord Rotterdam']. Provato anche il valore alternativo 'SC Feyenoord Rotterdam': identico, perche' 'sc' e' stopword e i due nomi hanno lo STESSO frozenset di token.
- Prova che 2826 e' la squadra amatoriale: 3 partite in games.csv, tutte competition_id NLP, stagioni 2014-2015; il 234 ne ha 629 su CL/CLQ/EL/ELQ/ECLQ/NL1/NLP/NLSC. Stessa struttura per 11495 'Ajax Amateurs' (15 partite, solo NLP) contro 610 (680 partite).
- Caccia alla regressione, fonte per fonte: raccolti 1.273 nomi di club da data/{5 leghe}_matches.csv, data/club_fixtures*.csv, data/coppe_2526/partite.csv e aggancio_squadre.csv, data/squadre_smarkets_2026_27.json, data/stagione_2026_2027/*.csv e SofaScore. Confronto candidati() prima/dopo: 0 nomi oggi univoci che cambiano o si perdono; 29 nomi passano da vuoto a univoco, di cui 1 effetto collaterale corretto ('Olympique lyonnais' della Coupe de France).
- Caccia alla regressione sul consumatore piu' grande dell'Agganciatore: 22.410 nomi-club distinti di data/carriere_wikipedia/tappe.csv.gz. 0 REGRESSIONI, ma 25 nomi passano da vuoto/ambiguo a univoco per effetto collaterale, fra cui 'Athletic' -> Athletic Bilbao.
- Diagnosi del falso positivo 'Athletic' (R5 passo 2, informazione indipendente): le 4 righe con club esattamente 'Athletic' hanno un contesto di carriera brasiliano - player 336697 Botafogo/Atletico Goianiense -> Athletic; 371967 Cruzeiro -> Athletic -> Avai; 512127 Leixoes -> Athletic; 337670 Fortuna Sittard -> Athletic -> Anorthosis. E' l'Athletic Club di Sao Joao del-Rei, che nel registro NON esiste (i 21 candidati di {'athletic'} sono tutti britannici piu' Bilbao e Raja Casablanca). Oggi restano vuote; con l'alias diventano 621.
- Matrice dei guadagni misurata: HEAD 181/212 - 677/912 - 29.691 righe; +29 alias 209/212 - 886/912 - 38.903; + fix caratteri 211/212 - 902/912 - 39.627; + esclusione 2826/11495 dal registro 212/212 - 912/912 - 40.067; senza l'alias globale 'Athletic Club' 211/212 - 904/912 - 39.712.
- Test: pytest tests/test_careers.py tests/test_coppe_aggancio.py con la patch applicata -> 50 passed. Nessuna asserzione esistente si rompe (inclusi test_club_riserve_non_si_agganciano_alla_prima_squadra e test_falsi_positivi_dellaudit_sono_corretti). File sorgente ripristinato allo stato di partenza a fine verifica.
- Verifica di collisione fra chiavi: nessuna delle 29 chiavi normalizzate coincide con un alias gia' presente ne' con un'altra nuova. Verificato inoltre che il valore 'Araz-Nakhchivan' scritto senza lo spazio finale del registro risolve comunque a [44360].

---

## Verifica 8

**Esito**: `confermato = True`

### Motivo

Il difetto esiste ed e' esattamente quello descritto: `candidati` confronta la stringa GREZZA (`nome.strip().lower() in NON_AGGANCIARE`) mentre tutto il resto del modulo lavora su token, quindi qualunque suffisso societario scavalca la guardia. Riprodotto: `Agganciatore().candidati('Red Star FC')` -> [159] Red Star Belgrade (clubs.csv: dom=SER1; games.csv: 190 partite, 60 SER1 2024-25, 40 EL, 39 CLQ, 26 CL, 25 ELQ, mai una competizione francese), mentre `'Red Star'` -> []. L'assenza a monte del Red Star di Saint-Ouen regge a TRE metodi indipendenti: nessun nome contenente «red star»/«etoile»/«ouen» in club_names.csv.gz oltre a 159; nessuno in clubs.csv.gz neppure cercando nella colonna `url`; e competitions.csv per la Francia elenca solo FR1 e FRCH — il registro non copre ne' la Ligue 2 ne' la Coupe de France, quindi il club francese non c'e' per costruzione. Le 2 righe esposte sono confermate: data/coppe_2526/partite.csv idx 270 (US Forbach, 7° turno, 2025-11-16) e 284 (ASC Biesheim, 8° turno, 2025-11-29), entrambe con divisione_ospite=2 e sigla L2.

La riparazione risolve il difetto e non ne sposta il sintomo: la guardia canonica e' un SUPERSET formale di quella attuale (verificato: `canonico(x) in BLOCCO` per tutte e 14 le voci, e nessuna voce canonicalizza a stringa vuota), conserva l'ordine dei token (blocca 'Bilbao Athletic', non 'Athletic Bilbao' -> 621), e chiude anche varianti che il proponente non ha dichiarato: 'Red Star FC 93' -> [159] e soprattutto 'US Lusitanos' e 'Lusitanos FC' -> [28958], che sono la stessa CERTEZZA sbagliata sul club andorrano (identita' del 28958 verificata con informazione indipendente: 8 partite CLQ 2012-13 e ELQ 2015-16 contro Valletta, EB/Streymur, West Ham, Domzale — un club di primo turno preliminare, non l'US Lusitanos Saint-Maur di National 2).

Regressione cercata attivamente e misurata, non assunta: scansione esaustiva di 528 file CSV/JSON sotto data/ e files/ piu' un universo di 3.996 nomi (snapshot 5 leghe tutte le stagioni, club_fixtures, coppe nazionali, aggancio_squadre diretta.it, sofascore coppe europee, squadre_smarkets_2026_27, registro): cambiano esattamente DUE esiti, 'Red Star FC' e 'FC Lusitanos'. Il costo dichiarato e' quindi reale ma vale ZERO sui dati veri: 'FC Lusitanos' compare SOLO nel registro stesso, in nessuna delle fonti. Le prime squadre restano agganciate (Real Madrid 418, Athletic Bilbao 621, Celta Vigo 940, Villarreal 1050, Sevilla 368, Barcelona 131, Atletico 13, Pirae 17782), e le forme riserve non in blocklist ('Celta Vigo B', 'Barca Atletic', 'Athletic Club B') restano vuote come oggi, quindi la fix non apre nuove ambiguita'. Suite: 1608 passed sia a HEAD sia con la patch applicata (393s / 396s).

### Correzione alla riparazione proposta

La riparazione e' giusta ma il GUADAGNO e' formulato male e l'implementazione va completata su tre punti.

1. IL GUADAGNO DICHIARATO E' SOVRASTIMATO. «2 partite di Coupe de France smettono di attribuirsi al Red Star Belgrado» e' falso oggi: quelle 2 partite NON sono attribuite a nessuno. `costruisci_coupe_de_france` (scripts/build_coppe_2526.py:324) scrive `"home_club_id": None, "away_club_id": None` per costruzione, e infatti in data/coppe_2526/partite.csv i club_id sono NaN su 201/201 righe CdF; la divisione viene dalla sigla Wikipedia (L2), non dall'aggancio. Verificato anche che il 159 non compare in NESSUN file di data/coppe_2526/. E la fonte diretta.it scrive «Red Star» (aggancio_squadre.csv riga 316 -> NaN), che la guardia gia' blocca. Il difetto e' quindi LATENTE, non materializzato: la formulazione onesta e' «2 righe di partite.csv portano un nome che darebbe una certezza sbagliata a qualunque consumatore futuro dell'agganciatore, piu' le forme US Lusitanos/Lusitanos FC/Red Star FC 93 che oggi la danno gia'». Va scritto cosi' nel diario, altrimenti si registra come corretto un errore che non era stato commesso (e la sessione dopo cerchera' nei dati un 159 che non c'e').

2. GUARDIA SULLA STRINGA VUOTA (manca in scratchpad/guardia.py). `bloccato(n)` deve essere `can = canonico(n); return bool(can) and can in _BLOCCO_CANONICO`. Motivo: `canonico` toglie stopword e cifre, quindi una voce futura in NON_AGGANCIARE fatta di sole sigle (es. "FC", "B 2") canonicalizzerebbe a "" e bloccherebbe ogni nome che canonicalizza a vuoto. Oggi nessuna voce lo fa (verificato), ma la guardia costa una riga e la blocklist e' un elenco che cresce.

3. FORMA DELLA PATCH E TEST. `canonico` va esposta come funzione pubblica del modulo accanto a `normalizza` (condividono i primi cinque passi: e' l'unico modo perche' resti vero che «la guardia vede lo stesso nome del matcher»), e `_BLOCCO_CANONICO = frozenset(canonico(x) for x in NON_AGGANCIARE)` va calcolata a livello di modulo, non dentro `candidati`. I test in tests/test_coppe_aggancio.py sono la ragione per cui il buco e' sopravvissuto: `test_omonimi_stranieri_restano_vuoti` parametrizza SOLO le forme "Red Star" e "Lusitanos", cioe' esattamente le due stringhe che il confronto grezzo copriva. Vanno aggiunte le VARIANTI ("Red Star FC", "Red Star F.C.", "Red Star FC 93", "US Lusitanos", "Lusitanos FC", "RED STAR FC") e, accanto, un test di non-regressione che fissa cio' che NON deve essere bloccato ("Athletic Bilbao"->621, "Real Madrid"->418, "Pirae"->17782, "Red Star Belgrade"->159), piu' un test che asserisce la proprieta' generale: per ogni voce della blocklist, la voce stessa e la voce con " FC" in coda danno entrambe [].

4. IL COSTO VA REGISTRATO COME ANOMALIA DICHIARATA (R4), non solo come commento. FC Lusitanos (28958) e' un club vero che perde l'aggancio dal proprio nome di registro. Misurato: non compare in nessuna fonte del progetto, quindi il costo pratico e' zero oggi. La nota nel codice deve dire questo e non «se serve, toglilo»; e se un domani servisse, la forma giusta NON e' togliere 'lusitanos' dalla blocklist (riaprirebbe US Lusitanos -> 28958) ma spostare i due omonimi stranieri da una blocklist globale a un alias negativo per-fonte, cioe' «per le fonti francesi questo nome non si aggancia», che e' l'unico posto dove l'informazione discriminante (il paese della competizione) esiste davvero.

### Prove eseguite

- Riprodotta l'evidenza a HEAD: python -c "from src.data.club_matching import Agganciatore; A=Agganciatore(); print(A.candidati('Red Star FC'), A.candidati('Red Star'), A.candidati('Red Star F.C.'))" -> [159] / [] / []. Anche 'RED STAR FC', 'Red Star Fc', 'Red Star  FC' -> [159]: il buco e' su qualunque variante, non solo quella maiuscola.
- Identita' del 159 con informazione indipendente (R5 passo 2): clubs.csv.gz dom=SER1, url transfermarkt 'roter-stern-belgrad'; games.csv.gz 190 partite raggruppate per competizione = SER1 60 (2024-25), EL 40, CLQ 39, CL 26, ELQ 25. Nessuna competizione francese, mai.
- Assenza a monte del Red Star di Saint-Ouen con TRE metodi: (a) sottostringa su club_names.csv.gz per 'red star','etoile','ouen' -> solo Red Star Belgrade; (b) stessa ricerca su clubs.csv.gz includendo la colonna url -> stesso unico risultato; (c) competitions.csv.gz country_name=='France' -> solo FR1 (ligue-1) e FRCH (trophee-des-champions): il registro non contiene ne' Ligue 2 ne' Coupe de France.
- Le 2 partite dichiarate: data/coppe_2526/partite.csv, righe 270 (US Forbach - Red Star FC, 7° turno, 2025-11-16) e 284 (ASC Biesheim - Red Star FC, 8° turno, 2025-11-29), divisione_ospite=2.0, sigla_divisione_ospite='L2'. Confermate.
- MATERIALIZZAZIONE (smentita parziale del guadagno): in partite.csv le colonne home_club_id/away_club_id sono NaN su 201/201 righe Coupe de France, perche' scripts/build_coppe_2526.py:324 le scrive None per costruzione. Scansione di tutti i CSV di data/coppe_2526/ per il valore 159 in ogni colonna *club*: zero occorrenze. Il difetto e' latente, non ha ancora sporcato un artefatto.
- Verificati gli ALTRI percorsi che potrebbero materializzarlo: livelli_divisione() scarica la seconda divisione solo per IT/EN/ES/DE (SECONDA_DIVISIONE non contiene FR), e football-data F2 2025-26 scrive comunque 'Red Star' (18 nomi scaricati e stampati), che la guardia gia' blocca; deduci_club/appaia_partite in src/data/coppe_aggancio.py passano sempre da ag.aggancia/ag.candidati, quindi sono coperti dalla stessa fix.
- REGRESSIONE, universo di 3.996 nomi (5 snapshot tutte le stagioni + club_fixtures + coppe_2526/partite.csv + aggancio_squadre.csv diretta.it + sofascore giocatori e foglio Partite + squadre_smarkets_2026_27.json + club_names.csv.gz): candidati() calcolati prima e dopo -> esattamente 2 nomi cambiano esito, 'Red Star FC' [159]->[] e 'FC Lusitanos' [28958]->[] (fonte: solo 'registro').
- REGRESSIONE, scansione ESAUSTIVA indipendente dall'universo: 528 file CSV/CSV.GZ/JSON/JSON.GZ sotto data/ e files/, ogni colonna stringa, cercando i nomi il cui canonico cade nella blocklist. Uniche voci: 'Lusitanos' e 'Sociedad B' (gia' [] oggi), 'Real Sociedad B' e i suoi contratti handicap Smarkets (gia' [] oggi), 'Red Star' (gia' []) e i contratti 'Red Star +/-x.x' dell'archivio Smarkets, che oggi danno [159] e domani [] — nomi di contratto che nessun codice passa all'agganciatore (smarkets_archive non importa club_matching).
- Batteria di 33 forme reali prima/dopo: le prime squadre restano agganciate (Real Madrid 418, Athletic Bilbao 621, Real Sociedad 681, Villarreal 1050, Sevilla 368, Barcelona 131, Celta Vigo 940, Atletico Madrid 13, Pirae 17782); le riserve non in blocklist ('Celta Vigo B', 'Barca Atletic', 'Athletic Club B', 'Castilla') danno [] sia prima sia dopo, quindi la fix non crea ne' rimuove ambiguita'; guadagno non dichiarato dal proponente: 'US Lusitanos' e 'Lusitanos FC' -> [28958] e 'Red Star FC 93' -> [159] si chiudono anch'essi.
- Prova formale che la nuova guardia e' un superset della vecchia: all(canonico(x) in BLOCCO for x in NON_AGGANCIARE) = True, e all(canonico(x) != '' ...) = True (nessuna voce attuale canonicalizza a vuoto).
- Suite completa: patch applicata a src/data/club_matching.py -> 1608 passed in 393s; git checkout e ri-esecuzione a HEAD -> 1608 passed in 396s. Nessuna regressione, e il file e' stato ripristinato (git status pulito).
- Ispezionati i test esistenti: tests/test_coppe_aggancio.py:148-149 parametrizza solo 'Red Star' e 'Lusitanos' — cioe' esattamente le due stringhe coperte dal confronto grezzo. E' la ragione per cui il buco e' sopravvissuto, e va corretto insieme al codice.

---

## Verifica 9

**Esito**: `confermato = True`

### Motivo

DIFETTO RIPRODOTTO E RIPARAZIONE CORRETTA, ma l'evidenza dichiarata e' sovra-estesa in un punto e il test proposto, come formulato, nascerebbe ROSSO.

1) DIFETTO — riprodotto identico su HEAD (89efb9e...): `normalizza('Zirə FK')` = {'zir'}, `normalizza('Ħamrun Spartans FC')` = {'amrun','spartans'}, `candidati()` = [] per entrambi. Verificato che NFKD lascia invariati U+0259 (ə), U+018F (Ə), U+0127 (ħ), U+0126 (Ħ), quindi `re.sub(r'[^a-z0-9 ]',' ')` li cancella.

2) EVIDENZA — «sono gli UNICI due caratteri-lettera che sopravvivono a NFKD» e' vera SOLO sulle 4 fonti. Censimento mio su 3.440 nomi distinti (4 fonti + registro): sul REGISTRO ne sopravvivono altri, tutti cirillici, su 3 nomi — club 932 «Футбольный клуб "Локомотив" Москва» (normalizza -> insieme VUOTO, quindi il club non entra proprio nell'indice: `Lokomotiv Moscow` da' [] ed e' un finto assente, R6), e 16611 «FС Taganrog (-2015)» / 40427 «FС Vologda (-2014)», che hanno una С CIRILLICA omoglifa al posto della C latina, per cui «fc» non viene riconosciuta come stopword e resta il token spurio 'f' nell'indice inverso. Non invalida la riparazione (nessuno dei tre e' toccato), ma invalida il test proposto.

3) LA RIPARAZIONE RISOLVE, NON SPOSTA — con la sola aggiunta delle 4 voci, su 3.440 nomi: 2 normalizzazioni cambiate (esattamente i due nomi), 2 candidati cambiati ([] -> [46710] e [] -> [17149]), indice del registro INVARIATO, 0 nomi che perdono l'univocita', 0 nuove ambiguita'. Sulle sole 212 squadre SofaScore: univoci 181 -> 183, ambigui 6 -> 6, assenti 25 -> 23. Le uniche collisioni di token create sono con i club bersaglio giusti.

4) IDENTITA' — retta da informazione indipendente, non da somiglianza di stringa. Zirə FK: SofaScore Conference League 2° turno prelim. 31.07.2025 Hajduk Split-Zirə FK <-> games.csv 2025-07-31 ECLQ Second Round 2nd leg, 447 Hajduk Split 2-1 46710 Zira FC (1/1). Ħamrun Spartans FC: 9 partite SofaScore, tutte con data + avversario + competizione identici in games.csv per il club 17149 (9/9: Maccabi Tel Aviv 05/08 e 14/08 ELQ; Jagiellonia 02/10, Lausanne 23/10, Samsunspor 06/11, Lincoln Red Imps 27/11, Shakhtar 11/12, Shamrock 18/12 UCOL).

5) LA CONVENZIONE ə->a NON E' AD HOC come dichiara l'onesta' del proponente: il registro la usa gia' sistematicamente per l'azero — «FK Sabail» (57890) da Səbail e «Kapaz PFK» (7090) da Kəpəz. Generalizza a nomi futuri, non e' scelta per far coincidere l'unico caso (ə->e darebbe zire/sebail/kepez: nessuno dei tre esiste). E ħ->h e' gia' la scelta del modulo gemello `src/data/player_identity.py`, la cui `_TRADUZIONE` contiene gia' `"ħ": "h"`: l'omissione in club_matching e' un'incoerenza fra due tabelle sorelle, non una scelta di progetto.

6) NESSUNA REGRESSIONE TROVATA — 186 test verdi sui 6 file che toccano club_matching e i normalizzatori (test_careers, test_coppe_aggancio, test_aggancio_coppe, test_smarkets_matches, test_player_identity, test_raccolta_coppa_diretta) con esattamente questo patch applicato; suite intera 1.608 verdi. Nessun artefatto congelato dipende dai due nomi: non esiste ancora una tabella di aggancio per SofaScore coppe europee, e nessun alias hard-coded per «Zirə»/«Ħamrun» esiste in scripts/, src/, tests/, docs/.

⚠️ Nota d'ambiente: durante la verifica un'altra sessione stava modificando `src/data/club_matching.py` (un tie-break `_crudo` in `candidati`, comparso e poi sparito). Tutte le misure sopra sono state rifatte in isolamento contro la copia pristina di HEAD, non contro il file di lavoro. Il working tree e' stato lasciato pulito.

### Correzione alla riparazione proposta

La riparazione va applicata COSI' COM'E' (le 4 voci in `_TRADUZIONE`), ma con tre aggiunte.

(a) IL TEST PROPOSTO VA RISCRITTO. Cosi' com'e' («fallisce se un carattere-lettera sopravvive a `normalizza`») nasce ROSSO: applicato a `club_names.csv.gz` fallisce subito su 3 nomi (932, 16611, 40427, tutti cirillici). Va scritto sulle FONTI, non sul registro, oppure sul registro con le eccezioni cirilliche dichiarate per `club_id`. Formulazione che passa:

    def test_nessuna_lettera_sopravvive_a_normalizza():
        # ogni carattere-lettera non-ASCII deve essere TRADOTTO, non cancellato
        # in silenzio: cancellarlo mutila il token (`Zirə`->`zir`) e l'aggancio
        # resta vuoto senza che nessuno se ne accorga.
        CIRILLICI_DICHIARATI = {932, 16611, 40427}   # vedi (c)
        ...
        assert superstiti == [], superstiti

    def test_schwa_e_h_maltese():
        assert normalizza("Zirə FK") == normalizza("Zira FC")
        assert normalizza("Ħamrun Spartans FC") == normalizza("Hamrun Spartans")

(b) IL COMMENTO IN TESTA AL MODULO va esteso: il secondo bug dichiarato («ø, ł, đ non sono decomposti da NFKD») e' lo stesso, e ora comprende ə/Ə (schwa azero) e ħ/Ħ (H maltese con barra). Va scritto anche che ə->a e' la convenzione GIA' USATA dal registro (FK Sabail da Səbail, Kapaz PFK da Kəpəz) e che ħ->h e' la stessa scelta di `src/data/player_identity.py`: non e' una convenzione inventata per l'unico caso presente.

(c) VANNO DICHIARATE (R4) le tre anomalie del REGISTRO trovate dal censimento, che questa riparazione NON tocca e che restano aperte:
  - club 932 «Футбольный клуб "Локомотив" Москва»: `normalizza` torna l'insieme VUOTO, quindi `Agganciatore.__init__` lo salta (`if not ts: continue`) e il club e' INVISIBILE all'indice. `candidati('Lokomotiv Moscow')` = [] — un finto assente (R6), non un'assenza a monte;
  - club 16611 «FС Taganrog (-2015)» e 40427 «FС Vologda (-2014)»: la «С» e' CIRILLICA (omoglifo), quindi «FС» non e' riconosciuta come la stopword «fc» e resta il token spurio 'f' nell'indice inverso (oggi condiviso con 537, 49018, 121775). E' esattamente la classe di errore che questa fase chiude, sull'altro lato del join.

(d) FUORI PERIMETRO ma da segnalare: la stessa famiglia di bug e' viva in altri due normalizzatori del repo — `src/data/transfermarkt.py::_TRANSLITERATE` (manca ħ, ə, œ, ŋ) e `scripts/registra_raccolta_coppa_diretta.py` — mentre `src/data/player_identity.py` ha gia' ħ ma non Ħ ne' ə/Ə. Sono nomi di GIOCATORE, non di club, quindi non vanno cambiati in questa fase, ma la disallineatura fra le quattro tabelle e' il motivo per cui il bug e' ricomparso.

### Prove eseguite

- Riprodotto il difetto su HEAD: normalizza('Zirə FK')={'zir'}, normalizza('Ħamrun Spartans FC')={'amrun','spartans'}, candidati()=[] per entrambi; verificato con unicodedata che NFKD lascia invariati U+0259/U+018F/U+0127/U+0126
- Censimento indipendente su 3.440 nomi distinti (SofaScore coppe europee, Smarkets 2026-27, coppe nazionali 2025-26, snapshot 5 leghe, registro club_names): ə e ħ sono gli unici superstiti NELLE FONTI (1 nome ciascuno), ma sul REGISTRO ce ne sono altri 3 (cirillici) — l'affermazione 'gli UNICI due' e' vera solo se ristretta alle fonti
- Diff pre/post patch su tutti i 3.440 nomi: 2 normalizzazioni cambiate, 2 candidati cambiati ([]->[46710], []->[17149]), indice del registro identico (pre_idx==post_idx), 0 nomi che passano da univoco a non-univoco
- Ricerca attiva di ambiguita' nuove: cercate le collisioni di insieme-token dopo il patch — solo 'Zira FC' e 'Hamrun Spartans', cioe' i bersagli giusti; nessun altro club del registro normalizza a {zira} o {hamrun,spartans} (verificato anche a mano su Zirka Kropyvnytskyi, UD Alzira, Gzira United, CD Zirauki, Al-Jazira)
- Resa misurata sulle sole 212 squadre SofaScore, in isolamento contro la copia pristina di HEAD: univoci 181->183, ambigui 6->6, assenti 25->23
- Prova d'identita' indipendente per Zirə FK: SofaScore 31.07.2025 Conference League 2° turno prelim. Hajduk Split-Zirə FK <-> games.csv 2025-07-31 ECLQ Second Round 2nd leg 447 (Hajduk Split) 2-1 46710 (Zira FC). 1/1 per data+avversario+competizione+turno
- Prova d'identita' indipendente per Ħamrun Spartans FC: 9 partite SofaScore 2025-26 tutte ritrovate in games.csv per il club 17149 con data, avversario e competizione identici (9/9)
- Corroborazione della convenzione ə->a: il registro usa gia' 'FK Sabail' (57890) per Səbail e 'Kapaz PFK' (7090) per Kəpəz — la traslitterazione generalizza oltre l'unico caso, non e' scelta a posteriori
- Corroborazione della convenzione ħ->h: src/data/player_identity.py::_TRADUZIONE contiene GIA' "ħ": "h" — l'omissione in club_matching e' un'incoerenza fra tabelle sorelle
- Test del test proposto: applicato al registro, 'nessun carattere-lettera sopravvive a normalizza' fallisce su 3 nomi (932 Lokomotiv Moskva in cirillico -> insieme vuoto -> club assente dall'indice; 16611 e 40427 con С cirillica omoglifa -> token spurio 'f')
- pytest con esattamente questo patch: 186 verdi sui 6 file che toccano club_matching e i normalizzatori (test_careers, test_coppe_aggancio, test_aggancio_coppe, test_smarkets_matches, test_player_identity, test_raccolta_coppa_diretta); suite intera 1.608 verdi
- Verificato che nessun artefatto congelato o alias hard-coded dipende dai due nomi: grep di 'Zir|amrun|Hamrun' in scripts/ src/ tests/ docs/ data/coppe_2526/ senza risultati, e nessuna pipeline di aggancio esistente per files/sofascore_coppe_europee_2526/

---

## Verifica 10

**Esito**: `confermato = True`

### Motivo

IL DIFETTO E' CONFERMATO alla cifra: dando all'`Agganciatore` i 3.173 nomi del suo stesso registro torna su se stesso 3.121 volte (98,36%), 50 restano ambigue, 2 assenti, 0 sbagliate — identico al dichiarato. Le 50 stanno in 24 gruppi (22 coppie + 2 terne), non 25 come scritto nella proposta: sigle societarie (UD/SD/CD Logrones, Ourense, San Fernando, Melilla, Horsens, Fredericia), cifre (Extremadura 1924, Skala 1911) o marcatori d'epoca. Sulle coppe le 6 ambiguita' della Copa del Rey ci sono e la riparazione le risolve tutte e 6 sul club_id gia' noto (346 -> 352 su 354, 0 sbagliati): ricalcolato in proprio.

MA LA RIPARAZIONE, COSI' COM'E' SCRITTA, PRODUCE UNA REGRESSIONE MISURATA, e le sue due prove non la potevano vedere.

1) L'autotest "3.121 -> 3.171 (99,94%)" e' una TAUTOLOGIA, non una validazione. La forma `crudo` e' INIETTIVA sul registro: misurato, 0 collisioni su 3.173 nomi. Uno spareggio "vince chi ha la stessa forma cruda" non puo' quindi fallire su un nome del registro — il 99,94% (= 3.173 meno i 2 assenti) e' aritmetica, non evidenza.

2) La validazione sulle coppe e' IN-DOMINIO. `casa`/`ospite` di data/coppe_2526/partite.csv sono `r.home_club_name` di games.csv (scripts/build_coppe_2526.py:191): sono le grafie di player-scores stesso. Le etichette non le produce il matcher (quello va bene), ma la prova copre solo nomi identici parola per parola a una riga del registro — cioe' l'unico caso in cui lo spareggio e' giusto per costruzione.

3) LA SCANSIONE OMETTE IL CONSUMATORE PIU' GRANDE. La proposta dichiara "zero cambi su snapshot, SofaScore e Smarkets" (verificato: 0 su tutti e cinque gli snapshot, 0 su 212 nomi SofaScore) ma non guarda `src/data/careers.py:336` (`Agganciatore().aggancia_serie`), che aggancia le carriere Wikipedia: 209.809 righe, 22.410 nomi di club. Li' lo spareggio cambia 18 nomi e 983 tappe.

4) DI QUELLE 983, 469 FINISCONO SU UN CLUB CHE ANCORA NON ESISTEVA. Il registro marca i predecessori sciolti con "(-AAAA)", e lo spareggio "vince la forma cruda uguale" sceglie sempre il SUCCESSORE: Karpaty Lviv -> 85465 (in games.csv solo 2021-2025; il vecchio 2477 e' 2012-2020) su 198 tappe su 264 chiuse prima del 2021; Kuban Krasnodar -> 67241 (2018-2025 contro 2439 2012-2017) su 69/115; Metalist Kharkiv -> 83678 (2020-2025 contro 6414 2012-2015) su 166/214; Obolon Kyiv 33/81; Spartak Tambov 3/7.

5) L'INFORMAZIONE INDIPENDENTE DICE CHE LA SCELTA E' LA MINORANZA. Sullo strato 1 (`load_careers`, club_id NATIVO di player-scores, mai toccato dal matcher), fra gli stessi giocatori che su Wikipedia hanno quel nome: 212 conferme sull'entita' VECCHIA contro 80 sulla NUOVA (Karpaty 104 vs 29, Kuban 41 vs 2, Metalist 66 vs 19). Non e' un aggancio mancato: e' una CERTEZZA SBAGLIATA dove oggi c'e' un vuoto dichiarato — esattamente il caso «Brest» gia' pagato e documentato in testa al file (R6, e la regola d'oro degli agganci).

6) Radice: 13 dei 24 gruppi ambigui (27 dei 50 nomi) sono SPACCATURE TEMPORALI, non differenze di sigla. Una stringa non puo' risolvere un'identita' temporale — serve una data. La proposta tratta i due casi come uno solo.

7) I test attuali non proteggono: con la patch applicata `tests/test_coppe_aggancio.py` e `tests/test_careers.py` passano (50 verdi in 111s). La regressione e' invisibile alla suite.

Confermo con correzione perche' il nucleo (lo spareggio a forma cruda) e' valido e il guadagno dichiarato si conserva intero una volta ristretto il perimetro — vedi 'correzione'.

### Correzione alla riparazione proposta

SPAREGGIO SI', MA MAI SU UNA SPACCATURA TEMPORALE.

(a) In `candidati()`, lo spareggio a forma cruda si applica SOLO se nessuno dei candidati porta nel registro il marcatore d'epoca `\(\s*-\s*\d{4}\s*\)`. Misurato con la guardia attiva: coppe 352/354 giusti, 0 sbagliati — il guadagno dichiarato resta INTERO, comprese tutte e 6 le ex-ambigue della Copa del Rey e le 4 di diretta.it (Ourense CF, UD Ourense, UD/SD Logrones); e le carriere Wikipedia passano da 983 tappe cambiate a 201, con le 469 assegnazioni impossibili azzerate.

(b) Restano 3 certezze sbagliate che il marcatore non copre, perche' li' il registro non l'ha messo: «Skala Stryi» (2 tappe iniziate dopo il 2017, mentre 29281 e' 2012-2017 e 86787 e' 2023-2025) e «FC Horsens» (1 tappa 2006-2012 su 77303, che in games.csv esiste solo nel 2025). La forma generale della guardia e' quindi: non spareggiare quando gli intervalli di stagione dei candidati in games.csv sono DISGIUNTI. Attenzione al costo misurato: quella forma blocca anche Extremadura UD / CD Extremadura 1924 (2013-2021 contro 2024-2025), cioe' 1 dei 6 guadagni di coppa — quindi o si tiene il marcatore sul percorso coppe, o si passa la data.

(c) La riparazione giusta per lo strato carriere non e' una stringa: e' la DATA, che li' c'e'. Con «(-AAAA)» letto come confine d'epoca piu' gli anni della tappa, 655 tappe su 681 dei 5 casi d'epoca si risolvono — piu' di quante ne risolva lo spareggio, e nel verso giusto (Karpaty 202 vecchio / 53 nuovo, Kuban 77/38, Metalist 152/49). Lo spareggio testuale non deve toccare quelle righe.

(d) Igiene: lo spareggio deve usare la forma cruda del nome DOPO la risoluzione di `ALIAS`, non del nome grezzo (oggi indifferente — misurato: 0 chiavi di ALIAS restano ambigue — ma e' un'incoerenza latente).

(e) Test da aggiungere, altrimenti la regressione resta invisibile: (i) `candidati("Kuban Krasnodar")` deve restare AMBIGUO (o risolvere a 2439 data una tappa pre-2018), idem Karpaty/Metalist/Obolon/Spartak Tambov; (ii) un test che confronta lo strato Wikipedia con il club_id nativo dello strato 1 e fallisce se il matcher assegna un club la cui finestra in games.csv non interseca la tappa; (iii) i 6 nomi di Copa del Rey devono continuare a risolvere sul club_id noto.

(f) Nel diario/README l'autotest va scritto per quello che e': con uno spareggio a uguaglianza esatta il 99,94% e' garantito dall'iniettivita' di `crudo` sul registro (0 collisioni su 3.173), non e' una misura di bonta'. La misura di bonta' e' la 352/354 sulle coppe, e va detto che copre solo nomi scritti come li scrive player-scores.

### Prove eseguite

- Autotest del registro ri-eseguito in proprio su files/player_scores/club_names.csv.gz: 3.173 nomi -> 3.121 su se stesso (98,36%), 50 ambigui, 2 assenti (932 'Локомотив' Москва, 121777 'AC Football Club'), 0 sbagliati. Coincide col dichiarato.
- Raggruppamento delle 50 ambiguita': 24 gruppi (22 coppie + 2 terne), non 25 come dichiarato; 13 gruppi / 27 nomi portano un marcatore d'epoca '(-AAAA)'.
- Iniettivita' di `crudo` sul registro: 0 collisioni fra club_id diversi su 3.173 nomi -> l'autotest post-spareggio (3.171/3.173 = 99,94%) e' garantito per costruzione, ricalcolato e riprodotto.
- Origine delle etichette della validazione coppe: data/coppe_2526/partite.csv scrive `casa` = r.home_club_name di games.csv (scripts/build_coppe_2526.py:191), quindi le 354 coppie sono grafie di player-scores stesso.
- Validazione coppe ri-eseguita: ORA 346/354 giusti 0 sbagliati 8 vuoti; CON SPAREGGIO 352/354 giusti 0 sbagliati 2 vuoti. I 6 cambi sono CD Extremadura 1924, Ourense CF, UD Ourense, SD Logrones, UD Logrones, UD San Fernando, tutti sul club_id noto.
- Scansione dei consumatori reali: snapshot 5 leghe (32/32/30/29/30 nomi) 0 cambi; SofaScore coppe europee (212 nomi) 0 cambi; diretta.it (520 nomi, tutte le raccolte) 4 cambi, tutti corretti.
- Scansione del consumatore omesso: carriere Wikipedia via src/data/careers.py (209.809 righe, 22.410 nomi) -> 18 nomi cambiati, 983 tappe di carriera coinvolte.
- Conteggio delle assegnazioni impossibili: 469 tappe finiscono su un club_id la cui prima stagione in games.csv e' successiva alla fine della tappa (Karpaty 198/264, Kuban 69/115, Metalist 166/214, Obolon 33/81, Spartak Tambov 3/7).
- Prova indipendente dallo strato 1 (club_id nativo di appearances, mai prodotto dal matcher): fra i giocatori con quel nome su Wikipedia, 212 conferme sull'entita' vecchia contro 80 sulla nuova (Karpaty 104 vs 29, Kuban 41 vs 2, Metalist 66 vs 19, Obolon 1 vs 30).
- Finestre di stagione di ogni club_id coinvolto ricalcolate da games.csv (es. 2439 = 2012-2017 vs 67241 = 2018-2025; 2477 = 2012-2020 vs 85465 = 2021-2025).
- Patch applicata davvero a src/data/club_matching.py e suite mirata eseguita: tests/test_coppe_aggancio.py + tests/test_careers.py, 50 passed in 111s -> la regressione non e' coperta da nessun test.
- Variante ristretta (nessuno spareggio se un candidato porta il marcatore d'epoca) misurata: coppe 352/354 con 0 sbagliati invariato, carriere Wikipedia da 983 a 201 tappe cambiate, 11 nomi residui.
- Variante 'intervalli disgiunti in games.csv' misurata gruppo per gruppo: cattura anche Skala Stryi ma blocca Extremadura, costando 1 dei 6 guadagni di coppa.
- Alternativa a data misurata sulle carriere: con il marcatore '(-AAAA)' e gli anni della tappa, 655 tappe su 681 dei 5 casi d'epoca si risolvono (Karpaty 202/53 con 9 residue, Kuban 77/38, Metalist 152/49 con 13, Obolon 33/44 con 4, Tambov 3/4).
- Controllo di igiene: 0 chiavi di ALIAS restano ambigue oggi, quindi l'uso della forma cruda sul nome pre-alias non ha effetto misurabile al momento.
- Stato del repo ripristinato: la patch di prova e' stata rimossa (git checkout) e la modifica non committata preesistente (le 4 traduzioni ə/ħ in _TRADUZIONE) e' stata rimessa con git stash pop.

---

## Verifica 11

**Esito**: `confermato = True`

### Motivo

Il difetto è REALE e riprodotto alla cifra: sui 96 nomi di `data/squadre_smarkets_2026_27.json`, `Agganciatore.candidati` ne lascia non-univoci esattamente 4 — 'Le Mans FC' {le,mans}, 'Lille OSC' {lille,osc}, 'Man Utd' {man,utd}, 'Nottm Forest' {forest,nottm} — cioè 92/96 = 95,8333%. Applicando i tre alias proposti la resa sale a 95/96 = 98,9583% e i tre agganci sono quelli dichiarati (985 Manchester United, 703 Nottingham Forest, 1082 LOSC Lille).

NESSUNA REGRESSIONE trovata, cercandola attivamente: ho raccolto 2.038 nomi di club da tutte le fonti che passano per l'agganciatore (snapshot delle 5 leghe, `data/coppe_2526/**`, `data/ricerca_esterna/fixtures_*`, `data/club_fixtures*`, ultimi 40 file di `data/smarkets_matches/`) e confrontato l'esito prima/dopo: cambiano SOLO i 3 nomi bersaglio ([]→[985]/[703]/[1082]), univoci 1.397→1.400, zero nomi che erano univoci e smettono di esserlo, zero nuovi ambigui. Nessuna collisione di chiave normalizzata fra i 3 alias nuovi e i 63 esistenti (verificato: `normalizza(k)` distinto per tutti). Il registro non contiene alcun club con token {lille,osc}, {man,utd} o {nottm,forest}, quindi l'alias non dirotta nulla. Test: 136 passed su tests/test_careers.py + test_coppe_aggancio.py + test_aggancio_coppe.py + test_smarkets_matches.py col patch applicato.

PROVA D'IDENTITÀ (informazione indipendente, non somiglianza di stringa): `domestic_competition_id` dei tre è GB1/GB1/FR1, coerente con la lega dichiarata da Smarkets; il controllo su tutti e 95 i nomi risolti dà club_id DISTINTI dentro ogni lega (18/20/17/20/20) e 3 sole apparenti incoerenze, tutte con dom=NaN e tutte neopromosse (64 SV 07 Elversberg, 630 Racing Santander, 990 Coventry City). L'esclusione regge: fra le 20 cartelle di `data/stagione_2026_2027/club/ENG` gli unici club con un `club_id` risolvibile non ancora preso dai 18 nomi Smarkets già agganciati sono 985 e 703; in FRA resta il solo 1082.

'Le Mans FC' è davvero un'ASSENZA A MONTE, verificata con quattro metodi indipendenti: (1) `club_names.csv.gz`, 3.173 club, contiene per 'mans' solo Mansfield Town (3820) e Sever Murmansk (16614); (2) i 3.170 nomi di club di `games.csv.gz` danno lo stesso identico insieme; (3) nessun club con `\b72\b`/MUC/'Union Club', e l'unico nome che inizia per «Le » è Le Havre AC (738); (4) le uniche competizioni francesi presenti sono FR1 e FRCH — la Ligue 2 non è coperta.

Ho verificato anche l'argomento accessorio contro la strada «togliere l'apostrofo»: è corretto che «Nott'm Forest» collasserebbe su {forest,nottm}, ma quella variante cambia i token di 14 club del registro (fra cui 64780 Atlètic Club d'Escaldes → {atletic,descaldes}, 41916 Inter Club d'Escaldes, 1189 St. Patrick's Athletic, 3031 Queen's Park). L'alias esplicito cambia 3 nomi e zero club del registro: la scelta è la più sicura delle due.

### Correzione alla riparazione proposta

La riparazione tecnica va adottata così com'è (i 3 alias in `src/data/club_matching.py`), ma DUE parti dell'istruttoria vanno riscritte perché sono false o violano una regola.

1) IL GUADAGNO DICHIARATO È FALSO — misurato, non opinione. «Restituisce Manchester United e Nottingham Forest al riconoscimento delle amichevoli in `club-friendlies`» non è vero: quel riconoscimento non passa da `club_matching`. `scripts/fetch_smarkets_matches.py::_amichevole_nostra` fa un confronto ESATTO di stringa contro l'insieme dei nomi letti dal JSON (`squadre_nostre()`), e 'Man Utd'/'Nottm Forest' sono GIÀ in quel JSON. Verificato eseguendo la funzione al codice di HEAD, senza alcun alias: `_amichevole_nostra('Man Utd vs Real Madrid')` = True, `'Nottm Forest vs Olympiacos'` = True, `'Lille OSC vs Anderlecht'` = True, e persino `'Le Mans FC vs Nantes'` = True (mentre 'Volos vs Kalamata' = False). Nessun consumatore di `squadre_smarkets_2026_27.json` istanzia `Agganciatore` (grep: gli unici utenti sono careers, coppe_aggancio, build_coppe_2526, aggancia_coppe). Formulazione corretta del guadagno: «i tre nomi Smarkets acquistano un `club_id` di player-scores, che oggi NON hanno; è la precondizione per qualunque join futuro fra il listino Smarkets e lo strato anagrafico/rosa — non la riparazione di una rottura in corso. Il perimetro delle amichevoli è già corretto oggi e resta identico dopo.»

2) LA DICHIARAZIONE DI 'Le Mans FC' NON VA MESSA NEL JSON. `data/squadre_smarkets_2026_27.json` è un file GENERATO da `scripts/costruisci_squadre_smarkets.py` e `docs/DATI.md` §5-ter-quater lo dichiara «generato, mai a mano (R3)»: una chiave aggiunta a mano verrebbe cancellata alla prima ri-esecuzione, ed è esattamente la modifica a mano che R3 vieta. Inoltre l'assenza è GIÀ dichiarata dove serve: `src/data/club_matching.py` righe 164-168 elenca «Annecy, Boulogne, Dunkerque, Grenoble, Laval, **Le Mans**, Pau, Rodez» come club di Ligue 2 che nel registro non esistono. Va solo AGGIORNATO quel commento (Le Mans non è più solo un caso di Coupe de France: dal 2026-27 Smarkets lo quota in Ligue 1) e aggiunta la riga in `docs/DATI.md`. Testo suggerito: «⚠️ 'Le Mans FC' compare fra le iscritte di Ligue 1 2026-27 secondo Smarkets ma NON esiste in `club_names.csv.gz` (3.173 club; per 'mans' solo Mansfield Town 3820 e Sever Murmansk 16614), né fra i 3.170 nomi di `games.csv.gz`, né come club francese in `clubs.csv.gz` (sole competizioni FR1/FRCH): player-scores non copre la Ligue 2, da cui il club sale. È un'assenza a monte, non un alias mancante: resta senza `club_id`, ed è l'esito giusto.»

3) PRECISIONE SULL'ESCLUSIONE (non un errore, ma va detto, R4). Nella cartella ENG i club non coperti dai 18 nomi già agganciati sono TRE, non due: oltre a manchester-united (985) e nottingham-forest (703) c'è coventry-city, che ha `nome_dataset: null` e `copertura: "assente"` — eppure il nome Smarkets 'Coventry' aggancia benissimo 990 Coventry City. Conseguenza da scrivere: `copertura: "assente"` nell'anagrafica 2026-27 NON è prova che il club manchi dal registro (Coventry è il controesempio), quindi il `nome_dataset: null` di le-mans-fc non può essere citato come prova dell'assenza. L'assenza di Le Mans regge sulle quattro ricerche dirette sul registro, ed è su quelle che va motivata.

### Prove eseguite

- RI-CALCOLO dell'evidenza: `python -c` che scorre i 96 nomi di data/squadre_smarkets_2026_27.json con Agganciatore().candidati -> 4 non univoci ('Le Mans FC', 'Lille OSC', 'Man Utd', 'Nottm Forest'), resa 95,8333%. Numero dichiarato CONFERMATO.
- Applicazione dei 3 alias e ri-misura: 1 solo non univoco ('Le Mans FC'), resa 98,9583% (95/96). Agganci: Man Utd->985, Nottm Forest->703, Lille OSC->1082, identici a quelli dei rispettivi valori d'alias.
- CACCIA ALLA REGRESSIONE: raccolti 2.038 nomi di club da snapshot 5 leghe, data/coppe_2526/**, data/ricerca_esterna/fixtures_*, data/club_fixtures*, ultimi 40 file di data/smarkets_matches. Diff candidati() prima/dopo: 3 nomi cambiati (i bersagli), 0 peggiorati, univoci 1.397 -> 1.400.
- Collisioni di chiave: normalizza(k) su tutti i 63 alias esistenti + 3 nuovi -> nessuna chiave duplicata (nessun alias silenziosamente sovrascritto).
- Ambiguita' introdotta: nessun club del registro ha token {lille,osc}, {man,utd} o {nottm,forest} (grep su club_names: 'LOSC Lille' 1082, 'Nottingham Forest' 703, 'Manchester United' 985 sono candidato unico ciascuno).
- pytest tests/test_careers.py tests/test_coppe_aggancio.py tests/test_aggancio_coppe.py tests/test_smarkets_matches.py col patch applicato: 136 passed. File poi ripristinato con git checkout (repo pulito).
- PROVA D'IDENTITA' indipendente 1 - competizione: domestic_competition_id dei tre = GB1/GB1/FR1, coerente con la lega Smarkets. Controllo su tutti i 95 risolti: 3 sole apparenti incoerenze, tutte dom=NaN e tutte neopromosse (64 SV 07 Elversberg, 630 Racing Santander, 990 Coventry City).
- PROVA D'IDENTITA' indipendente 2 - esclusione: club_id distinti per lega dopo il fix = 18/20/17/20/20 (nessun nome ruba il club di un altro); fra le cartelle di data/stagione_2026_2027/club/ENG gli unici club con club_id risolvibile non gia' preso sono 985 e 703, in FRA il solo 1082.
- ASSENZA A MONTE di Le Mans, quattro metodi: (a) club_names.csv.gz 3.173 club, regex 'mans' -> solo 3820 Mansfield Town e 16614 Sever Murmansk; (b) token normalizzati del registro contenenti 'mans' -> stessi due; (c) 3.170 nomi di club in games.csv.gz -> stessi due, e competizioni francesi presenti solo FR1 e FRCH; (d) nessun nome che inizia per 'Le ' oltre a 738 Le Havre AC, nessun '72'/'MUC'/'Union Club'.
- SMENTITA DEL GUADAGNO DICHIARATO: caricato scripts/fetch_smarkets_matches.py al codice di HEAD (senza alias) ed eseguito _amichevole_nostra -> 'Man Utd vs Real Madrid' True, 'Nottm Forest vs Olympiacos' True, 'Lille OSC vs Anderlecht' True, 'Le Mans FC vs Nantes' True, 'Volos vs Kalamata' False. Il riconoscimento delle amichevoli e' gia' corretto oggi e non passa da ALIAS.
- VERIFICA dell'alternativa scartata (togliere l'apostrofo): re-implementata normalizza con s.replace("'","") -> "Nott'm Forest" diventa {forest,nottm} come dichiarato, ma cambia i token di 14 club del registro (64780 Atletic Club d'Escaldes, 41916 Inter Club d'Escaldes, 1189 St. Patrick's Athletic, 3031 Queen's Park, 4153 L'Aquila 1927, ...). L'alias esplicito e' la strada meno invasiva: 0 club del registro toccati.

---
