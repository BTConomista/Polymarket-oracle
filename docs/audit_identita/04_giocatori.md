# L identita dei giocatori

> Dominio come dichiarato dall'agente: **L'identita' dei giocatori: i ponti fra le statistiche giocatore-partita (diretta.it, coppe nazionali, SofaScore coppe europee) e il `player_id` del database carriere.**

> 8 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

Il claim di CLAUDE.md e' VERO e riproducibile alla riga: 54.270/54.303, 33 scoperte, 22 della partita interrotta Nantes-Tolosa 17/05/2026 e 11 di 6 giocatori assenti a monte. Ma e' vero su un perimetro che il numero non dichiara — `load_player_matches` filtra `solo_campionato=True`, e le 189 righe di spareggio Bundesliga/Ligue 1 restano fuori dal conteggio e agganciate 0 su 189. Il problema vero di questo dominio non e' la copertura: e' che la copertura e' l'unica cosa che qualcuno stia misurando. Il ponte diretta.it e' quasi perfetto ma ha 4 righe attribuite alla persona sbagliata (un Kiko portoghese del Moreirense al posto di Kiko Femenia del Getafe), e il test che avrebbe dovuto proteggere proprio da quello asserisce il valore sbagliato: il bug e' verde in pytest. Due controlli indipendenti — club della presenza e competizione della presenza — convergono sulle stesse 4 righe e nessun conteggio di celle piene le vede, perche' un id sbagliato e' pieno quanto uno giusto. Gli altri due difetti sono della stessa famiglia R6: una colonna chiamata `id_diretta` dentro `aggancio_giocatori.csv` che contiene l'ID della PARTITA, e l'`ID giocatore` di SofaScore che collide numericamente con 159 dei nostri `player_id` sbagliando tutte e 159 le volte.

---

## 1. Quattro righe agganciate alla persona sbagliata: il Kiko del Moreirense al posto di Kiko Femenia

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/player_identity.py`, `tests/test_player_identity.py`

### Evidenza

4 righe su 54.270 (0,0074%). Le righe La Liga 'Kiko'/Getafe del 13/09/2025, 27/09/2025, 21/03/2026 e 25/04/2026 portano player_id=934031 = 'Kiko', nato 2002-04-16, che nel 2025-26 ha 27 presenze e TUTTE in PO1 col Moreirense FC (club 979), mai al Getafe (club 3709). Due controlli indipendenti convergono sulle stesse 4 righe: purezza del club per squadra (Getafe 0,992895, unica delle 96 squadre sotto 1) e competizione della presenza (4 righe la_liga la cui presenza player-scores e' in PO1). Informazione indipendente (R5): in tutte e 4 le date diretta.it elenca UNA sola riga 'Kiko' per il Getafe, e player-scores registra Kiko Femenia (76467) in campo in tutte e 4. La causa e' nel passo 1 di `collega()`: la chiave (data, token) non vincola la competizione, e {kiko} e' univoco su quella data perche' Femenia nell'anagrafica si chiama 'Kiko Femenia' = {kiko, femenia}, cioe' una chiave diversa. Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/h_purezza.py e .../f_kiko.py

### Riparazione proposta

Restringere le presenze da cui si costruisce la tabella di aggancio alla competizione della lega: aggiungere a `tabella_aggancio()` e `collega()` un parametro `competizioni=None` che filtra `appearances['competition_id']`, e passargli la competizione dedotta dalla colonna `lega` (serie_a->IT1, premier_league->GB1, la_liga->ES1, bundesliga->L1, ligue_1->FR1). E' sicuro per costruzione: filtrare riduce i candidati, quindi puo' solo trasformare una chiave ambigua in univoca, mai il contrario. MISURATO simulando la riparazione (.../i_fix.py): passo 1 sale da 51.849 a 51.922 righe (+73), il totale finale resta identico a 54.270/54.303 con le stesse 33 scoperte, e le 28 righe 'Kiko' vanno tutte e sole su 76467 con 0 scoperte. Le 54.266 righe oggi corrette hanno tutte la presenza nella competizione attesa, quindi il filtro non ne perde nessuna.

### Guadagno atteso

4 righe da persona sbagliata a persona giusta, e +73 righe agganciate gia' al passo 1 (che oggi l'eliminazione recupera, ma per una via piu' fragile). Soprattutto: chiude la classe di errore, non il caso — oggi vale 4 righe perche' un solo giocatore delle 5 leghe ha un omonimo esatto attivo altrove lo stesso giorno.

---

## 2. Il test che doveva proteggere dall'errore lo asserisce: `test_omonimi_veri_restano_distinti` e' verde grazie al bug

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `tests/test_player_identity.py`

### Evidenza

tests/test_player_identity.py:196-214 asserisce `sub['player_id'].nunique() == 2` per il nome 'Kiko', con la docstring «Al Getafe giocano due Kiko (Femenia 1991 e Kiko 2002)». Misurato: al Getafe gioca UN Kiko. Il secondo player_id (934031) e' il Kiko del Moreirense, e le sue 4 righe sono il falso positivo del difetto precedente. Il test passa oggi e FALLIREBBE dopo la riparazione corretta — cioe' e' orientato al contrario. Ricalcolo del fatto: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/g_kiko2.py (mostra 1 riga 'Kiko' per partita e Kiko Femenia presente in tutte e 4 le date).

### Riparazione proposta

Sostituire il caso 'Kiko' con un omonimo VERO e verificato: nelle 5 leghe 2025-26 ce ne sono quattro misurati, tutti gia' distinti correttamente dal ponte — 'Vitinha' (487469 Paris SG nato 2000-02-13 / 586853 Genoa nato 2000-03-15, 64 righe), 'Lopez David' (129444 Girona 1989 / 947431 Mallorca 2003, 20 righe), 'Gueye Idrissa' (126665 Everton 1989 / 1178488 Metz-Udinese 2006, 47 righe), 'Gonzalez Nicolas' (466805 Man City 2002 / 486031 Ath Madrid-Juventus 1998, 51 righe). Su 'Kiko' l'asserzione giusta e' `nunique() == 1`. Aggiungere inoltre il test che il conteggio non poteva fare: nessuna riga agganciata deve avere la presenza player-scores in una competizione diversa da quella della sua lega (oggi: 4, dopo la riparazione: 0).

### Guadagno atteso

Il difetto smette di essere invisibile. Oggi la suite verifica la copertura (quante righe hanno un id) e non la correttezza (se e' l'id giusto): il controllo di competizione e' la guardia che manca, e costa una riga.

---

## 3. 189 righe di spareggio fuori dal ponte e fuori dal numero dichiarato

**categoria** `assenza-a-monte` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `CLAUDE.md`, `README.md`, `tests/test_player_identity.py`, `docs/DATI.md`

### Evidenza

`load_player_matches(tutte=True)` usa `solo_campionato=True` di default, quindi il 54.303 del claim NON include le partite fuori campionato. Con `solo_campionato=False` le righe sono 54.492: 62 dello Spareggio Bundesliga e 127 del Play Off retrocessione Ligue 1. Il ponte le aggancia 0 su 189, sia lanciato su di esse sole sia sull'intero dataset (quindi non e' un artefatto della mappa club dedotta). La causa e' a monte ed e' dimostrata dalle date: il 25/05, 26/05 e 29/05/2026 player-scores non ha NESSUNA presenza, in nessuna competizione; il 12/05, 15/05 e 21/05 ne ha ma solo di ES1/UKR1/GB1/POBE/TR1/EJPL. Le 48 competizioni della fonte non includono gli spareggi promozione/retrocessione. Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/c_spareggi2.py

### Riparazione proposta

Non e' riparabile come aggancio — il dato non esiste nella fonte. E' riparabile come DICHIARAZIONE, ed e' li' che serve: la frase «ponte d'identita' 54.270/54.303» va scritta col suo perimetro, «54.270/54.303 righe di campionato; le 189 righe di spareggio non sono agganciate perche' player-scores non copre quelle competizioni». Stesso trattamento in `test_copertura_del_ponte_su_tutte_le_raccolte`, che oggi misura solo il ramo `solo_campionato=True`: aggiungere il ramo `solo_campionato=False` con l'atteso 54.270/54.492 e la causa nominata, cosi' che una raccolta futura che perdesse righe di spareggio si veda invece di restare sotto la soglia.

### Guadagno atteso

Il numero smette di essere vero-ma-parziale. Oggi 189 righe non sono agganciate e nessun documento del progetto lo dice, perche' il default del caricatore le nasconde prima che qualcuno le conti.

---

## 4. `id_diretta` in aggancio_giocatori.csv non e' l'id del giocatore: e' l'id della PARTITA

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `True`

**File**: `scripts/aggancia_coppe.py`, `data/coppe_2526/aggancio_giocatori.csv`, `data/coppe_2526/README.md`

### Evidenza

data/coppe_2526/aggancio_giocatori.csv ha `id_diretta` pieno al 100% (18.307/18.307) ma con soli 442 valori distinti contro 8.857 nomi distinti. 419 dei 442 mappano a >1 player_id; 4.156 player_id su 8.153 stanno sotto piu' di un `id_diretta`. Prova diretta: ognuno dei 442 valori copre esattamente 2 squadre, mediana 40 righe di formazione (min 35, max 52), e tutti e 442 compaiono nella colonna `id_diretta` di aggancio_partite.csv, che e' per definizione l'id partita. L'origine e' scripts/aggancia_coppe.py:232, che rinomina `ID partita` in `id_diretta` dentro la tabella dei giocatori. Il codice la usa correttamente come chiave composta (id_diretta, nome) — riga 238 — quindi oggi non c'e' danno a valle: il difetto e' il NOME, e non e' documentato da nessuna parte (0 occorrenze di `id_diretta` nel README delle coppe e in docs/). Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/q_iddiretta.py

### Riparazione proposta

Rinominare la colonna in `id_partita_diretta` in scripts/aggancia_coppe.py (riga 232, il rename di output della tabella giocatori) e rigenerare data/coppe_2526/aggancio_giocatori.csv con lo script, non a mano (R3). Documentarla nel README di data/coppe_2526/ insieme alle altre colonne di aggancio. Se si preferisce non toccare il file gia' versionato, il minimo indispensabile e' la riga di documentazione: una colonna che si chiama come un id giocatore in una tabella di giocatori, e non lo e', e' esattamente il caso che R6 descrive.

### Guadagno atteso

Chiude una trappola latente che costa ~40 persone collassate su un id al primo che la usi come chiave giocatore — cioe' il modo esatto in cui il progetto ha gia' pagato «Hellas Verona», ma su un id invece che su un nome, quindi ancora meno visibile.

---

## 5. L'`ID giocatore` di SofaScore collide con 159 dei nostri player_id, e sbaglia tutte e 159 le volte

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `False`

**File**: `src/data/player_identity.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

files/sofascore_coppe_europee_2526/giocatori.csv.gz ha `ID giocatore` int64, pieno 40.067/40.067, 6.024 valori distinti nell'intervallo 1.076-2.644.287 — cioe' lo STESSO ordine di grandezza dei nostri player_id (50.149 valori in players.csv.gz). 159 dei 6.024 id SofaScore esistono anche come player_id nostro. Di questi 159, quanti hanno anche un nome compatibile (almeno un token in comune dopo normalizzazione)? ZERO. Un `merge(left_on='ID giocatore', right_on='player_id')` produce quindi 159 accoppiamenti, tutti sbagliati, e si presenta come «copertura bassa, manca il dato» invece che come «join rotto». Nota positiva sulla fonte: l'id SofaScore e' internamente sano — 0 id sotto piu' di un nome, e i 19 nomi sotto piu' di un id sono omonimi veri, separati dalla data di nascita (Joao Pedro ha 3 id con 3 date diverse). Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/j_sofa.py

### Riparazione proposta

Non costruire il ponte sull'id (spazi di identificatori diversi e disgiunti nei fatti). Il metodo che funziona, MISURATO, e' (data di nascita, insieme dei token del nome) con argmax stretto sui token a parita' di data — la stessa forma del ponte diretta.it, ma con la data di NASCITA al posto della data della partita, perche' qui i due dataset non condividono un calendario affidabile: SofaScore ha `Data di nascita` su 6.020 dei 6.024 giocatori, players.csv.gz su 50.100 su 50.149. Resa misurata (.../k_sofaponte.py): 4.242 dei 6.020 agganciati univocamente, 2 soli ambigui (da lasciare vuoti, regola d'oro), 29 senza nessun nato quel giorno e 1.747 con la data ma nome incompatibile; copre 31.537 righe giocatore-partita su 40.067 (78,7%). Sulla parte che ci riguarda: 1.491 giocatori delle nostre 5 leghe, 13.288 righe. PUREZZA validata con informazione indipendente (.../l_purezzasofa.py e .../n_percomp.py): su chi ha minuti>0, la presenza player-scores nella stessa data conferma il 95,75% in Champions [IC95 0,9527-0,9624] e il 96,23% in Europa League [0,9573-0,9673], contro un placebo con id estratti a caso allo 0,97%. Prima di adottarlo: aggiungere il vincolo del club (come per diretta.it) per chiudere anche il ~4% residuo, e lasciare vuoti i 2 ambigui invece di risolverli.

### Guadagno atteso

Il primo ponte fra le coppe europee e le carriere: 1.491 giocatori delle nostre leghe e 13.288 righe giocatore-partita che oggi non si possono mettere nella stessa frase del resto del repo. E la dichiarazione che chiude la trappola: `ID giocatore` non e' un player_id, non si joina.

---

## 6. La fase principale di Conference League non esiste a monte: 0 conferme su 3.416

**categoria** `assenza-a-monte` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `files/sofascore_coppe_europee_2526/README.md`, `docs/DATI.md`

### Evidenza

Validando il ponte SofaScore proposto, il tasso di conferma crolla in Conference League: 0,2826 [IC95 0,2708-0,2945] contro 0,9575 in Champions e 0,9623 in Europa League. La scomposizione lo spiega senza residui: preliminari e spareggi di Conference confermano allo 0,7364 [0,7177-0,7551], la fase principale allo 0,0000 su 3.416 righe — un contrasto interno perfetto, dentro la stessa competizione e con lo stesso ponte. La causa e' nell'elenco delle competizioni di player-scores nel 2025-26: c'e' `ECLQ` (3.513 presenze, le qualificazioni Conference) ma NON esiste il codice della fase principale, mentre `CL`/`CLQ` e `EL`/`ELQ` ci sono entrambi. Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/m_conf.py e .../n_percomp.py

### Riparazione proposta

Nessuna riparazione possibile dal nostro lato: il dato non c'e' nella fonte. Va dichiarato, e va dichiarato PRIMA di costruire il ponte SofaScore, perche' altrimenti il suo 78,7% di resa verra' letto come «il ponte funziona male in Conference» invece che «la controparte non esiste». Conseguenza operativa: la validazione di purezza del ponte SofaScore va misurata su Champions ed Europa League, dove la controparte esiste, e sulla Conference solo sulle qualificazioni. Da scrivere nel README della raccolta SofaScore, accanto alle due trappole gia' dichiarate, e in docs/DATI.md.

### Guadagno atteso

Evita di leggere un'assenza a monte come un aggancio fallito — che e' la distinzione che questo dominio confonde piu' spesso, e l'unica che dice se vale la pena lavorarci.

---

## 7. `Ruolo` e' dichiarato statico ma cambia per il 60% dei giocatori: e' `post`

**categoria** `look-ahead` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/player_stats.py`, `docs/DATI.md`

### Evidenza

src/data/player_stats.py:86 dichiara `STATIC_COLUMNS = ('Giocatore', 'Ruolo')`, dove `statico` significa per definizione (R8) «anagrafica che non dipende dalla partita». Misurato sulle 54.270 righe agganciate: 1.617 player_id su 2.684 (60,2%) hanno piu' di un `Ruolo` nella stessa stagione, e le righe interessate sono 37.231 su 54.270 (68,6%). Esempi: Hofmann Jonas {Centrocampista 12, Centrocampista offensivo 8, Esterno 3}, Blind Daley {Difensore centrale 27, Terzino 3, Difensore 1}. E' la posizione occupata IN QUELLA partita, quindi dipende dalla formazione di quella partita. Stessa cosa nella raccolta SofaScore: 919 `ID giocatore` su 6.024 hanno piu' di un `Ruolo`. Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/p_r8.py

### Riparazione proposta

Spostare `Ruolo` da `STATIC_COLUMNS` a una dichiarazione `post` (o `pre` se un domani arrivera' dalla formazione ufficiale pre-partita, con la stessa nota gia' scritta per `Titolare/Subentrato` alle righe 82-84). Attenzione all'effetto collaterale da verificare prima: `statistic_columns()` esclude le STATIC_COLUMNS, quindi togliere `Ruolo` da li' lo farebbe rientrare fra le 97 statistiche e romperebbe il conteggio del manifesto — va aggiunto all'insieme `skip` di `statistic_columns()` come gia' fatto per `Fase` (righe 320-323), che e' esattamente lo stesso caso: un'etichetta che non e' ne' una misura ne' un'anagrafica. Il campo anagrafico corrispondente esiste ed e' quello giusto da usare come statico: `position`/`sub_position` in files/player_scores/players.csv.gz.

### Guadagno atteso

Toglie di mezzo una colonna che oggi la documentazione autorizza a usare come feature senza precauzioni, e che invece descrive la partita da prevedere. Non e' il look-ahead piu' grave possibile (il ruolo si sa a formazione uscita), ma e' dichiarato al contrario, ed e' proprio la R8 a dire che il pericolo sta nella dichiarazione e non nel valore.

---

## 8. Il ponte NON confonde gli omonimi, e questa e' una misura, non una speranza

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `tests/test_player_identity.py`, `docs/DATI.md`, `README.md`

### Evidenza

Verificato col discriminante chiesto ('nessuno gioca due partite diverse lo stesso giorno'), come per gli allenatori: (player_id, data) con piu' di una partita distinta = 0 su 54.270. Nessun player_id compare due volte nello stesso giorno, in nessuna lega. Coppe nazionali: (player_id, data) con piu' di una squadra = 0 su 16.464. Omonimi misurati: nell'anagrafica dei 2.685 giocatori attivi nelle 5 leghe 2025-26 ci sono 5 insiemi-token condivisi da 2 persone (david_lopez, gonzalez_nico, gueye_idrissa, vitinha, wesley) per 10 persone in tutto; nel dato diretta.it 5 stringhe `Giocatore` mappano correttamente a 2 player_id ciascuna, e 0 player_id su 2.684 stanno sotto piu' di una stringa. Controllo aggiuntivo: la coppia (Squadra, Giocatore) copre piu' di una persona in 1 caso su 2.831 — ed e' il falso positivo 'Kiko', quindi dopo la riparazione va a 0. Ricalcolo: python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/d_omonimi.py e .../e_coerenza.py. Stato degli altri ponti misurato nella stessa sessione: coppe nazionali 16.464/18.307 = 89,93% (1.843 scoperte, di cui 1.565 senza `game_id` = partita non agganciata a monte, 1.563 in Coupe de France; 0 righe con club incoerente su 5.316 verificabili); registro manuale R3 = 1 riga sola (Alessandro Romano), con motivo, fonte e data.

### Riparazione proposta

Non c'e' niente da riparare: e' il risultato positivo del dominio e va SCRITTO, perche' oggi non e' scritto da nessuna parte e la prossima sessione lo rimisurera' da zero. La forma giusta e' un test: `(player_id, data)` deve avere una sola partita, sulle 5 leghe e sulle coppe. E' la guardia che avrebbe intercettato un collasso di identita' — non ha intercettato il caso Kiko solo perche' quello e' l'errore opposto (una persona sola spezzata su due id, non due persone fuse in uno), che si vede invece col controllo di competizione proposto sopra. I due test sono complementari e servono entrambi.

### Guadagno atteso

Il ponte diventa difeso su entrambi i modi in cui puo' rompersi (fondere due persone / spezzarne una), invece che sul solo conteggio di copertura che oggi e' l'unica cosa misurata.

---
