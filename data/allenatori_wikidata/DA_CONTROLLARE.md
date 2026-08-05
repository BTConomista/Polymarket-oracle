# Cosa resta da controllare a mano — verifica allenatori (Fase 141)

> **A cosa serve.** Su 1.190 mandati, 896 sono confermati da Wikidata e 294
> sono stati istruiti caso per caso da un agente con ricerca esterna. Di questi
> 294, **solo 80 sono passati da uno scettico** incaricato di refutarli: le
> altre 30 refutazioni sono fallite per il limite di sessione. Questo file
> elenca ciò che resta scoperto, **in ordine di quanto conta**.
>
> Il file di lavoro è `da_controllare.csv` (294 righe, stessa priorità).

## Perché l'ordine è questo

Un verdetto che **afferma un ruolo** («questo era il vice, in carica c'era un
altro») cambia come si legge il dato. Un verdetto che **conferma** non cambia
niente: se sbagliato, lascia le cose come stanno. Quindi ciò che afferma e non
è stato ricontrollato viene prima, anche se pesa pochissime partite.

Dove lo scettico ha lavorato ha fatto cadere il **5%** dei verdetti — fra cui
uno che citava una pagina di Wikipedia a sostegno mentre quella **diceva
l'opposto**. È il tasso da tenere in mente leggendo ciò che non è stato
ricontrollato.

| priorità | cosa | mandati | partite |
|---|---|--:|--:|
| **A** | afferma un ruolo (vice/traghettatore), **mai** ricontrollato | **67** | 126 |
| **B** | confidenza dichiarata non alta | **3** | 29 |
| C | afferma un ruolo, già ricontrollato | 17 | 82 |
| D | conferma, mai ricontrollata | 155 | 3.798 |
| E | conferma, già ricontrollata | 52 | 1.844 |

## A · I 67 che affermano un ruolo e nessuno ha ricontrollato

**19 sono «vice»** — cioè i casi in cui il nostro dato ha in panchina
l'assistente e non chi era in carica. Sono i più importanti dei 67, perché sono
gli unici in cui l'attribuzione è *sbagliata* e non solo *imprecisa*:

| club | il nostro dato | data | in carica secondo la verifica |
|---|---|---|---|
| RB Leipzig | Alexander Zickler | 2024-09-14 | Marco Rose (squalifica) |
| Liverpool FC | Neil Critchley | 2020-02-04 | Jürgen Klopp |
| Bayern Munich | Peter Hermann | 2018-02-10 | Jupp Heynckes |
| Atlético de Madrid | Nelson Vivas | 2025-01-04 | Diego Simeone |
| Everton FC | Ian Woan | 2024-02-10 | Sean Dyche |
| Nottingham Forest | Rui Pedro Silva | 2024-10-21 e 2024-11-02 | Nuno Espírito Santo |
| Eintracht Frankfurt | Jan Fießer | 2025-01-23 | Dino Toppmöller |
| Hertha BSC | Mark Fotheringham | 2022-03-19 | Felix Magath |
| 1.FSV Mainz 05 | Babak Keyhanfar | 2022-01-22 | Bo Svensson |
| 1.FC Union Berlin | Babak Keyhanfar | 2024-09-14 | Bo Svensson |
| Arminia Bielefeld | Ilia Gruev | 2022-03-13 | Frank Kramer |
| FC Augsburg | Reiner Maurer | 2022-02-19 | Markus Weinzierl |
| Aston Villa | Mark Delaney | 2021-01-08 | Dean Smith |
| Brighton & Hove Albion | Björn Hamberg | 2022-01-23 | Graham Potter |
| Bologna FC 1909 | Miroslav Tanjga | 2020-07-12 | Siniša Mihajlović |
| Rayo Vallecano | Jaime Ramos | 2024-02-05 | Francisco Rodríguez |
| 1. FC Heidenheim | Bernhard Raab | 2024-05-18 | Frank Schmidt |
| FC Girondins Bordeaux | Éric Bedouet | 2018-11-11 (2g) | Ricardo Gomes |

**48 sono «traghettatore»**, quasi tutti di **una gara sola**. Qui l'interim
*era* in carica, quindi il dato non è sbagliato: manca solo la distinzione di
ruolo. Elenco completo in `da_controllare.csv` (filtra `priorita == 1` e
`ruolo == "traghettatore"`). I più lunghi: Ruthenbeck al Colonia (22 gare),
Alguacil alla Real Sociedad (9), Mike Jackson al Burnley (8), Sablé al
Saint-Étienne (7), Gallego all'Espanyol (5).

## B · I 3 a confidenza dichiarata non alta

1. **Bordeaux, Éric Bedouet, 2018-12-02 (15 gare)** — dichiarato `vice`, ma la
   nota dice che **Ricardo Gomes** guidava la squadra da *manager général*
   senza poter essere tesserato perché privo del BEPF, mentre Bédouet aveva la
   licenza. Chi era «in carica» qui dipende da cosa si intende: chi decide o
   chi è tesserato.
2. **Bordeaux, Éric Bedouet, 2018-08-19 (10 gare)** — dichiarato
   `traghettatore` dopo la sospensione di Poyet (17/08/2018).
3. **Alavés, Juan Muñiz, 2020-07-10 (4 gare)** — dichiarato `titolare`
   contro Wikidata, che sarebbe incompleta.

⚠️ **Il Bordeaux 2018-19 è il nodo più intricato del campione**: quattro
mandati di Bédouet, un verdetto già caduto in refutazione, e una situazione
(manager senza licenza + allenatore con licenza) che il nostro schema
`titolare/traghettatore/vice` non ha una casella per rappresentare. Se c'è un
posto dove vale la pena guardare per primo, è questo.

## Altri due dubbi, che non sono nell'elenco per mandato

- **`nathan jones` ha due Q-id su Wikidata** (Q10387537 per Southampton e
  Stoke, Q707158 per Luton). Ho verificato che è **una persona sola**: quindi è
  un **duplicato di Wikidata**, non un omonimo. Non tocca i nostri dati, ma se
  qualcuno ricalcola l'identità dai Q-id lo ritroverà.
- **`michel` e `luis castro`** restano gli unici due nomi del perimetro con un
  conflitto di identità dimostrato (`conflitti_identita()`). Il primo si divide
  davvero in due persone — Míchel Sánchez (Rayo, Huesca, Girona) e Míchel
  González (Málaga, Getafe); il secondo **no**: i suoi due mandati nostri sono
  la stessa persona, e la collisione del 2019 è fra una partita dentro il
  perimetro e una fuori.

## Come rieseguire la refutazione mancante

Le 30 refutazioni fallite si possono ripetere senza rifare le indagini: il
workflow rilegge dalla cache i lotti già conclusi.

```
Workflow({scriptPath: '<scratchpad>/wf_allenatori.js',
          resumeFromRunId: 'wf_e19533c6-1ac',
          args: {dir: '<scratchpad>/wf_lotti', n: 39}})
```
