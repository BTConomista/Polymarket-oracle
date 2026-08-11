# I casi ambigui dei nomi di club

> Dominio come dichiarato dall'agente: **Casi AMBIGUI dei nomi di club — i 6 di SofaScore (coppe europee 2025-26) e i 6 delle coppe nazionali**

> 9 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

I dodici casi non sono lo stesso problema, e vanno separati prima di ripararli. I sei di SofaScore sono ambiguità VERE: il nome esterno («Athletic Club», «SS Virtus») non esiste nel registro e i token che restano dopo la normalizzazione pescano più club — qui serve informazione indipendente, e c'è: l'insieme delle partite (data + casa/trasferta + avversario), lo stadio con la città e il paese, e il fatto misurato che le squadre riserve nel registro non hanno MAI giocato una partita UEFA. I sei delle coppe nazionali sono invece un'ambiguità ARTIFICIALE prodotta dal nostro codice: quei nomi coincidono LETTERALMENTE con un nome del registro, ma `normalizza()` butta via proprio i token che li distinguono («UD»/«SD»/«CD» sono stopword, «1924» è una cifra), così «UD Logroñés» e «SD Logroñés» collassano entrambi su {logrones}. Tutti e dodici i casi si chiudono con prove ri-calcolabili; nessuno resta indecidibile. Il fatto strutturale da portarsi dietro è che il normalizzatore fonde 24 gruppi di club distinti del registro, e sono quasi tutti coppie «club prima/dopo la rifondazione» o «prima squadra/riserve»: è la mappa di rischio dei prossimi agganci.

---

## 1. «Athletic Club» (SofaScore) → club_id 621 Athletic Bilbao — confidenza conclusiva

**categoria** `alias-mancante` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

21 candidati perché 'club' è stopword e 'athletic' è un token comune: «Athletic Club» collassa su {athletic}. Prova per identità delle partite: l'insieme delle 8 gare SofaScore (data + casa/trasferta) coincide 8/8 con il club_id 621 e 0/8 con TUTTI gli altri 20 candidati. 19 dei 21 candidati hanno 0 partite UEFA nell'intero registro; l'unico altro con partite UEFA nel 2025 è St. Patrick's Athletic (1189), che però giocò 6 gare di ECLQ contro Hegelmann/Kalju/Beşiktaş — e SofaScore lo chiama con un nome proprio distinto, «St. Patrick's Athletic», che è già univoco (candidati()=[1189]). Prove indipendenti concordi: stadio SofaScore = San Mamés, Bilbao, Spain, capienza 53.289; clubs.csv per il 621 = San Mamés, stadium_seats 53.289 (identico). Punteggi: 8/8 identici fra il foglio Partite e games.csv. Nessuna collisione: nessun altro dei 212 nomi SofaScore si aggancia al 621. Ricalcolo: python -c "import pandas as pd;sf=pd.read_csv('files/sofascore_coppe_europee_2526/giocatori.csv.gz',usecols=['Data','Squadra','Campo','ID partita']).drop_duplicates(['ID partita','Squadra']);sf['d']=pd.to_datetime(sf.Data,format='%d.%m.%Y').dt.strftime('%Y-%m-%d');g=pd.read_csv('files/player_scores/games.csv.gz');fix={(r.d,r.Campo=='Casa') for r in sf[sf.Squadra=='Athletic Club'].itertuples()};print([(c,len(fix&{(r.date,r.home_club_id==c) for r in g[(g.home_club_id==c)|(g.away_club_id==c)].itertuples()})) for c in [621,1189,358,1071]])"

### Riparazione proposta

Aggiungere l'alias «Athletic Club» → «Athletic Bilbao» in una tabella di alias DEDICATA alla raccolta SofaScore (sul modello di ALIAS_COPPA in src/data/coppe_aggancio.py), non nel dizionario ALIAS globale di club_matching: la portata va limitata alla fonte su cui la prova è stata fatta. Verificato in sandbox: con l'alias, candidati('Athletic Club') = [621], univoco.

### Guadagno atteso

8 partite di Champions 2025-26 di un club DENTRO il nostro perimetro modellato (Ath Bilbao è in data/la_liga_matches.csv, 171 partite in casa): è il caso a valore più alto dei sei.

---

## 2. «Feyenoord» (SofaScore) → club_id 234 — ma l'alias da solo NON basta, misurato

**categoria** `alias-mancante` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Fixture: 10/10 coincidenze (data + casa/trasferta) col 234, 0/10 col 2826. Il 2826 («SC Feyenoord Rotterdam») ha 3 partite in tutto il registro, tutte KNVB Beker 2014-2015, e 0 partite UEFA di sempre. L'argomento «le riserve non giocano le coppe europee» regge ed è verificabile in casa; ma va rafforzato, perché un'alternativa era «2826 è un doppione del 234»: falsa, il 2826 gioca le stesse edizioni di KNVB Beker in cui gioca anche il 234 (7 partite NLP del 234 nelle stagioni 2014-2015) → due entità coesistenti. Stadio SofaScore De Kuip, Rotterdam, capienza 47.500; clubs.csv per il 234 = Stadion Feyenoord "De Kuip", 47.500 (identico). ⚠️ IL PUNTO: l'alias non risolve da solo. normalizza('Feyenoord Rotterdam') e normalizza('SC Feyenoord Rotterdam') danno ENTRAMBI {feyenoord, rotterdam} perché 'sc' è stopword; in sandbox, con il solo alias, candidati('Feyenoord') resta ambiguo su [234, 2826].

### Riparazione proposta

Due modifiche insieme, non una: (a) alias «Feyenoord» → «Feyenoord Rotterdam» nella tabella SofaScore; (b) aggiungere 'sc feyenoord rotterdam' a NON_AGGANCIARE in src/data/club_matching.py — è esattamente la classe (1) già documentata lì (squadre riserve che non vanno agganciate alla prima squadra). Verificato: la stringa non compare LETTERALMENTE fra i nomi del registro nella forma minuscola usata da NON_AGGANCIARE, quindi la lista continua a comportarsi come prevista.

### Guadagno atteso

10 partite (1 turno preliminare CL + 8 di fase campionato EL + ...) agganciate; e chiude un buco del matcher che si ripresenterebbe su qualunque altra fonte che scriva «Feyenoord» corto.

---

## 3. «SS Virtus» (SofaScore) → club_id 10613 AC Virtus Acquaviva (San Marino), NON un club italiano

**categoria** `alias-mancante` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

5 candidati, 4 italiani (Virtus Lanciano, Bassano Virtus, Virtus Entella, Virtus Francavilla) e 1 sammarinese. Fixture: 6/6 col 10613, 0/6 con ciascuno degli altri quattro. I quattro italiani hanno 0 partite UEFA di sempre nel registro (compaiono solo in CIT, Coppa Italia: 5, 9, 21 e 6 partite). Prova indipendente dal foglio Partite: le 3 gare in casa si giocano al «San Marino Stadium», città Serravalle, Paese San Marino, capienza 6.664 — e Acquaviva è un castello di San Marino. La domanda del brief («sammarinese o italiano?») ha quindi due risposte concordi e indipendenti: il ramo di qualificazione (il 10613 gioca CLQ/ECLQ come campione di San Marino) e il paese dello stadio.

### Riparazione proposta

Alias «SS Virtus» → «AC Virtus Acquaviva» nella tabella SofaScore. Verificato in sandbox: candidati() = [10613]. ⚠️ Non metterlo nel dizionario ALIAS globale: «SS Virtus» in una fonte italiana significherebbe quasi certamente un altro club, e l'alias globale trasformerebbe un aggancio vuoto in una certezza sbagliata (R6).

### Guadagno atteso

6 partite (2 CLQ + 4 ECLQ) agganciate; ed è il caso che dimostra il metodo: la geografia dello stadio decide dove i token non bastano.

---

## 4. «FK Žalgiris» (SofaScore) → club_id 602 Vilnius — e qui la sola DATA non basta

**categoria** `alias-mancante` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Attenzione: su data + casa/trasferta il Kauno Žalgiris (40090) coincide 2/4, perché i doppi confronti dei preliminari si giocano negli stessi giorni (24/07 in casa, 31/07 in trasferta) — una prova basata solo sulla data avrebbe dato un falso segnale. Decide l'AVVERSARIO: SofaScore dà a «FK Žalgiris» Ħamrun Spartans (09 e 15/07, CLQ) e Linfield (24 e 31/07, ECLQ); games.csv dà al 602 esattamente Hamrun Spartans e Linfield FC nelle stesse quattro date, mentre il 40090 in quelle stesse settimane gioca Penybont e Valur Reykjavík. Con data+campo+avversario: 4/4 sul 602, 0/4 sul 40090. Conferma dal lato della fonte: SofaScore distingue i due club da sé, perché usa il nome proprio «FK Kauno Žalgiris» per quello di Kaunas — e quel nome è già univoco (candidati() = [40090]). Stadio SofaScore: FK Žalgiris Stadium, Vilnius, Lithuania.

### Riparazione proposta

Alias «FK Žalgiris» → «FK Zalgiris Vilnius» nella tabella SofaScore (candidati() = [602] verificato). Nessun alias serve per «FK Kauno Žalgiris», già risolto. Da scrivere accanto all'alias il motivo: la disambiguazione è per avversario, non per data.

### Guadagno atteso

4 partite; e la lezione riusabile che nelle coppe a eliminazione la data è una chiave DEBOLE (i turni si giocano tutti nello stesso giorno).

---

## 5. «FK Radnički 1923» (SofaScore) → club_id 4645 Kragujevac

**categoria** `alias-mancante` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Fixture: 2/2 col 4645, 0/2 col 7567 (Radnički Niš). Il Niš esiste ed è attivo (68 partite nel registro, 8 UEFA), ma nella stagione 2025 non ha giocato NESSUNA partita UEFA: 0 righe in CL/CLQ/EL/ELQ/ECLQ — quindi non può essere la squadra del file. Avversario concorde: SofaScore «Klaksvíkar Ítróttarfelag», games.csv «KÍ Klaksvík», stesse due date (24 e 31/07, ECLQ 2° turno). Stadio: SofaScore «Čika Dača Stadium», Kragujevac, Serbia, capienza 15.169; clubs.csv per il 4645 «Čika Dača Stadion», 15.100. Il token '1923' viene scartato da normalizza() perché cifra: senza quello, {radnicki} pesca entrambi.

### Riparazione proposta

Alias «FK Radnički 1923» → «FK Radnicki 1923 Kragujevac» nella tabella SofaScore (candidati() = [4645] verificato).

### Guadagno atteso

2 partite; e mette in luce che normalizza() scarta le cifre, che in Serbia/Ucraina/Spagna sono spesso l'anno di fondazione ed è l'UNICO token distintivo.

---

## 6. «AFC Ajax» (SofaScore) → club_id 610 Ajax Amsterdam

**categoria** `alias-mancante` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Fixture: 8/8 col 610, 0/8 con l'11495 («Ajax Amateurs»). L'11495 ha 15 partite nel registro, TUTTE KNVB Beker, e 0 partite UEFA di sempre; e come per il Feyenoord l'ipotesi «è un doppione» è falsa in modo misurabile: l'11495 gioca i turni preliminari della KNVB Beker nelle stesse stagioni in cui il 610 gioca la stessa coppa (28 partite NLP del 610 in quelle stagioni). Prove indipendenti: SofaScore Johan Cruijff Arena, Amsterdam, Netherlands, capienza 55.865; clubs.csv per il 610 Johan Cruijff ArenA, 55.885 (scarto 20 posti, R4: differenza di edizione della capienza fra le due fonti, non un errore). Punteggi 8/8 identici col registro.

### Riparazione proposta

Alias «AFC Ajax» → «Ajax Amsterdam» nella tabella SofaScore (candidati() = [610] verificato). Facoltativo e più conservativo: aggiungere 'ajax amateurs' a NON_AGGANCIARE, come per il SC Feyenoord — qui non è necessario perché i due token-set restano distinti ({ajax,amsterdam} vs {ajax,amateurs}), ma renderebbe simmetrico il trattamento delle due riserve olandesi.

### Guadagno atteso

8 partite di Champions.

---

## 7. I 6 «ambigui» delle coppe nazionali NON sono ambigui: è il normalizzatore che cancella il token che distingue

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/test_coppe_aggancio.py`

### Evidenza

Tutti e sei i nomi coincidono LETTERALMENTE con un nome del registro, e il registro è una biiezione: club_names.csv.gz ha 3.173 righe, 3.173 club_id unici e 3.173 nomi unici (0 duplicati). L'ambiguità nasce da normalizza(): 'ud'/'sd'/'cd' sono stopword e le cifre vengono scartate, quindi «UD Logroñés» e «SD Logroñés» collassano entrambi su {logrones}, i tre Ourense su {ourense}, «Extremadura UD» e «CD Extremadura 1924» su {extremadura}, «San Fernando CD» e «UD San Fernando» su {fernando,san}. Le assegnazioni corrette, per nome esatto: CD Extremadura 1924→101648, Ourense CF→55398, SD Logroñés→33303, UD Logroñés→24420, UD Ourense→60225, UD San Fernando→57379 (1 riga esatta ciascuno). Tre conferme INDIPENDENTI dal nome: (1) data/coppe_2526/partite.csv porta già home_club_id/away_club_id presi da games.csv, e sono esattamente quei sei id — l'ambiguità è a valle di un dato che è già risolto a monte; (2) l'etichetta di games.csv è affidabile: su 177.916 lati partita il nome coincide con club_names nel 99,5453% dei casi, e le 687 divergenze sono ridenominazioni storiche dello STESSO club (FCI Levadia/Levadia Tallinn), mai due club confusi; (3) i due Logroñés si sono incontrati IN CAMPO — game_id 2254420, 29/08/2012, «SD Logroñés 2-1 UD Logroñés» a Las Gaunas: i due id compaiono nella stessa riga, quindi il registro li tiene distinti. Per la coppia di Ourense c'è una quarta conferma: la deduzione per ELIMINAZIONE di deduci_club() (fonte diretta.it, indipendente dal nome) ha già scritto 55398 e 60225 in data/coppe_2526/aggancio_squadre.csv — e coincidono. ⚠️ R4: né lo stadio né la divisione disambiguano qui — i due Logroñés giocano entrambi a Las Gaunas, i tre Ourense a O Couto, e in Copa del Rey 2025-26 SD Logroñés (28/10) e UD Logroñés (30/10) sono entrambi in divisione 3. Ricalcolo: python -c "import pandas as pd;cn=pd.read_csv('files/player_scores/club_names.csv.gz');print(len(cn),cn.club_id.nunique(),cn.name.nunique());print(cn[cn.name.isin(['CD Extremadura 1924','Ourense CF','SD Logroñés','UD Logroñés','UD Ourense','UD San Fernando'])].to_string())"

### Riparazione proposta

In Agganciatore.candidati(), inserire un passo di CORRISPONDENZA LETTERALE fra l'alias curato e la corrispondenza per token: se il nome coincide esattamente con un nome di club_names, restituire quel solo club_id. È sicuro perché il registro è una biiezione nome↔id (misurato: 0 nomi duplicati). L'ORDINE è vincolante e va scritto nel docstring: (1) NON_AGGANCIARE, (2) ALIAS curati, (3) nome letterale, (4) token. Se il passo letterale precedesse ALIAS/NON_AGGANCIARE si rischierebbe di resuscitare i casi già chiusi — verificato che oggi non accadrebbe (nessuno dei nomi di NON_AGGANCIARE, né 'Brest', 'Cardiff', 'Lincoln', 'Inter', 'Verona', esiste letteralmente nel registro), ma è una coincidenza fortunata, non una garanzia. IMPATTO MISURATO su 883 nomi di club usati nel repo (coppe nazionali 558, SofaScore 212, i 5 snapshot): 0 esiti cambiati (nessun univoco diventa un altro club) e 6 sbloccati — esattamente questi sei. Servono due test: uno che asserisca i sei id, uno che asserisca la priorità ALIAS > letterale (es. un nome finto che sia sia alias sia nome del registro).

### Guadagno atteso

9 partite di Copa del Rey 2025-26 con entrambi i lati agganciati (oggi 4 nomi su 6 restano vuoti), e — più importante — il difetto sparisce per TUTTE le fonti future, invece di essere tappato con sei alias a mano.

---

## 8. Mappa di rischio: il normalizzatore fonde 24 gruppi di club DISTINTI del registro, e quasi tutti sono rifondazioni o riserve

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `tests/test_coppe_aggancio.py`, `docs/DATI.md`

### Evidenza

Applicando normalizza() ai 3.173 nomi del registro restano 3.145 token-set: 24 gruppi contengono più club. Non sono casi esotici, sono UNA FAMIGLIA: (a) club prima/dopo la rifondazione, dove il distintivo è un suffisso d'anno che viene scartato — Metalurg Zaporizhya (3 club), Kuban Krasnodar, Karpaty Lviv, Metalist Kharkiv, Obolon Kyiv, Spartak Tambov, Dinamo St. Petersburg, FK Sevastopol, FK Poltava, Skala Stryi/Skala 1911 Stryi, FK Kudrivka; (b) prima squadra/riserve, dove il distintivo è '2'/'II'/'SC' — Rubin/Rubin 2 Kazan, Rotor/Rotor 2 Volgograd, Sibir/Sibir-2 Novosibirsk, Feyenoord/SC Feyenoord; (c) sigle societarie diverse nella stessa città — i tre Ourense, i due Logroñés, i due Extremadura, i due San Fernando, i due Horsens, i due Fredericia, i due Melilla. Ogni gruppo è un caso «Hellas Verona» in attesa: finché il matcher restituisce >1 candidato si comporta bene (lascia vuoto), ma qualunque alias scritto a mano su uno di quei token-set può cadere sul club sbagliato senza dare errore. Ricalcolo: python -c "import pandas as pd;from collections import defaultdict;from src.data import club_matching as cm;cn=pd.read_csv('files/player_scores/club_names.csv.gz');d=defaultdict(list);[d[cm.normalizza(n)].append((int(i),n)) for i,n in zip(cn.club_id,cn.name) if cm.normalizza(n)];print(sum(1 for v in d.values() if len(v)>1),'gruppi su',len(d))"

### Riparazione proposta

Non è una riparazione di codice ma una guardia: (a) scrivere i 24 gruppi nel docstring di club_matching.py come elenco esplicito dei punti ciechi noti; (b) aggiungere un test che ricalcoli il numero di gruppi collidenti e fallisca se cresce senza che qualcuno lo dichiari (stessa logica dei guardiani strutturali già in tests/); (c) regola operativa da scrivere accanto ad ALIAS: mai aggiungere un alias il cui token-set di destinazione cade in uno di quei 24 gruppi senza indicare il club_id esplicito. Alternativa più invasiva, da valutare a parte: far sopravvivere le cifre in normalizza() — ma cambierebbe il comportamento su tutte le fonti e va misurata, non fatta di slancio.

### Guadagno atteso

Trasforma un rischio latente in un elenco chiuso e sorvegliato: 24 punti ciechi noti invece di N ignoti.

---

## 9. R4 — nel foglio Partite di SofaScore «Gol casa» SOMMA i rigori della lotteria finale, esattamente come games.csv

**categoria** `finto-pieno` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Ħamrun Spartans - FK Žalgiris del 15/07/2025 risulta 13-10 in ENTRAMBE le fonti. Scomposizione dalle colonne dello stesso foglio: 1T 2-0, supplementari 0-0, «Rigori casa/trasferta» 11-10 → 2+11=13 e 0+10=10. Il punteggio vero della gara è 2-0 (andata 0-2, poi 11-10 ai rigori). È lo stesso difetto già documentato per le coppe nazionali («il punteggio di games.csv SOMMA I RIGORI su 68 partite su 458») e ricostruito lì dagli eventi. Va dichiarato ORA perché il confronto punteggi che ho usato come prova d'identità dà 38/38 coincidenze PROPRIO GRAZIE al fatto che le due fonti condividono la stessa convenzione: la coincidenza conferma l'aggancio, non la correttezza del punteggio. Chiunque costruisca il ponte partita→game_id userà quei numeri. Ricalcolo: python -c "import pandas as pd;p=pd.read_excel('files/sofascore_coppe_europee_2526/originale_sofascore.xlsx',sheet_name='Partite');print(p[(p.Data=='15.07.2025')&p.Casa.str.contains('amrun',na=False)][['Casa','Trasferta','Gol casa','Gol trasferta','Casa 1T','Trasferta 1T','Casa suppl.','Trasferta suppl.','Rigori casa','Rigori trasferta']].to_string())"

### Riparazione proposta

Aggiungere il rilievo al README della raccolta SofaScore, nella sezione delle trappole misurate, con la ricomposizione esatta (gol_90 + supplementari + rigori) e l'indicazione di ricostruire il punteggio dalle colonne per tempo — non da «Gol casa» — esattamente come fa già data/coppe_2526/partite.csv con le sue colonne separate. Nessuna modifica ai dati (R3): il valore grezzo resta com'è.

### Guadagno atteso

Evita che il prossimo lettore usi 13-10 come risultato: un numero che non è sbagliato per la fonte, ma non è il punteggio della partita.

---
