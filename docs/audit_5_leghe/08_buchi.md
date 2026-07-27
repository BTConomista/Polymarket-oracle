# Report 8 — I buchi: quanti sono, dove sono, come si chiudono

Domanda posta: *«dei dati che hai importato quanti buchi abbiamo? come potremmo
risolvere?»*

Risposta breve: **7.353 celle vuote su 612.218 (1.20%)**, ma il numero da solo
inganna. Il **99.3%** di quel vuoto è **un buco solo** — la linea Over/Under di
chiusura del 2017-19, che non esiste alla fonte per **nessuna** delle 5 leghe.
Tolto quello restano **49 celle** in tutto: lo **0.008%**.

E c'è una terza categoria, la più insidiosa: i buchi che **non appaiono come
NaN**. Uno l'ho appena trovato (§4).

---

## 1 · Il conto esatto

| lega | righe | celle | NaN totali | di cui O/U-chiusura 2017-19 | **altri** |
|---|--:|--:|--:|--:|--:|
| serie_a | 3.420 | 129.960 | 1.527 | 1.520 | **7** |
| premier_league | 3.420 | 129.960 | 1.520 | 1.520 | **0** |
| la_liga | 3.420 | 129.960 | 1.523 | 1.520 | **3** |
| bundesliga | 2.754 | 104.652 | 1.251 | 1.224 | **27** |
| ligue_1 | 3.097 | 117.686 | 1.532 | 1.520 | **12** |
| **totale** | **16.111** | **612.218** | **7.353** | **7.304** | **49** |

Nessuna **riga** manca: 380 partite per stagione ovunque, 306 in Bundesliga
(18 squadre), 306 in Ligue 1 dal 2023-24 (riforma a 18 squadre) e 279 nel
2019-20 (campionato **cancellato** per COVID, unico dei cinque a non essere
ripreso). Non è un buco d'importazione: quelle partite non si sono giocate.

---

## 2 · Il buco grosso: O/U di chiusura 2017-19 (7.304 celle, 99.3%)

**Cos'è.** Per le stagioni 2017-18 e 2018-19 football-data pubblica una sola
rilevazione O/U, e non è una chiusura: le colonne `*C*` (closing) per l'O/U
nascono nel 2019-20. Vale identicamente per tutte e 5 le leghe — nelle due nuove
la copertura è **0% nel 2017-19 e 100% da lì in poi**, esattamente come nelle tre
già in repo. È coerenza, non contagio: è la stessa fonte.

**Si può chiudere?** No, e ora so *perché* fonte per fonte (report 7 §2):
football-data è la fonte stessa; BetExplorer ha **ritirato** il confronto quote di
quelle stagioni; OddsPortal lo **vieta** nel suo `robots.txt` (`Disallow: *-2017*`);
diretta.it/Flashscore attingono allo stesso gruppo di BetExplorer; Sofascore
risponde 403 anche sul `robots.txt`. La ricerca web trova risultati e marcatori,
mai le quote storiche per singola partita.

**Cosa c'è al suo posto.** Una **stima dichiarata**, già in uso nel progetto e
validata: dalla linea O/U di **apertura** (che esiste) più il movimento medio
apertura→chiusura misurato dove entrambe esistono. Errore atteso **≈ 0.012** di
probabilità. Sta in `data/estimates/`, mai nelle colonne quota. Le due leghe
nuove **non hanno ancora la loro stima**: si genera con lo stesso script, è uno
dei passi della tranche 2.

---

## 3 · Le altre 49 celle, una per una

| lega | partita | colonne vuote | perché | recuperabile? |
|---|---|---|---|---|
| bundesliga | Leverkusen-Dortmund, Hoffenheim-RB Leipzig, Ein Frankfurt-Bayern, Bayern-Hertha, Werder-Leverkusen (2017-18), Dortmund-Wolfsburg (2018-19) | O/U apertura (12) | **svuotate da noi**: overround impossibile fino a 1.339 (report 5 §1.1) | no → **stimate**, MAE 0.0267 (`data/stime_ou_corrotte.csv`) |
| ligue_1 | Lyon-Metz, Monaco-Lyon (2017-18) | O/U apertura (4) | idem | idem |
| bundesliga | Bayern-Hoffenheim 24/08/2018 | O/U apertura (2) | **assente alla fonte** (cella vuota nel CSV originale) | stessa strada delle 8 sopra |
| bundesliga | Bayern-Hannover 04/05/2019 | 1X2 chiusura (3) | assente alla fonte (colonne Pinnacle vuote) | l'apertura c'è: sostituibile solo dichiarandolo |
| bundesliga | Union Berlin-Bochum 14/12/2024 | tiri in porta (2) | football-data non li ha per la partita interrotta e riassegnata | Understat dà 4 e 3, ma **conta i tiri in modo diverso**: registrata come *proposta non applicata* |
| bundesliga | Holstein Kiel-Bochum 09/02/2025 | xG, npxG, deep (6) | **svuotate da noi oggi**: erano un **segnaposto**, non una misura (§4) | no: la fonte non ha mai acquisito la partita |
| ligue_1 | Nantes-Toulouse 17/05/2026 | xG, npxG, ppda, deep (8) | Understat marca `isResult=false` (ultima giornata, dato non ancora consolidato) | **sì, da sola**: basta ri-scaricare quando la fonte aggiorna |
| serie_a | Torino-Fiorentina 10/01/2022 | 1X2 + O/U apertura (5) | assente alla fonte (partita rinviata per ASL) | no |
| serie_a | Verona-Genoa 19/10/2020 | O/U apertura (2) | assente alla fonte | no |
| la_liga | Alaves-Sociedad 14/10/2017 | 1X2 chiusura (3) | assente alla fonte | no |

Nessuna di queste celle è un errore d'importazione: le 10 colonne quota sono
state **ri-derivate dal grezzo con il codice di produzione** e coincidono al bit
(controllo B4, 0 differenze su 5 leghe). Dove c'è NaN, alla fonte c'è il vuoto —
o ce l'abbiamo messo noi, con motivo scritto nel registro.

---

## 4 · I buchi che NON sono NaN (la categoria pericolosa)

Un buco dichiarato è innocuo: si vede e si gestisce. Il problema sono i buchi
**travestiti da dato**. Cercarli era il senso dell'audit avversariale; oggi ne è
emerso uno nuovo, e la ricerca è stata estesa.

**4.1 · xG segnaposto — trovato e chiuso.** Holstein Kiel-Bochum 09/02/2025
portava `xG 2.0 / 2.0`: plausibile, e **identico alla fonte** — nessun confronto
snapshot↔fonte poteva accorgersene. Ma la lista tiro-per-tiro di Understat
(`getMatchData/27930`) è **vuota su entrambi i lati**, mentre football-data conta
3+6 tiri in porta. La fonte non ha mai acquisito la partita e ha scritto valori
di comodo: xG = gol esatti, npxG = gol meno un rigore forfettario, ppda `att=0
def=0`, deep 0, previsione 0/1/0. Le sei celle sono ora **NaN dichiarato**
(registro); il modello scarta le righe senza segnale secondario, quindi la
partita continua a contare nel modello-gol. Il controllo che lo intercetta
(`check_xg_segnaposto`) è nell'audit: **1 segnaposto su 16.111 partite**, gli
altri 3 candidati verificati e legittimi. Dopo la correzione: **0**.

**4.2 · `midweek_europe` = 0 quando invece si giocava.** Il calendario di club
viene da openfootball, che non copre tutto. Numeri esatti dai file del cantiere:

| lacuna | dove | effetto |
|---|---|---|
| Europa/Conference League 2025-26 | **tutte e 5 le leghe** | falso 0 per i club impegnati in EL/Conference nella stagione in corso |
| DFB-Pokal 2016-17 e 2017-18 | bundesliga | riposo sovrastimato per chi giocava la coppa nazionale |
| Coupe de France, tutte le stagioni tranne 2024-25 | ligue_1 | idem |

Non è un NaN: è uno **0 che sembra un'informazione**. Si chiude solo aggiungendo
le fonti mancanti (le competizioni esistono, i file no). Fino ad allora va
dichiarato — cosa che le variabili di congestione, già misurate come **rumore**
nelle analisi precedenti, rendono poco urgente ma non meno vero.

**4.3 · Cosa è stato cercato e NON c'era.** Simmetria d'onestà: impronte-quota
duplicate 0, riposo incoerente col calendario 0, tiri in porta > tiri 0, valore
rosa non costante per (squadra, stagione) 0, squadre con due gare lo stesso
giorno 0, xG impossibili 0 (autogol verificati uno per uno).

---

## 5 · Come si chiudono, in ordine di rapporto valore/costo

| # | buco | come | costo | vale la pena? |
|---|---|---|---|---|
| 1 | Nantes-Toulouse xG | ri-scaricare Understat quando consolida | ~0 | **sì**, si chiude da solo |
| 2 | O/U chiusura 2017-19 delle 2 leghe nuove | generare la stima dichiarata con lo script esistente | basso | **sì** — è un passo della tranche 2 |
| 3 | 9 linee O/U di apertura corrotte/assenti | stima già prodotta (MAE 0.0267 vs 0.0743 baseline) | fatto | **sì**, già fatto |
| 4 | tiri in porta Union-Bochum | decidere se accettare la convenzione Understat | decisione, non lavoro | **da decidere** (oggi: proposta non applicata) |
| 5 | coppe nazionali + EL/Conference mancanti | trovare e integrare altre fonti calendario | medio-alto | **no per ora**: la congestione è già risultata rumore |
| 6 | O/U chiusura 2017-19 *reale* | non esiste strada legale/tecnica | ∞ | **no**, chiuso con prova (report 7 §2) |

**La conclusione onesta.** Al netto di un buco sistemico che nessuno può chiudere
e che è già coperto da una stima validata, i dati importati sono **completi allo
0.008% di celle vuote**, e ogni singola cella vuota ha un nome, una causa e una
riga di registro. Il rischio residuo non è il vuoto: è il **finto pieno** — ed è
per questo che il controllo del §4.1 vale più di tutte le 49 celle messe insieme.
