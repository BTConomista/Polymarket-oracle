# Statistiche per giocatore, La Liga 2025-26 — diretta.it / Flashscore

> **Terza raccolta del progetto.** **11.953 righe giocatore-partita × 97
> statistiche**, **380 partite su 380**, 20 squadre, 599 giocatori.
> È la raccolta più ricca delle tre per righe e per giocatori.

## 1 · Provenienza

| | |
|---|---|
| **fonte** | **diretta.it (Flashscore)**, gruppo Livesport s.r.o. |
| **dato a monte** | **Opta / Stats Perform** |
| **raccolta** | **a mano dall'utente**, nessuno scraping |
| **estrazione** | 31 luglio 2026 · registrata 01/08/2026 |

**Licenza**: il progetto non rivendica alcun diritto su questi dati. Quadro
completo in `files/diretta_serie_a_2526/README.md` §1-bis. Scelta consapevole
del titolare del repo.

## 2 · Copertura

- **380/380 partite**, **760 team-partita**, 20 squadre, **599 giocatori**
- finestra: **15/08/2025 → 24/05/2026**
- **nessuna partita mancante**
- **1.024 gol** in stagione (2,69 a partita)

## 3 · ⚠️ Nessun report dell'utente per questa raccolta

Le prime due raccolte avevano un report di verifica scritto da chi ha raccolto i
dati. **Per la Liga non c'è**: il terzo file caricato il 01/08/2026 era di nuovo
il **report della Premier League**, non quello della Liga. Quindi la verifica
qui sotto è **interamente della sessione**, senza un secondo parere con cui
incrociarla — ed è giusto saperlo.

## 4 · Verifica indipendente (01/08/2026)

Stessa batteria delle altre due raccolte, più il confronto col nostro snapshot
(football-data.co.uk, **fonte diversa da diretta.it**):

| controllo | esito |
|---|---|
| **join** a `data/la_liga_matches.csv` | **760/760 = 100%** |
| **coerenza gol** (`gol giocatori + autogol avversari == risultato snapshot`) | **760/760 = 100%** |
| **11 titolari** per squadra-partita | **760/760** |
| righe duplicate | **0** |
| minuti fuori da 1-120 | **0** |
| percentuali fuori da 0-100 (15 colonne) | **0** |
| classifica ricostruita **dal file** | **20/20 con 38 partite ciascuna**; punti coerenti con V/N su tutte |
| marcatori | Mbappé 25, Muriqi 23, Budimir 17, Vinicius 16, Lamine Yamal 16 |
| assist | Lamine Yamal 11, Milla 10, Fermín 9, Güler 9 |

## 5 · Un'anomalia trovata, misurata e ridimensionata (R4)

Il controllo «squadra-partita sotto 985 minuti» — che su Serie A e Premier dava
**0 casi senza espulsione** — sulla Liga ne dava **2**: Sevilla-Villarreal
(978′) e Girona-Ath Madrid (984′).

Invece di dichiararlo un difetto della Liga, la domanda è stata **rifatta bene**
su tutte e tre le raccolte, misurando il **deficit rispetto ai 990 minuti
attesi** (11 × 90) sulle sole squadra-partita **senza espulsi**:

| deficit | squadra-partita |
|---:|---:|
| **0** | **2.077 (99,57%)** |
| 1-6 | 8 |
| 12 | 1 |

**I 9 casi sono distribuiti su tutte e tre le leghe** — 4 Serie A, 2 Premier,
3 Liga — non solo sulla Spagna. E **non è arrotondamento per sostituzione**: la
correlazione fra deficit e numero di cambi è **+0,0004**, cioè nulla.

> **Conclusione onesta**: è un'imprecisione minore nell'attribuzione dei minuti
> alla fonte, che tocca lo **0,43%** dei team-partita, con caso peggiore **12
> minuti su 990 (1,2%)**. Non è una corruzione del dato e non richiede
> correzioni. **La soglia dei 985 minuti usata dai report era arbitraria**: fa
> sembrare la Liga diversa dalle altre due, mentre il fenomeno è comune e più
> piccolo di quanto quella soglia suggerisca.

## 6 · Gli alias che sono serviti

Alla prima registrazione il join si è fermato a **420/760**: **5 nomi su 20**
seguono una convenzione diversa. Due famiglie, e vale la pena conoscerle perché
**si ripeteranno su Bundesliga e Ligue 1**:

1. **i nomi sono italianizzati** — diretta.it è l'edizione italiana di
   Flashscore: `Barcellona`, `Siviglia`, `Maiorca`. Sulle prossime leghe
   aspettarsi *Bayern Monaco*, *Colonia*, *Marsiglia*, *Lilla*;
2. **le abbreviazioni portano il punto**: `Ath. Bilbao`, `Atl. Madrid` contro i
   nostri `Ath Bilbao`, `Ath Madrid`.

I 5 alias sono entrati in `src/data/sources.py::TEAM_ALIASES`. Join: **760/760**.

## 7 · ⏱️ R8 e limiti

Identici alle altre raccolte (`files/diretta_serie_a_2526/README.md` §5-6):
tutte e 97 le statistiche sono **`post`**, si usano aggregando le partite
**precedenti** via `team_form()`, il riepilogo stagionale va usato **solo
ritardato**, e il `Rating` è un modello proprietario e non una misura.
