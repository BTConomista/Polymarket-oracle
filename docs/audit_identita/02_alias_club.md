# Gli alias dei nomi di club

> Dominio come dichiarato dall'agente: **Alias dei nomi di club — le squadre che due fonti chiamano diverso (SofaScore coppe europee, Smarkets 2026-27, coppe nazionali, snapshot 5 leghe) contro il registro files/player_scores/club_names.csv.gz**

> 12 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

Il dominio non è "mancano alias": è che **il conteggio dei nomi agganciati non distingue il giusto dallo sbagliato**. Ho costruito un controllo indipendente dalla stringa — dedurre il club dalle PARTITE (data + avversario già agganciato + punteggio esatto in games.csv) — e l'ho passato su tutte e cinque le fonti. Risultato: i 25 assenti e i 6 ambigui di SofaScore si risolvono TUTTI con prova a livello di fixture (1.818 conferme partita-squadra, 0 candidati concorrenti, 0 discordanze su 212 nomi), ma lo stesso controllo ha trovato **due certezze sbagliate che nessuna percentuale vedeva**: `Espanol` (football-data) agganciato univocamente a *Jove Español San Vicente* invece che a RCD Espanyol — 272 partite di La Liga su cui lo snapshot "100% agganciato" è falso — e `Red Star FC` agganciato al Red Star Belgrado perché la guardia `NON_AGGANCIARE` confronta la stringa grezza e basta un suffisso «FC» per aggirarla. Il matcher non aveva un autotest: girato sul proprio registro torna su se stesso 3.121/3.173 volte (98,36%), e le 50 ambiguità sono tutte casi in cui la sigla che DISTINGUE due club (UD/SD/CD, «1924») viene buttata via dalle stopword. I 174 assenti delle coppe sono invece per il 94,8% assenza a monte vera e strutturale (player-scores non ha né la Ligue 2 né la Coupe de France: le uniche competizioni francesi presenti sono FR1 e FRCH), con solo 4 controesempi. Con 36 alias + 2 caratteri + spareggio + guardia: SofaScore 85,4%→100,0%, e le partite europee con ENTRAMBE le squadre agganciate passano da 677/912 a 912/912.

---

## 1. FINTO PIENO: 'Espanol' è agganciato univocamente al club SBAGLIATO (Jove Español San Vicente, non RCD Espanyol) — 272 partite di La Liga

**categoria** `finto-pieno` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `docs/DATI.md`

### Evidenza

`normalizza('Espanol')` = {espanol}; il registro scrive «RCD Espanyol Barcelona» (espan**y**ol) e l'unico club che fa {espanol} è «Jove Español San Vicente» (25462), che in games.csv ha UNA sola partita (Copa del Rey 2024). Misura indipendente: ricomponendo le 16.111 partite dello snapshot contro games.csv per data + due club_id + punteggio, tornano 15.837 (98,30%) e **272 coppie non esistono affatto** — tutte e sole le partite di Espanyol (266 righe 'Espanol' su 7 stagioni + 6 di data slittata). Comando: `python /tmp/claude-0/-home-user-Polymarket-oracle/b3327155-e644-51d1-9512-6e349f88a5c8/scratchpad/RIPRODUCI.py` (blocco [2]). Nota metodo: lo stato di partenza dice «snapshot 153 nomi -> 100% agganciati»: è vero e inutile — 1 nome su 153 è agganciato a un club sbagliato, e nessun conteggio di celle piene lo vede (R6, R7).

### Riparazione proposta

Aggiungere a `ALIAS` in src/data/club_matching.py: `"Espanol": "RCD Espanyol Barcelona",  # football-data scrive Espanyol senza la y: {espanol} pesca Jove Español San Vicente (25462, 1 partita in games.csv). Verificato: con l'alias, tutte e 266 le partite ricompongono contro games.csv`. Verificato: candidati('Espanol') -> [714] e le 272 coppie mancanti scendono a 6 (slittamenti di data).

### Guadagno atteso

266 partite di La Liga (1,65% delle 16.111) smettono di puntare a un club di Tercera División; 20 squadre-stagione di Espanyol rientrano nel perimetro. Impedisce un errore silenzioso su ogni futuro join snapshot->player-scores.

---

## 2. La guardia NON_AGGANCIARE si aggira con un suffisso: 'Red Star FC' finisce sul Red Star Belgrado

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/`

### Evidenza

`Agganciatore.candidati` fa `nome.strip().lower() in NON_AGGANCIARE`, cioè un confronto di stringa GREZZA, mentre tutto il resto del modulo lavora su insiemi di token. La blocklist contiene 'red star', ma i dati scrivono «Red Star FC»: `A.candidati('Red Star FC')` -> **[159] = Red Star Belgrade** (dom=SER1, 60 partite di Super Liga serba), mentre il club vero è il Red Star FC di Saint-Ouen, Ligue 2, che nel registro non esiste. Sono 2 partite di Coupe de France (US Forbach e ASC Biesheim, 7° e 8° turno). Stesso buco per 'Red Star F.C.' (che però resta vuoto per altra via). Comando: blocco [7] di RIPRODUCI.py. È esattamente il caso «Brest» che il modulo dichiara di aver già pagato: non un mancato aggancio, una CERTEZZA sbagliata (R6).

### Riparazione proposta

Sostituire il confronto grezzo con una forma canonica che tolga punteggiatura/accenti/sigle MA **conservi l'ordine dei token** (l'ordine è il motivo per cui la blocklist esiste: 'Bilbao Athletic' e 'Athletic Bilbao' collassano sullo stesso frozenset). Implementazione misurata in scratchpad/guardia.py: `canonico(n) in {canonico(x) for x in NON_AGGANCIARE}`. Verificato: blocca 'Red Star FC' e 'Bilbao Athletic', NON blocca 'Athletic Bilbao' né 'Real Madrid'. ⚠️ COSTO DA DICHIARARE: blocca anche «FC Lusitanos» (28958, l'andorrano, 8 qualificazioni europee 2012-16), che oggi si aggancia. Se quel club serve, va tolto 'lusitanos' dalla blocklist e gestito come alias negativo per le sole forme francesi.

### Guadagno atteso

2 partite di Coupe de France smettono di attribuirsi al Red Star Belgrado; la guardia smette di essere aggirabile da qualunque variante ortografica futura. Costo misurato: 1 club (FC Lusitanos) passa da agganciato a bloccato.

---

## 3. 31 alias mancanti su SofaScore — tutti PROVATI a livello di fixture, non per somiglianza

**categoria** `alias-mancante` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`, `docs/DATI.md`

### Evidenza

25 assenti + 6 ambigui su 212 nomi (85,4%). Ognuno identificato SENZA usare la stringa: per ogni partita SofaScore del nome ignoto si cerca in games.csv la gara di quella data che coinvolge l'avversario già agganciato e si prende l'altro club. Esito: **31/31 con un solo candidato**, e la verifica piena (data ±1g + avversario + PUNTEGGIO ESATTO + paese dello stadio) dà 207/207 riscontri sui casi usabili. Passato lo stesso controllo su TUTTI i 212 nomi: **212 concordi, 0 discordi, 0 senza verdetto, 1.818 conferme su 1.824 partite-squadra (99,7%), 0 secondi candidati**. Comando: blocco [4] di RIPRODUCI.py. Classificazione del meccanismo (da `normalizza`): ESONIMO/LINGUA 12 (Praha/Prague ×2, München/Munich, København/Copenhagen, Wien/Vienna ×2, Crvena Zvezda/Red Star, Naxçıvan/Nakhchivan, Thessaloniki/Thessalonikis, Oleksandria/Oleksandriya, Ferencváros/Ferencvárosi, Klaksvíkar Ítróttarfelag/KÍ Klaksvík); SIGLA/FORMA ESTESA O RIDOTTA 11 (AIK/Allmänna Idrottsklubben, Beşiktaş JK, FCI Levadia, KF Ballkani, KF Shkëndija, ETO FC Győr, Nõmme Kalju, Royale Union, Sporting Braga, Ħamrun Spartans FC, Zirə FK); NOME UFFICIALE vs CORRENTE 3 (Athletic Club/Athletic Bilbao, Olympique Lyonnais/Olympique Lyon, AFC Ajax/Ajax Amsterdam); OMONIMIA VERA da sciogliere 5 (Feyenoord, FK Radnički 1923, FK Žalgiris, SS Virtus, Hapoel Be'er Sheva).

### Riparazione proposta

Aggiungere a `ALIAS` un blocco «coppe europee SofaScore 2025-26», ognuno con la prova nel commento (n. partite ricomposte con data+avversario+punteggio): 'AC Sparta Praha'->'AC Sparta Prague' (14/14); 'AIK'->'Allmänna Idrottsklubben' (4/4); 'Araz Naxçıvan'->'Araz-Nakhchivan' (4/4); 'Aris Thessaloniki'->'Aris Thessalonikis' (2/2, sciolto al 2° giro dopo Araz — NON è l'Aris Limassol); 'Beşiktaş JK'->'Beşiktaş Jimnastik Kulübü' (6/6); 'ETO FC Győr'->'ETO FC' (6/6); 'FC Bayern München'->'Bayern Munich' (14/14); 'FC København'->'FC Copenhagen' (14/14); 'FCI Levadia Tallinn'->'Levadia Tallinn' (6/6); 'FK Austria Wien'->'Austria Vienna' (4/4); 'FK Crvena Zvezda'->'Red Star Belgrade' (16/16); 'Ferencváros TC'->'Ferencvárosi TC' (18/18); "Hapoel Be'er Sheva"->'Hapoel Beer Sheva' (4/4, casa in Ungheria — R4, sede neutra); 'KF Ballkani'->'FC Ballkani' (3/3); 'KF Shkëndija'->'Shkendija Tetovo' (16/16); 'Klaksvíkar Ítróttarfelag'->'KÍ Klaksvík' (2/2); 'Nõmme Kalju'->'Kalju FC' (2/2); 'Oleksandria'->'FC Oleksandriya' (2/2, casa in Polonia — R4); 'Olympique Lyonnais'->'Olympique Lyon' (10/10; NON «Lyon - La Duchère»); 'Royale Union Saint-Gilloise'->'Union Saint-Gilloise' (8/8); 'SK Rapid Wien'->'Rapid Vienna' (12/12); 'SK Slavia Praha'->'SK Slavia Prague' (7/7); 'Sporting Braga'->'SC Braga' (19/19); 'AFC Ajax'->'Ajax Amsterdam' (8/8; NON «Ajax Amateurs» 11495); 'Athletic Club'->'Athletic Bilbao' (8/8; 'athletic' da solo dava 21 candidati); 'FK Radnički 1923'->'FK Radnicki 1923 Kragujevac' (2/2; stadio SofaScore «Čika Dača Stadium» = stadium_name del 4645, NON il Radnicki Nis); 'FK Žalgiris'->'FK Zalgiris Vilnius' (4/4; NON Kauno Žalgiris); 'Feyenoord'->'Feyenoord Rotterdam' (10/10); 'SS Virtus'->'AC Virtus Acquaviva' (6/6, San Marino — ⚠️ NON Virtus Entella, che è l'accoppiamento che una somiglianza di stringa sceglierebbe). Zirə FK e Ħamrun Spartans FC NON servono come alias se si adotta il fix caratteri (difetto separato).

### Guadagno atteso

SofaScore 85,4% -> 100,0% dei nomi. Partite europee con ENTRAMBE le squadre agganciate: 677/912 -> 912/912. Righe-giocatore utilizzabili: 29.691/40.067 -> 40.067/40.067. Sblocca il punto (a) dei tre prerequisiti dichiarati nel README della raccolta.

---

## 4. 'ə' e 'Ħ' non sono decomposti da NFKD e vengono CANCELLATI: 'Zirə'->'zir', 'Ħamrun'->'amrun'

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/`

### Evidenza

`_TRADUZIONE` copre ø/ł/đ/ß/æ/œ/ð/þ/ı ma non lo schwa azero (U+0259) né la H maltese con barra (U+0126/0127). Dopo NFKD restano non-ASCII e il `re.sub(r'[^a-z0-9 ]',' ')` li cancella, mutilando il token: `normalizza('Zirə FK')` = {'zir'}, `normalizza('Ħamrun Spartans FC')` = {'amrun','spartans'}. Censimento su tutte le fonti (scratchpad/chars.py): sono gli UNICI due caratteri-lettera che sopravvivono a NFKD, 1 occorrenza ciascuno. È la stessa famiglia dei due bug già dichiarati in testa al modulo, non un caso nuovo.

### Riparazione proposta

Aggiungere a `_TRADUZIONE`: `"ə": "a", "Ə": "a", "ħ": "h", "Ħ": "h"`. Misurato: 'Zirə FK'->{zira} coincide ESATTAMENTE con «Zira FC» (46710) e 'Ħamrun Spartans FC'->{hamrun,spartans} con «Hamrun Spartans» (17149); **zero regressioni** su tutte e quattro le fonti e sull'autotest del registro. Onestà: 'ə'->'a' è una convenzione di traslitterazione scelta perché produce la coincidenza esatta sull'unico caso presente ('ə'->'e' darebbe 'zire', che non esiste); vale la pena aggiungere un test che fallisca se un carattere-lettera sopravvive a `normalizza` invece di essere cancellato in silenzio.

### Guadagno atteso

2 nomi SofaScore risolti senza alias (la via giusta: è un difetto della normalizzazione, non una differenza fra le fonti). Chiude una classe di errori, non due casi.

---

## 5. Le sigle che DISTINGUONO due club (UD/SD/CD, e le cifre '1924') sono fra le stopword: 6 ambiguità sulle coppe e 50 dentro il registro stesso

**categoria** `ambiguita-da-decidere` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/`

### Evidenza

AUTOTEST MAI FATTO: dando in pasto ad `Agganciatore` i 3.173 nomi del suo stesso registro, torna su se stesso **3.121 volte (98,36%)**, 50 restano ambigue, 2 assenti, 0 sbagliate. Le 50 sono 25 coppie/terne in cui l'unico token diverso è una sigla societaria («UD Logroñés» vs «SD Logroñés», «CD Ourense»/«Ourense CF»/«UD Ourense», «San Fernando CD» vs «UD San Fernando», «AC Horsens» vs «FC Horsens», «FC Rubin Kazan» vs «Rubin 2 Kazan») o una cifra («Extremadura UD» vs «CD Extremadura 1924», «Skala Stryi» vs «Skala 1911 Stryi»). Le stesse 6 tornano come ambigue sulla Copa del Rey. Comando: blocco [3] e [5] di RIPRODUCI.py.

### Riparazione proposta

Aggiungere in `candidati()` uno **spareggio di ultima istanza**, applicato solo quando i candidati sono >1: se ESATTAMENTE UNO ha la stessa forma «cruda» del nome cercato — accenti piegati, punteggiatura tolta, ma sigle e cifre CONSERVATE, token ordinati (scratchpad/tiebreak.py, funzione `crudo`) — si prende quello; altrimenti resta ambiguo. VALIDAZIONE INDIPENDENTE, non circolare: sulle coppe 354 coppie (nome, club_id) sono già note perché la fonte è player-scores stesso, e lo spareggio passa da 346 giusti (97,7%) a **352 (99,4%) con 0 SBAGLIATI**; le 6 ex-ambigue della Copa del Rey vengono tutte e 6 sul club_id già noto. Autotest registro: 3.121 -> 3.171/3.173 (99,94%), 0 ambigue, 0 sbagliate. Zero cambi su snapshot, SofaScore e Smarkets.

### Guadagno atteso

6 nomi di coppa risolti (+13 partite con entrambe le squadre agganciate); e soprattutto il matcher smette di non sapere riconoscere i nomi del proprio registro — che è la condizione minima perché una percentuale di copertura voglia dire qualcosa.

---

## 6. ALIAS non sa esprimere «questo esatto club»: mappa insiemi di token, e due club possono avere lo stesso insieme (Feyenoord)

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`

### Evidenza

`Agganciatore.__init__` costruisce `self._alias = {normalizza(k): normalizza(v)}`: l'alias sostituisce un insieme di token con un altro, non punta a un club_id. Ma «Feyenoord Rotterdam» (234) e «SC Feyenoord Rotterdam» (2826) danno lo STESSO frozenset {feyenoord, rotterdam} — 'sc' è stopword. Quindi l'alias 'Feyenoord'->'Feyenoord Rotterdam' resta ambiguo: verificato, `candidati('Feyenoord')` -> [234, 2826] anche con l'alias. È 1 caso su 38 alias proposti, ma è un limite del meccanismo, non del caso.

### Riparazione proposta

Nello spareggio del difetto precedente, provare la forma cruda del nome cercato E POI quella del VALORE dell'alias. Misurato: `crudo('Feyenoord Rotterdam')` = 'feyenoord rotterdam' coincide con 234 e non con 2826 ('feyenoord rotterdam sc') -> [234]. In alternativa, più pulito ma più invasivo: permettere a `ALIAS` valori `int` (club_id diretto). La prova che Feyenoord è il 234 è indipendente: 10/10 partite ricomposte con data + avversario + punteggio esatto.

### Guadagno atteso

Chiude l'ultimo nome SofaScore (212/212). Rende esprimibile qualunque alias futuro verso un club il cui nome è prefisso/sottoinsieme di un altro.

---

## 7. Smarkets: 3 abbreviazioni mancanti + 1 assenza a monte vera

**categoria** `alias-mancante` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `data/squadre_smarkets_2026_27.json`, `docs/DATI.md`

### Evidenza

4 nomi su 96 non agganciati (95,8%). 'Man Utd' -> {man, utd}: nessun club ha quei token (ALIAS ha già 'Man United' e 'Manchester Utd', non questa terza forma). 'Nottm Forest' -> {nottm, forest}. 'Lille OSC' -> {lille, osc}: il registro scrive «LOSC Lille», e L+OSC non si ricompone per token. 'Le Mans FC' -> il club NON esiste: `cerca('mans')` sul registro dà solo Mansfield Town e Sever Murmansk, e player-scores non ha la Ligue 2. PROVA per i tre agganciabili, per ESCLUSIONE su informazione indipendente (data/stagione_2026_2027/club/{ENG,FRA}, 20 e 18 cartelle-club): dei 20 nomi Smarkets di Premier 18 si risolvono su 18 club distinti, e i 2 club dell'anagrafica non ancora presi sono esattamente Manchester United (985) e Nottingham Forest (703); idem in Ligue 1, dove restano le-mans-fc (nessun club_id) e lille-osc (1082). Secondo canale: `domestic_competition_id` dei tre è GB1/GB1/FR1, coerente con la lega dichiarata da Smarkets; controllo di coerenza su tutti i 92 nomi già risolti: 0 disallineamenti reali (3 apparenti sono neopromosse con dom=NaN). ⚠️ NON usare `nome_smarkets` dell'anagrafica come prova: il CLAUDE.md lo dichiara già falso 64 volte su 96, e infatti lì Man Utd è scritto «Manchester United».

### Riparazione proposta

Aggiungere a `ALIAS`: `'Man Utd': 'Manchester United'`, `'Nottm Forest': 'Nottingham Forest'`, `'Lille OSC': 'LOSC Lille'`. Per 'Le Mans FC' NON si propone nulla: è assenza a monte, va dichiarata in data/squadre_smarkets_2026_27.json e in docs/DATI.md come «club di Ligue 1 2026-27 senza club_id perché player-scores non copre la Ligue 2». NOTA: 'Nottm Forest' si risolverebbe anche togliendo l'apostrofo invece di sostituirlo con uno spazio (l'alias esistente "Nott'm Forest" collasserebbe sullo stesso insieme), ma quella strada ha una regressione misurata — rompe «Atlètic Club d'Escaldes» (64780), dove l'apostrofo è un'elisione e separa davvero due parole. Meglio l'alias esplicito.

### Guadagno atteso

Smarkets 95,8% -> 99,0%. Restituisce Manchester United e Nottingham Forest al riconoscimento delle amichevoli in `club-friendlies` (Fase 149), che è lo scopo dichiarato di quel file.

---

## 8. Coppe nazionali: l'ipotesi «quasi tutti dilettanti francesi assenti a monte» è VERA al 94,8%, con 4 controesempi

**categoria** `assenza-a-monte` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `data/coppe_2526/README.md`, `docs/DATI.md`

### Evidenza

174 nomi assenti su 558. **172 su 174 = 98,9% sono Coupe de France**; gli altri 2 sono Coppa Italia. Ripartizione dei 172 per divisione (colonna `divisione_casa/ospite` di partite.csv): d1=1, d2=8, d3=10, d4=23, d5=33, d6=52, d7=24, d8=14, d9=4, oltremare=3 (AS Magenta/Nuova Caledonia, AS Le Gosier/Guadalupa, Bandrélé FC/Mayotte). Quindi **153/172 (89,0%) sono quarta divisione o inferiore o d'oltremare** e **163/172 (94,8%) stanno sotto la Ligue 2**. La causa è strutturale e verificabile in un colpo: le uniche competizioni francesi in competitions.csv sono **FR1 e FRCH** — niente Ligue 2, niente Coupe de France. Verifica diretta di assenza per token distintivo su tutti gli 8 club di Ligue 2 e i 10 di National 1: `cerca()` dà NESSUNO per boulogne, grenoble, annecy, rodez, laval, dunkerq, puy, orlean, peronnas, chateauroux, aubagne, quevilly, concarneau, fleury, brieuc, magenta, gosier, bandrele; 'mans' dà solo Mansfield/Murmansk, 'paris' solo PSG e Paris FC (non Paris 13 Atletico). CONTROESEMPI (4, cioè assenza a monte FALSA — 2,3% dei 174): (1) **'Olympique lyonnais'**, divisione 1, cioè una NOSTRA squadra: il club esiste (1041), è solo scritto in minuscolo e con l'aggettivo; (2) **'Thonon Évian GG FC'**, divisione 5, esiste come «Thonon Évian Grand Genève FC» (14171, dom=FR1, 114 partite di Ligue 1 2012-2014 — è l'Évian TG rifondato, e transfermarkt lo tiene sullo stesso ID); (3) **'Internazionale'** (finale di Coppa Italia, fonte wikipedia-en) = Inter Milan (46); (4) **'FC Südtirol-Alto Adige'** = FC Südtirol (4554). Screening avversariale a conferma: la somiglianza di stringa sui 172 produce, sopra la coppia vera, solo falsi amici — «FC Mulhouse»~«FC Toulouse» 0,818, «FC Challans»~«FC Dallas» 0,800, «Le Mans FC»~«Al-Ain FC» 0,737, «Rodez AF»~«Boldklubben af 1893». 114/172 (66,3%) non condividono NEMMENO UN token col registro.

### Riparazione proposta

Non serve un alias per i 168 restanti: vanno DICHIARATI come assenza a monte in data/coppe_2526/README.md e docs/DATI.md, con la ragione misurabile («competitions.csv ha per la Francia solo FR1 e FRCH»). Alias da aggiungere, 3 (il quarto è già coperto dall'alias 'Olympique Lyonnais' proposto per SofaScore, perché `normalizza` è insensibile al maiuscolo): `'Thonon Évian GG FC': 'Thonon Évian Grand Genève FC'`, `'Internazionale': 'Inter Milan'`, `'FC Südtirol-Alto Adige': 'FC Südtirol'`. ⚠️ Sul Thonon va scritto che agganciarlo attribuisce una partita di quinta divisione a un club_id che nel nostro dataset è un club di Ligue 1 2012-14: è corretto rispetto a come il registro definisce l'entità, ma va dichiarato (R4).

### Guadagno atteso

Coppe 67,7% -> 69,4% dei nomi e 457 -> 470 partite con entrambe le squadre agganciate. Il guadagno è volutamente piccolo: il valore qui è chiudere la domanda («il buco è strutturale, non è lavoro arretrato») invece di lasciarla aperta.

---

## 9. player-scores chiama lo stesso club con due nomi diversi: 71 coppie (club_id, nome) di games.csv non si riagganciano

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `False`

**File**: `docs/DATI.md`, `src/data/club_matching.py`

### Evidenza

Confrontando `home_club_name`/`away_club_name` di games.csv col nome dello stesso club_id in club_names.csv.gz: **3.099 su 3.170 (97,8%)** si riagganciano al club giusto, 71 no. Alcuni sono nomi DIVERSI nella stessa fonte («FC Südtirol-Alto Adige» vs «FC Südtirol», «FCI Levadia» vs «Levadia Tallinn», «Slavutych Cherkasy» vs «Cherkaskyi Dnipro», «Skala Morshyn» vs «Skala Stryi»); molti altri sono nomi IDENTICI che comunque falliscono per ambiguità («Feyenoord Rotterdam», «CD Ourense», «SD Logroñés», «FC Rubin Kazan», «AC Horsens»). Comando: scratchpad/tool.py + il confronto in fondo alla sezione autotest.

### Riparazione proposta

Non riparabile con alias — è una proprietà della fonte, e la sola parte «ambigua» la chiude lo spareggio (difetto 5). Va DICHIARATA in docs/DATI.md: chi aggancia partendo da games.csv non può assumere che il nome lì scritto sia quello di club_names, e deve usare il club_id quando c'è. Se serve chiudere anche il residuo, la via giusta è un indice ausiliario costruito dai nomi di games.csv (club_id già noto), non altri alias a mano.

### Guadagno atteso

Evita che una sessione futura tratti come «alias mancanti» 71 casi che sono rumore interno della fonte, e che ne aggiunga a mano una lista non verificabile.

---

## 10. games.csv registra il risultato del TRIBUNALE, il nostro snapshot quello del campo (R1): 2 partite su 16.111

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `False`

**File**: `docs/DATI.md`, `data/correzioni_dichiarate.csv`

### Evidenza

Ricomponendo snapshot vs games.csv per data + due club_id, due partite hanno lo stesso incontro ma punteggio diverso: Verona-Roma 19/09/2020 (snapshot 0-0, games.csv 3-0) e Union Berlin-Bochum 14/12/2024 (snapshot 1-1, games.csv 0-2). Il secondo è già dichiarato nel CLAUDE.md come caso-scuola di R1; il primo **non lo è**. In entrambi lo snapshot è nel giusto per la nostra regola (i mercati si regolano sul fischio finale). Comando: blocco [2] di RIPRODUCI.py.

### Riparazione proposta

Nessuna correzione ai dati — R1 dice che il nostro dato è quello giusto. Va aggiunta la riga «Verona-Roma 19/09/2020, 0-0 sul campo, 3-0 a tavolino» accanto a Union Berlin-Bochum in docs/DATI.md, e va scritto che **player-scores segue la convenzione opposta**: qualunque join che verifichi il punteggio contro games.csv ha 2 eccezioni note e non è un bug.

### Guadagno atteso

Evita che il prossimo controllo di coerenza «scopra» due partite corrotte e le corregga nel verso sbagliato (R4: un'anomalia si dichiara anche quando non è un errore).

---

## 11. Il matcher dei club non ha un test che lo esegua sul proprio registro

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `tests/`

### Evidenza

`grep -rn 'club_matching' tests/` — non esiste un test che verifichi la proprietà minima «ogni nome del registro si aggancia al proprio club_id». Girandola a mano ho trovato i 50 casi ambigui e i 2 assenti del difetto 5, e senza quella misura sarebbero rimasti invisibili. Analogamente non esiste un controllo che ricomponga lo snapshot contro games.csv — ed è quello che ha scoperto `Espanol`.

### Riparazione proposta

Due test: (1) `test_il_matcher_riconosce_i_nomi_del_proprio_registro`: per ogni riga di club_names.csv.gz, `aggancia(name) == club_id`, con soglia dichiarata (oggi 98,36%, con le riparazioni 99,91% — i 3 residui sono il Lokomotiv in cirillico, «AC Football Club» che è tutto stopword, e FC Lusitanos bloccato di proposito); (2) `test_lo_snapshot_ricompone_contro_games_csv`: le 16.111 partite devono ritrovarsi in games.csv per data + due club_id, con le 2 eccezioni R1 elencate per nome. Il secondo è la guardia che avrebbe visto `Espanol` il giorno in cui è entrato.

### Guadagno atteso

Il difetto 1 è costato 272 partite silenziose per un tempo imprecisato. Un test da venti righe lo avrebbe reso rumoroso al primo pytest.

---

## 12. 14 righe di Copa del Rey hanno l'avversario a NaN nella fonte

**categoria** `assenza-a-monte` · **rischio** `nullo` · **riparabile ora** `False`

**File**: `data/coppe_2526/README.md`, `docs/DATI.md`

### Evidenza

`data/coppe_2526/partite.csv`: 7 valori NaN in `casa` e 7 in `ospite`, tutti nei turni di qualificazione del 27/09 e 04/10/2025 (Atlètic Sant Just, CD Getxo, CD Sant Jordi, Puerto de Vega CF, SD Negreira, Atlético Palma del Río CF, UD Maracena), fonte player-scores. Sono le 7 sfide di qualificazione con un solo lato nominato, andata e ritorno.

### Riparazione proposta

Nessuna riparazione con alias: è un buco della fonte, non un problema di nomi. Va dichiarato nel README della raccolta coppe come le 204 partite senza formazione già dichiarate. ⚠️ Va anche corretto il modo di contare: un `dropna()` sui nomi cambia il totale degli assenti da 175 a 174, ed è la differenza fra «nome non agganciato» e «nome che non c'è» — due stati diversi che vanno tenuti separati (R6).

### Guadagno atteso

Chiude una discrepanza di 1 unità nei conteggi di copertura, che altrimenti riappare a ogni ricalcolo.

---
