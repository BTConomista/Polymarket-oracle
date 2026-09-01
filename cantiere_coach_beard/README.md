# Cantiere — bundle «coach-beard-starter» (fantacalcio 2026-27)

Cartella **provvisoria**, non una destinazione finale. Contiene dati scaricati su
richiesta dell'utente il 01/09/2026 e il confronto che ne è seguito.
⚠️ **Questi dati NON sono entrati in `data/` e non devono entrarci così come sono**
(il perché è in fondo).

## Che cosa c'è

| percorso | che cos'è |
|---|---|
| `drive_file.zip` | l'**originale come consegnato** (§5-ter di CLAUDE.md): senza, un errore nostro di estrazione sarebbe indistinguibile dal dato |
| `coach-beard-starter/prd.md` | il PRD dell'app «Coach Beard», assistente per l'asta. Non è un dato: dice a cosa i dati servivano |
| `coach-beard-starter/Dati/Dati Su Giocatori, Allenatori e Squadre/Guida_Asta_202627.xlsx` | ⭐ **il pezzo che interessa**: guida all'asta, 8 fogli, 504 giocatori + 20 squadre |
| `coach-beard-starter/Dati/Listone E quotazioni/Quotazioni_Fantacalcio_Stagione_2026_27.xlsx` | il listone ufficiale: 507 giocatori + 17 ceduti, con l'**`Id` ufficiale** (l'unica chiave del bundle) |
| `coach-beard-starter/Dati/Template_Import.json` | JSON Schema: contratto di export verso Leghe Fantacalcio |
| `coach-beard-starter/Dati/{Strategie,Aste Passate}/` | **cartelle con solo un LEGGIMI**: il bundle si aspetta che le riempia l'utente |
| `CONFRONTO_con_serie_a_2025_26.md` | il documento di confronto con i nostri dati di Serie A 2025-26 |
| `confronto_panchine.py` | ri-esegue la tabella allenatori 25-26 → 26-27 (`python3 cantiere_coach_beard/confronto_panchine.py` dalla radice) |

## Provenienza (R2)

- Google Drive, file id `1R81yvpzv6ywI5XKIgef2GsDBBO7vNbH8`, titolo originale
  «coach-beard-starter 2.zip», 135.277 byte, caricato il 25/08/2026 da
  `caponelorenzo23@gmail.com`.
- sha256 dello zip: `6e8168225f52562f7071687c5f939dc8a800a6cbdfe50df37527085a60db796e`
- **Fonte del listone**: `https://www.fantacalcio.it/api/v1/Excel/prices/21/1`, letta
  dal resource fork AppleDouble dentro lo zip (`kMDItemWhereFroms`) — nel file `.xlsx`
  non c'è nessun marcatore di fonte.
- ⚠️ **La fonte della GUIDA resta ignota**: lo stesso attributo, per lei, è vuoto.
  Ed è il file che contiene le previsioni.

## Le tre cose da sapere prima di usarli

1. **È una PREVISIONE, non una misura.** Di 17 colonne del foglio Giocatori, 11 sono
   giudizi di un esperto, 2 sono misure della stagione 2025-26 (`MV`/`FMV`), 1 è
   ricostruibile dai nostri eventi (`FMV`, MAE 0,015), 1 è un aggregato di aste reali
   (`PMA`), 2 sono chiavi. Sotto la regola §5 di CLAUDE.md sono **stime di terzi**:
   non vanno nelle colonne dei dati reali.
2. **È `pre`, ed è già scaduto.** Guida estratta il 18/08/2026, listone il 19/08.
   La Serie A 2026-27 è iniziata il **23/08**: al 01/09 si erano già giocate due
   giornate. `Diff.`/`Diff.M` valgono zero su 507/507 e `Qt.A` è identica a `Qt.I`
   perché l'asta non era iniziata — sono **finti pieni con data di scadenza** (R6).
   La traiettoria 19/08 → oggi non si recupera: va ri-scaricata (§5-ter).
3. **`MV = 0` su 151 righe (30%) significa «non ha giocato», non «zero».** Misurato:
   72 degli 82 con MV=0 di squadre già in A c'erano l'anno scorso, ma con **mediana
   0 minuti**. Una media non filtrata sbaglia del 30% (4,19 contro 5,98).

## Il confronto con i nostri dati — in breve

Il documento integrale è `CONFRONTO_con_serie_a_2025_26.md`. I punti che reggono:

- **I dati sono veri, non sintetici.** 20/20 squadre coincidono con
  `data/calendari_2026_27/originali/serie_a_2026-27.csv`; le tre che escono rispetto
  alla nostra 2025-26 (Cremonese, Verona, Pisa) sono **esattamente le ultime tre**
  della classifica ricalcolata dal nostro snapshot; `FMV` si ricostruisce dai NOSTRI
  eventi 2025-26 con r = 0,9983.
- **Il join non ha una chiave.** La guida scrive il cognome, noi il nome intero in tre
  convenzioni diverse. Cinque implementazioni indipendenti danno **fra il 70% e l'80%**:
  il tasso misura quanto è aggressiva la fusione delle identità, non la sovrapposizione
  dei due dataset. Serve una tabella di alias di ~20-26 righe, scritta a mano (R3).
- ⚠️ **Otto agganci falsi e sicuri di sé** accertati (`Colombo L.` [Monza] → Lorenzo
  Colombo [Genoa] è il peggiore: anche l'iniziale coincide). Il tripwire che li prende
  tutti è la colonna `MV`: chi la guida dichiara senza dati di Serie A non può essere
  agganciato a chi in Serie A ha giocato mezza stagione.
- **La guida non è calibrata.** La somma delle `Titolarità` fa **249,79** dove gli
  undici in campo per 20 squadre ne chiedono **220** (+13,5%); 18 squadre su 20 sopra
  quota 11. I portieri invece tornano (19,86 su 20). `Titolarità` ha 5 soli valori:
  è un **ordinamento**, non una probabilità.
- **Ciò che aggiunge davvero** sono cinque colonne `pre` che il repo non ha in nessuna
  forma: `Titolarità`, `Titolare XI`, `Ballottaggio`, la gerarchia dei piazzati,
  allenatore e modulo attesi. Tutto il resto è ridondante o derivabile.

## Perché resta FUORI da `data/`

- mescola `pre`, `post` e `stima/previsione` senza una colonna che lo dica riga per
  riga (R8);
- è previsione di terzi, e §5 vuole le stime solo in `data/estimates/`, come
  probabilità — e `Titolarità` non lo è;
- è deperibile e già scaduto: un file congelato di due settimane fa è una trappola per
  la sessione successiva, che non ha modo di sapere che è vecchio.

## Che cosa deve fare un lavoro successivo

Questa cartella va **smontata**, non lasciata a decantare. In ordine:

1. **Decidere quale domanda si vuole rispondere** (§8 del confronto): validazione
   retrospettiva / inventario di ciò che manca / **feature pre-registrata per il
   2026-27**. Solo la terza rispetta R8, e va congelata prima possibile — due giornate
   sono già andate.
2. Se si sceglie la terza: congelare guida e listone con sha256 e un commit datato,
   e scorare a K = 1, 3, 5, 10, 19, 38. Il disegno del test e la sua **potenza** stanno
   in §6.3 del confronto (attenzione: l'unità indipendente è il **giocatore**, non la
   giornata — ICC 0,320, design effect 12,84 a K=38).
3. Scrivere la tabella di alias (~20-26 righe) con il registro R3.
4. Portare in `docs/DATI.md` e `docs/PISTE.md` ciò che sopravvive, e cancellare la
   cartella.

## ⚠️ Un difetto NOSTRO trovato durante questo lavoro

Non riguarda il bundle: riguarda `data/stagione_2026_2027/club/*/*/rosa_wikipedia.json`.
**Quattro file su 41 contengono la rosa di un altro club**, e sono byte-identici
all'originale sbagliato:

| file | contiene invece | n |
|---|---|---|
| `ITA/cagliari-calcio/rosa_wikipedia.json` | Associazione Calcio Milan 2026-2027 | 33 |
| `ITA/frosinone-calcio/rosa_wikipedia.json` | Associazione Calcio Milan 2026-2027 | 33 |
| `ITA/udinese-calcio/rosa_wikipedia.json` | Società Sportiva Calcio Napoli 2026-2027 | 47 |
| `ENG/newcastle/rosa_wikipedia.json` | Manchester United Football Club 2026-2027 | — |

Più due assenze: `ITA/genoa-cfc` e `ITA/venezia-fc` non hanno il file (18 su 20).
Sono file **pieni, ben formati e con la fonte dichiarata**: nessun conteggio di celle
li vede — è la famiglia R6 in purezza. La riparazione va fatta con uno script che
ri-scarica dalla voce giusta e verifica il valore-prima, più una riga in
`data/correzioni_dichiarate.csv` (R3). **Non è stata fatta**: è una decisione
dell'utente, non nostra.
