# Allenatori, traghettatori, vice

> Dominio come dichiarato dall'agente: **Allenatori, traghettatori e vice (src/data/allenatori.py) + il blocco SofaScore coppe europee 2025-26**

> 11 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

Questo dominio non ha un problema di dati mancanti: ha un problema di UNITA' DI MISURA e di IDENTITA'. Tre numeri diversi (righe di conflitto, chiavi in conflitto, persone dietro le chiavi) girano nei documenti come se fossero lo stesso, e la stessa confusione colpisce i mandati: `interruzione` non e' un flag "vice", e' una proprieta' RELAZIONALE del mandato di mezzo, che in 40 casi su 412 marca il TITOLARE invece del suo secondo. Il dato grezzo (836 interruzioni, 13.810 mandati) e' esatto e ricalcolato riga per riga: sbagliate sono le frasi che lo riassumono. Sotto la superficie ci sono pero' due difetti veri: un bug in `panchine(ricuci=True)` che spezza 9 mandati e attribuisce 23 partite a "partite_altrui" dello stesso allenatore che le ha giocate, e un finto pieno da manuale nel registro della Fase 141, dove la colonna `ruolo` e' piena al 100% ma per 896 righe su 1.190 e' un default e non una misura. `esperienza_prima()` invece regge: tre mutazioni avversariali (5.000 partite future, una competizione che nasce nel futuro, troncamento del dataset) cambiano ZERO celle su 41.560 — e' R8-sicura contro il futuro, ma perde per identita' (gli omonimi) e non distingue "debuttante" da "chiave non agganciata". Sul fronte SofaScore il sospetto R8 sullo storico arbitro e' CONFERMATO con margine schiacciante, e in compenso e' emersa un'occasione che il README dichiara impossibile: il ponte partita->game_id via gli allenatori aggancia 728/912 partite con 728/728 punteggi identici e regala 183 alias di squadra a zero ambiguita', senza nessuna tabella scritta a mano.

---

## 1. «29 righe di conflitto» contro «11 omonimi»: non e' una discrepanza, sono tre unita' diverse mai dichiarate

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `docs/GLOSSARIO.md`

### Evidenza

conflitti_identita() restituisce una riga per ogni COPPIA di partite in conflitto, non per persona: 29 righe = 11 chiavi distinte = >=22 persone. CLAUDE.md («11 omonimi, 2 nel perimetro») conta le CHIAVI ed e' corretto, e rapporto_copertura() lo ricalcola da solo (conflitti_identita_globali=11, conflitti_identita_perimetro=2). Le 29 righe si concentrano su 2 nomi: michel 13, luis castro 5, gli altri 9 nomi 1 riga a testa (luis tevenet 3). Nessuna chiave arriva a 3 club distinti nello stesso giorno, quindi il limite inferiore dimostrato e' esattamente 2 persone per chiave. Comando: python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;c=A.conflitti_identita(A.load_partite());print(len(c),c.manager_key.nunique());print(c.groupby('manager_key').size())" e python -c "import sys,json;sys.path.insert(0,'.');from src.data import allenatori as A;print(json.dumps(A.rapporto_copertura(),indent=1))"

### Riparazione proposta

Aggiungere UNA riga al docstring di conflitti_identita(): «ritorna una riga per COPPIA di partite in conflitto; per il numero di NOMI usa .manager_key.nunique(), per le persone il minimo dimostrato e' 2 per nome». E dire nel docstring che 29/11/22 sono tre numeri diversi dello stesso fatto. Nessun numero di CLAUDE.md va cambiato: e' gia' giusto.

### Guadagno atteso

Zero sul modello; toglie di mezzo la prossima sessione che «corregge» un numero corretto — che e' esattamente il costo che la regola R4 vuole evitare.

---

## 2. «836 mandati su 13.810 sono un vice per una gara» e' falso: 424 delle 836 durano piu' di una partita

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `CLAUDE.md`

### Evidenza

I due totali sono esatti (13.810 mandati, 836 interruzioni, verificati al codice di HEAD), ma la frase li lega male: la distribuzione delle 836 per numero di partite e' {1: 412, 2: 94, 3: 52, 4: 38, 5: 19, 6: 20, 7: 13, 8: 17, 9: 12, 10: 5, ...} — 424 su 836 (50,7%) hanno piu' di una partita e non sono «un vice per una gara». Il docstring di panchine() lo dice bene («di cui 412 di una partita sola»); e' il riassunto in CLAUDE.md §4 che perde il «di cui». Comando: python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;m=A.panchine(A.load_partite());print(len(m),int(m.interruzione.sum()));print(m[m.interruzione].partite.value_counts().sort_index().head(10).to_dict())"

### Riparazione proposta

In CLAUDE.md §4 sostituire «836 mandati su 13.810 sono un vice per una gara» con «836 mandati su 13.810 sono un'interruzione A->X->A, di cui 412 di una partita sola». E, se si adotta la classificazione del punto successivo, aggiungere che delle 412 solo 260 sono davvero uno stand-in.

---

## 3. Tre numeri stantii nei docstring, gia' smentiti da rapporto_copertura() nello stesso file

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `tests/`

### Evidenza

(1) panchine() dice «62 su 1.105 nella finestra del perimetro»: misurato 65 su 1.190, ed e' rapporto_copertura() dello stesso modulo a dirlo (mandati_club_perimetro_timeline_completa=1190, interruzioni_club_perimetro=65). (2) Il docstring di testa dice «65 competizioni»: sono 70 (competizioni=70). (3) load_partite() dice «16.111 partite -> 32.222 righe», ma col default solo_con_allenatore=True sono 16.110 partite e 32.220 righe — lo dice il paragrafo successivo dello stesso docstring, che scarta le 2 righe di Nantes-Tolosa. Comando: python -c "import sys,json;sys.path.insert(0,'.');from src.data import allenatori as A;print(json.dumps(A.rapporto_copertura(),indent=1))" e python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;p=A.load_partite(solo_top5=True,stagioni=A.STAGIONI);print(len(p),p.game_id.nunique())"

### Riparazione proposta

Allineare i tre numeri ai valori che rapporto_copertura() gia' calcola, e scrivere nel docstring che quei numeri NON vanno citati a memoria ma riletti da rapporto_copertura() (il modulo lo dice gia' per se stesso: applicarlo anche ai suoi docstring). Meglio: un test che confronta i numeri del docstring col dizionario, cosi' la deriva si vede subito.

---

## 4. BUG in panchine(ricuci=True): 9 mandati restano spezzati e 23 partite finiscono in `partite_altrui` dell'allenatore che le ha giocate

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `tests/test_allenatori.py`

### Evidenza

ricuci=True deve riassorbire le interruzioni di una partita nel mandato che le circonda. Su sequenze alternate A-X-A-X-A dove ANCHE il mandato di mezzo di A e' di una partita, il riaggancio `gruppo[i]=gruppo[i-2]` punta a un mandato che nel frattempo e' stato assorbito, e il merge fallisce in silenzio: 27 riconnessioni puntano a un gruppo morto, e il risultato sono 9 coppie di mandati CONSECUTIVI dello stesso allenatore nello stesso club — che per costruzione non dovrebbero esistere (senza ricuci sono 0). Caso: Nottingham Forest, nuno espirito santo esce come DUE mandati (2023-12-23/2024-10-06, 34 partite e 2024-11-10/2025-08-31, 36) invece di uno da 71; e la sua partita del 25/10/2024 e' contata fra le `partite_altrui` del suo stesso mandato precedente. Casi identici: Barcellona/tito vilanova, Club Brugge/philippe clement, Bodo-Glimt/kjetil knutsen, Wolfsberger/dietmar kuhbauer, Sonderjyske/thomas norgaard, Farul/ianis zicu, Mladost/nikola rakojevic, PAOK/gianpaolo castorina. In totale 23 delle 412 assorbite hanno lo stesso manager_key del mandato ospite. Le partite non si perdono (sum(partite)+sum(partite_altrui)=176.228 = tutte le righe), ma sono attribuite male. Comando: python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;t=A.load_partite();r=A.panchine(t,ricuci=True).sort_values(['club_id','data_da']);print(int((r.manager_key==r.groupby('club_id').manager_key.shift()).sum()))" -> 9

### Riparazione proposta

Nel ciclo di ricuci, tenere accanto a `ultimo_vivo` anche la sua manager_key (`ultimo_vivo_key`) e riagganciare a QUELLO invece che a i-2: `if ultimo_vivo is not None and manager_key[i]==ultimo_vivo_key: gruppo[i]=ultimo_vivo` PRIMA del ramo `assorbibile`. Verificato in scratch sulla stessa timeline: mandati 13.032 (invece di 13.041), consecutivi stesso allenatore 0 (invece di 9), assorbite con host omonimo 0 (invece di 23), partite conservate 176.228/176.228, e Forest torna un mandato solo di 71 partite con 2 interruzioni. Serve anche un test di invariante: dopo ricuci, nessun club puo' avere due mandati consecutivi con la stessa manager_key.

### Guadagno atteso

Correttezza, non predizione: oggi nessun modello legge panchine(). Ma e' esattamente il tipo di errore che non si vede piu' a valle — un mandato spezzato in due dimezza l'anzianita' dell'allenatore e inventa un cambio di panchina che non c'e' stato, cioe' avvelena proprio la feature «effetto rimbalzo» per cui il modulo esiste.

---

## 5. I mandati di UNA partita sono cinque cose diverse, e tre bastano a separarle: STAND_IN / TRAGHETTATORE / ISOLATA-fuori-copertura

**categoria** `ambiguita-da-decidere` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `docs/DATI.md`, `docs/GLOSSARIO.md`

### Evidenza

Sui 3.609 mandati di una sola partita di tutto il dataset, tre feature calcolabili — l'allenatore dominante nelle 5 partite prima e nelle 5 dopo, e i giorni di stacco da quelle partite — danno: ISOLATA_FUORI_COPERTURA 2.412 (67%), TRAGHETTATORE 575, STAND_IN 264, AMBIGUO 236, TITOLARE_SPEZZATO 113, SOSPETTO_FONTE 9. Regola: dominante-prima == dominante-dopo, quota >=0,6 su entrambi i lati e stacco <=21 giorni -> STAND_IN (vice/squalifica/malattia); dominanti diversi e almeno un lato entro 21 giorni -> TRAGHETTATORE; stacco >45 giorni su ENTRAMBI i lati -> il club non e' coperto in quella stagione (una gara di coppa isolata), non e' un interim; dominante == l'allenatore stesso -> e' il TITOLARE spezzato dal suo secondo. VALIDAZIONE su una verita' indipendente — i 91 mandati di una partita del perimetro verificati caso per caso nel registro della Fase 141: STAND_IN 15/15 vice (IC95 Wilson 0,796-1,0), TRAGHETTATORE 31/33 traghettatore (0,94; IC95 0,804-0,983), ISOLATA 30/33 titolare (0,91; IC95 0,764-0,969), TITOLARE_SPEZZATO 2/2. E la causa dichiarata nelle note conferma la semantica: le 8 squalifiche e le 7 malattie cadono tutte in STAND_IN, i 35 esoneri tutti in TRAGHETTATORE. Per confronto, il flag `interruzione` da solo, su quelle 91, e' impuro: 44 delle 412 interruzioni globali di una partita sono in realta' il titolare (TITOLARE_SPEZZATO 40 + TRAGHETTATORE 41 + ISOLATA 24 + SOSPETTO 3 = 108 su 412 non sono uno stand-in). La terza classe che il compito ipotizzava — «errore della fonte» — praticamente NON esiste in forma dimostrabile: 9 casi su 3.609, tutti varianti di grafia del nome del dominante (nessun caso di allenatore uguale a quello avversario, a parte l'unica partita Odense-Naesby 2016 in cui la fonte mette lo stesso nome sulle due panchine).

### Riparazione proposta

Aggiungere a src/data/allenatori.py una funzione `classifica_mandati_brevi(partite, mandati, k=5, giorni_stacco=21, giorni_isolamento=45)` che restituisce la colonna `classe` con i cinque valori, e NON toccare `interruzione` (che resta la descrizione grezza, come vuole R3-in-spirito: marcare e' descrivere, classificare e' interpretare). Dichiarare nel docstring che la classe e' una DEDUZIONE con purezza misurata e intervallo, non un dato, e che la validazione vale sulle 91 righe caso_per_caso del perimetro — non su tutto il dataset. Decisione che spetta all'utente: se `ricuci` debba assorbire solo gli STAND_IN invece di tutte le interruzioni di una partita (oggi assorbe anche 24 gare isolate e 40 titolari).

### Guadagno atteso

Separa 264 stand-in veri da 2.412 artefatti di copertura: qualunque feature «e' cambiato l'allenatore» costruita sul flag grezzo conta oggi 3.609 eventi dove ne esistono 575+264.

---

## 6. FINTO PIENO nel registro della Fase 141: `ruolo` e' pieno al 100% ma per 896 righe su 1.190 e' un default, non una misura

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `data/allenatori_wikidata/registro_incarichi.csv`, `docs/DATI.md`

### Evidenza

registro_incarichi.csv ha `ruolo` valorizzato su tutte le 1.190 righe (titolare 1.104, traghettatore 63, vice 23) e nessun conteggio di celle vuote lo vede. Ma `verificato_da` vale 'wikidata' su 896 righe e 'caso_per_caso' su 294, e le due popolazioni non sono la stessa cosa: fra i 172 mandati di UNA partita, tutte e 81 le righe 'wikidata' hanno ruolo='titolare' e ZERO hanno vice o traghettatore, mentre le 91 'caso_per_caso' si dividono 36/37/18. Wikidata conferma la PERSONA e il suo mandato al club, non chi sedeva in panchina quella singola gara. Controesempio dimostrativo: Albert Stuivenberg, Arsenal, 01/01/2022, 1 partita, ruolo='titolare', verificato_da='wikidata' — ma il mandato precedente e successivo e' Arteta a 6 e 8 giorni di distanza, cioe' il caso da manuale del secondo che sostituisce il titolare. Comando: python -c "import pandas as pd;r=pd.read_csv('data/allenatori_wikidata/registro_incarichi.csv');print(pd.crosstab(r.verificato_da,r.ruolo));print(pd.crosstab(r[r.partite==1].verificato_da,r[r.partite==1].ruolo))"

### Riparazione proposta

Non riscrivere i valori (R3). Aggiungere alla funzione incarichi_verificati() un avviso esplicito nel docstring — «`ruolo` e' una misura solo dove verificato_da=='caso_per_caso' (294 righe su 1.190); sulle 896 righe 'wikidata' e' il valore di default e non distingue titolare da vice» — e, se serve un'etichetta usabile, esporre `ruolo_misurato` che sia NaN sulle righe wikidata. Chiunque valuti un classificatore contro questa colonna deve filtrare prima, altrimenti misura il proprio accordo con un default (nel mio caso: purezza apparente di STAND_IN 16/20 su tutte le righe contro 15/15 sulle sole misurate).

### Guadagno atteso

Evita che la prossima fase «validi» un modello di ruolo contro un default e ne concluda che funziona.

---

## 7. esperienza_prima() e' R8-sicura contro il futuro — dimostrato, non assunto — ma perde per IDENTITA': michel al 1/1/2023 ha 281 partite che sono due persone

**categoria** `alias-mancante` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `tests/test_allenatori.py`, `data/allenatori_wikidata/persone_qid.csv`

### Evidenza

Ho provato a romperla in tre modi e non si e' rotta: (1) troncando il dataset a date<as_of, 0 celle divergenti su 41.560; (2) iniettando 5.000 partite datate 2030 a un allenatore reale, 0 celle cambiate; (3) creando una competizione nuova che nasce nel 2031, 0 celle cambiate. Il motivo e' dimostrabile e non casuale: l'unico punto che legge tutto il frame e' _inizio_competizioni(), ma il minimo di una competizione calcolato su tutti i dati coincide con quello calcolato sui soli dati passati ogni volta che la competizione ha almeno una riga prima di as_of — ed e' sempre cosi', perche' il bordo serve solo per la competizione dell'esordio, che per definizione e' precedente. Controprova che il test e' sensibile: spostando INDIETRO il bordo della Serie A con una riga passata, `censurata` cambia per 7 allenatori. Il confine e' stretto giusto (< e non <=): al 2020-01-01 nigel pearson ha 49 partite_prima, 49 con date<as_of e 50 con date<=as_of. Il buco e' un altro: la chiave e' il nome, e per gli 11 omonimi l'esperienza si somma. Al 1/1/2023 'michel' ha partite_prima=281 su 8 club — ma la Fase 141 ha gia' sciolto che sono Michel Sanchez (Rayo 31 + Huesca 22 + Girona 21 = 74) e Michel Gonzalez (Olympiakos 105 + Marsiglia 40 + Malaga 33 + Siviglia 21 + Getafe 8 = 207). Per l'allenatore del Girona in Liga la feature dichiara 281 invece di 74: +280%. Idem 'luis castro', 190 partite su 6 club. Comando: python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;t=A.load_partite();e=A.esperienza_prima('2023-01-01',t);print(int(e.loc['michel','partite_prima']));print(t[(t.manager_key=='michel')&(t.date<'2023-01-01')].club_name.value_counts())"

### Riparazione proposta

Due cose separate. (a) Scrivere nel docstring che la R8-sicurezza e' DIMOSTRATA (con i tre test) e aggiungere quei tre test in tests/ come guardiani permanenti — CLAUDE.md §5-bis R8 nota che la regola anti-look-ahead non aveva un test, e qui il test e' gratis. (b) Dare a esperienza_prima() un parametro opzionale `identita: dict[str,str] | None` che rimappa manager_key -> Q-id prima del groupby, alimentato da data/allenatori_wikidata/persone_qid.csv (che esiste gia'): con l'identita' esterna gli 11 omonimi smettono di sommarsi. Finche' non c'e', la funzione dovrebbe almeno restituire una colonna `chiave_ambigua` a True per le 11 chiavi in conflitto, cosi' chi costruisce una feature lo sa.

### Guadagno atteso

Il flag ambiguo costa nulla e copre 2 chiavi su 494 nel perimetro; la rimappa Q-id le azzera. Nessun guadagno predittivo atteso — l'allenatore non e' mai stato misurato su alcun mercato.

---

## 8. esperienza_prima() non distingue «debuttante» da «chiave non agganciata»: 151 allenatori del perimetro su 494 non hanno NESSUNA riga alla loro prima partita

**categoria** `assenza-a-monte` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/allenatori.py`, `tests/test_allenatori.py`

### Evidenza

La funzione ritorna solo gli allenatori con almeno una partita precedente ad as_of. Chiamandola alla data della prima partita nel perimetro di ognuno dei 494 allenatori: 151 non compaiono affatto nell'output (nessuna riga) e 120 compaiono con censurata=True. Un chiamante che faccia left-join e riempia con 0 ottiene «esordiente assoluto» sia per il vero debuttante sia per l'allenatore la cui chiave non ha agganciato — e i due casi sono indistinguibili a valle. E' la stessa famiglia del finto pieno (R6): lo zero che significa «non lo so». Comando: python -c "import sys;sys.path.insert(0,'.');from src.data import allenatori as A;t=A.load_partite();p=t[t.is_top5&t.season.isin(A.STAGIONI)];pr=p.groupby('manager_key').date.min();d=sum(1 for k,x in pr.items() if k not in A.esperienza_prima(x,t,manager_keys=[k]).index);print(d,len(pr))"

### Riparazione proposta

Far restituire a esperienza_prima() una riga anche per le chiavi richieste esplicitamente via `manager_keys` ma senza passato, con partite_prima=0 e una colonna `esordio_assoluto=True`; e documentare che l'assenza dall'output non e' mai da riempire con 0 dal chiamante. In alternativa, un parametro `reindex_su=` con l'elenco delle chiavi attese.

---

## 9. SofaScore: lo storico dell'arbitro E' al momento dell'estrazione — sospetto R8 CONFERMATO con margine 45:1

**categoria** `look-ahead` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `files/sofascore_coppe_europee_2526/README.md`, `docs/DATI.md`

### Evidenza

Prova diretta e non aggirabile: se «Partite arbitro» fosse il totale al momento della partita, per un arbitro con n partite nel file il valore dovrebbe crescere di almeno n-1 fra la prima e l'ultima. Misurato sui 179 arbitri con piu' di una partita: crescita OSSERVATA totale 15, crescita ATTESA se fosse as-of-match 684 — rapporto 1:45,6 — e 0 arbitri su 179 raggiungono la crescita attesa. Il piu' esposto e' Daniel Siebert: 12 partite dal luglio 2025 al 2026 e «Partite arbitro» costante a 455; idem Joao Pedro Pinheiro (12 partite, 383) e Danny Makkelie (11, 578). 164/179 hanno il valore ESATTAMENTE costante, e i 15 che variano variano di 1 sola unita' e NON in modo crescente col tempo (Spearman mediano fra data e valore -0,31): e' rumore di scraping, non un aggiornamento. Anche sugli arbitri con oltre 200 giorni fra prima e ultima partita nel file, 48/52 sono costanti. Controllo indipendente: il valore dichiarato supera il nostro conteggio da games.csv all'11/08/2026 con mediana +76 partite (competizioni che noi non copriamo) e non e' mai inferiore in 156 casi su 161. Comando: python -c "import pandas as pd;p=pd.read_excel('files/sofascore_coppe_europee_2526/originale_sofascore.xlsx','Partite');g=p.dropna(subset=['Arbitro']).groupby('Arbitro')['Partite arbitro'].agg(['size','min','max']);g=g[g['size']>1];print(int((g['max']-g['min']).sum()),int((g['size']-1).sum()),len(g))" -> 15 684 179

### Riparazione proposta

Il README della raccolta dichiara gia' il sospetto: va promosso da sospetto a FATTO MISURATO, con questi numeri, e le quattro colonne (Partite/Gialli/Rossi/Doppi gialli arbitro + Gialli per partita) vanno marcate `post` nel catalogo di docs/DATI.md — non `pre` — con la nota che sono un'unica istantanea all'11/08/2026 uguale per tutte le 912 righe di quell'arbitro. La ricostruzione R8-sicura e' possibile solo PARZIALMENTE: contando dalle nostre fonti si ottiene la carriera visibile al dataset (mediana 76 partite in meno della vera), quindi va esposta col nome giusto — `partite_arbitro_visibili_prima`, come esperienza_prima() fa per gli allenatori — e mai chiamata «carriera».

### Guadagno atteso

Impedisce un look-ahead che avrebbe un numero perfettamente plausibile: 4 colonne x 912 partite = 3.648 celle oggi utilizzabili per sbaglio.

---

## 10. OCCASIONE: gli allenatori agganciano il blocco SofaScore al repo senza la tabella di alias che il README dichiara necessaria — 728/912 partite, 728/728 punteggi identici, 183 alias squadra a zero ambiguita'

**categoria** `assenza-a-monte` · **rischio** `basso` · **riparabile ora** `True`

**File**: `scripts/aggancia_sofascore.py`, `src/data/sources.py`, `files/sofascore_coppe_europee_2526/README.md`

### Evidenza

Aggancio degli allenatori: le 1.824 celle Allenatore casa/trasferta sono piene al 100%, danno 280 chiavi distinte dopo normalizza_nome, di cui 243 (86,8%) esistono gia' in games.csv; a livello di celle 1.666/1.824 = 91,3%, e 764/912 partite (83,8%) hanno ENTRAMBI gli allenatori agganciati. Nessuna delle chiavi agganciate e' fra gli 11 omonimi dimostrati. Da qui il ponte: la chiave (data, manager_key casa, manager_key trasferta) aggancia 728 delle 912 partite a un game_id di games.csv, e su tutte e 728 il punteggio dei 90' coincide (728/728, zero eccezioni; la tolleranza +-1 giorno non aggiunge nulla, quindi non c'e' ambiguita' di fuso). Delle 184 non agganciate, 148 hanno un allenatore fuori dal nostro universo e 36 sono partite che games.csv non contiene (turni preliminari minori: 2o turno 47, spareggi 29, 3o turno 25, 1o turno 15). Sottoprodotto: dai 728 agganci si ricava una tabella di alias squadra di 183 nomi SofaScore -> club_id con 0 nomi ambigui (nessuno mappa su due club_id diversi) su 1.456 lati di partita, che copre 37 delle nostre 96 squadre 2025-26 — cioe' tutte quelle che hanno giocato in Europa. Il README dichiara «finche' non c'e' [la tabella di alias verificata a mano], questi dati non si agganciano al resto del repo»: e' vero per il nome della squadra, falso per la partita. Comandi nel corpo della diagnosi (join su tutte=A.load_partite() lato casa contro il foglio Partite).

### Riparazione proposta

Scrivere scripts/aggancia_sofascore.py sul modello di scripts/aggancia_coppe.py: prima il ponte partita->game_id via (data, allenatore casa, allenatore trasferta), poi la tabella di alias squadra DERIVATA dal ponte (non scritta a mano, quindi non ipotizzata) e verificata con le due guardie che l'hanno gia' superata — nessun nome SofaScore su due club_id, e punteggio identico su tutti gli agganci. Le 184 partite non agganciate restano dichiarate vuote, come vuole la regola d'oro degli agganci: un aggancio ambiguo non si sceglie a caso.

### Guadagno atteso

728 partite europee 2025-26 collegate al resto del repo, con formazioni, eventi al minuto, tiri con xG e statistiche per periodo — cioe' il primo dato UEFA usabile del progetto — al costo di uno script, senza una sola riga di alias scritta a mano.

---

## 11. 37 nomi di allenatore non agganciano, e i piu' costosi non sono errori di grafia ma FORME DI NOME diverse: Adi Hutter e Hansi Flick perdono tutte le loro 14 partite

**categoria** `alias-mancante` · **rischio** `medio` · **riparabile ora** `False`

**File**: `src/data/sources.py`, `files/sofascore_coppe_europee_2526/README.md`, `tests/`

### Evidenza

Delle 280 chiavi SofaScore, 37 non esistono in games.csv (158 celle). Dieci sono varianti di grafia che normalizza_nome non copre perche' non sono accenti ma traslitterazioni o spaziature: jeton bekiri/bekjiri (16 celle), leeroy echteld/lee roy echteld (6), radomir dalovic/djalovic (6), srdan blagojevic/srdjan (6), per mathias hogmo/hogmo (6), dmitri molosh/dmitriy molosh (2), lukasz/lukasz tomczyk (2), tugberk tanrivermis (2), dan romann/dan roman (1), yevhenii/yevgen kalynychenko (1). Le altre 27 non hanno nessun quasi-omonimo sopra 0,90, e almeno tre sono nostri allenatori sotto il nome anagrafico completo: 'adolf hutter' = adi hutter (Monaco), 'hans dieter flick' = hansi flick (Barcellona), 'ioan ovidiu sabau' = ovidiu sabau — in ognuno dei tre casi il cognome ha UN solo portatore nel nostro universo (16 dei 37 hanno questa proprieta'). Costo misurato: tutte e 14 le partite europee di Barcellona e Monaco presenti nel file cadono fra le 184 non agganciate, cioe' il 100% delle partite di due nostre squadre di prima fascia, per una sola forma del nome. Comando: python -c "import sys,difflib,pandas as pd;sys.path.insert(0,'.');from src.data import allenatori as A;t=A.load_partite();p=pd.read_excel('files/sofascore_coppe_europee_2526/originale_sofascore.xlsx','Partite');k=pd.concat([p['Allenatore casa'],p['Allenatore trasferta']]).map(A.normalizza_nome);g=set(t.manager_key);m=[x for x in sorted(set(k)) if x not in g];print(len(m));print([(x,difflib.get_close_matches(x,g,1,0.90)) for x in m])"

### Riparazione proposta

Un MANAGER_ALIASES esplicito in src/data/sources.py accanto a TEAM_ALIASES, riga per riga con la fonte del controllo — non un fuzzy automatico: il README della raccolta ha gia' misurato che il fuzzy sulle SQUADRE produce Alaves->Ilves e Angers->Rangers, e sui nomi di persona il rischio e' identico (dan romann ~ dan roman e' un candidato, non una prova). Il match per cognome unico va usato solo come GENERATORE di candidati da far confermare a mano, e i 21 che restano ambigui vanno lasciati vuoti. Attenzione a non allargare normalizza_nome: aggiungere la traslitterazione dj->d o la rimozione degli spazi cambierebbe le chiavi di TUTTO il modulo (13.810 mandati) per riparare 158 celle di un altro file — il rischio e' asimmetrico nel verso sbagliato.

### Guadagno atteso

Circa 148 delle 184 partite oggi non agganciate diventano agganciabili, fra cui le 14 di Barcellona e Monaco. Ma il lavoro e' a mano e va confermato caso per caso: non e' riparabile in questa sessione senza violare la regola d'oro degli agganci.

---
