# Le carriere

> Dominio come dichiarato dall'agente: **Carriere (src/data/careers.py, wikipedia_careers.py, wikidata_identity.py, data/carriere_wikipedia/)**

> 17 reperti. Diagnosi del 2026-08-11, workflow `wf_93f8ba67-2b8`.

> ⚠️ **Nessuno di questi reperti è stato verificato in modo avversariale**
> (la fase di verifica è stata interrotta dal limite di sessione): vanno letti
> come *misure da confermare*, non come conclusioni. Vedi `00_indice.md`.

---

## Il riepilogo dell'agente

Il database carriere e' una tabella unica da due fonti disomogenee (197.813 righe appearances a data esatta + 209.809 tappe Wikipedia a grana anno = 407.622), tenute insieme da tre join fragili: il player_id verso Wikipedia (per NOME, quindi omonimi), il club_id verso Wikipedia (per SOMIGLIANZA di token, quindi falsi positivi «univoci»), e la grana temporale (anno contro giorno, quindi righe indistinguibili). Il progetto ha costruito difese serie su tutti e tre — verifica d'identita' gerarchica, Agganciatore che rifiuta l'ambiguo, career_before per la R8 — e le difese funzionano. Il difetto dominante non e' nelle difese: e' che la pipeline si e' FERMATA A META'. La raccolta Wikipedia e' proseguita dopo che erano stati costruiti il file dei Q-id (24.413 righe su 29.816 tentativi) e la selezione dei casi da dirimere, e nessuno dei due e' stato rigenerato: 92 giocatori dubbi non sono mai stati verificati, 41 sono esclusi dal database pur essendo decidibili con dati gia' su disco, e i numeri pubblicati (483 in limbo, «la bday a volte non c'e'», i limiti misurati sul lotto pilota di 60) descrivono uno stato che non esiste piu'. Il secondo problema, indipendente, e' che l'avvertenza «non sommare le presenze fra le due fonti» e' scritta in tre docstring e non e' presidiata da una sola riga di codice o di test: la somma ingenua gonfia 22.637 giocatori su 22.665.

---

## 1. Il 483 non regge: oggi i giocatori in limbo sono 555 (+14,9%)

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/wikidata_identity.py`, `src/data/careers.py`, `docs/DATI.md`

### Evidenza

Misurato: 295 quarantena + 260 respinta = 555, contro i 483 dichiarati in src/data/wikidata_identity.py riga 10 e i «483, non 24.000» di riga 26. Il 483 era un'istantanea del 01/08/2026 con la raccolta ANCORA IN CORSO (docs/AUDIT_DATABASE_CARRIERE.md riga 25 dichiara il deliverable passato da 16.483 a 54.001 righe in due ore; oggi sono 209.809 righe su 29.816 tentativi). Comando: python -c "import pandas as pd; e=pd.read_csv('data/carriere_wikipedia/esiti_riepilogo.csv',low_memory=False); print(e.identita.value_counts().reindex(['quarantena','respinta']).to_string(), '| tot', int(e.identita.isin(['quarantena','respinta']).sum()))"

### Riparazione proposta

Sostituire il numero fisso con la sua data e il modo di ricalcolarlo: «al 01/08/2026 erano 483 a raccolta in corso; sul deliverable di HEAD sono 555 — ricalcolabile col comando qui accanto». Stessa correzione nel commento di careers.py riga 255 («solo 483 giocatori sono stati dirimenti» -> 477 verdetti, di cui 463 sul limbo e 14 su confermata_club). Regola generale gia' scritta nell'audit e non applicata qui: ogni numero dello strato Wikipedia vale solo alla sua data.

### Guadagno atteso

Nessun guadagno di modello. Toglie il numero che ha fatto partire questa indagine nella direzione sbagliata: chi legge «483» crede che il fronte sia chiuso al 96% (477/483) quando la copertura vera e' 463/555 = 83,4%.

---

## 2. La causa dichiarata del limbo e' FALSA: la bday HTML c'e' in 555 casi su 555

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/wikidata_identity.py`, `docs/DATI.md`

### Evidenza

wikidata_identity.py righe 6-10 dice che il limbo nasce perche' «quando il markup non c'e' — infobox senza bday, template diverso, data solo in prosa — il confronto e' impossibile». Misurato sul limbo: bday_pagina e' NON NULLA in 555/555, e parsabile come data ISO in 554/555 (l'unica eccezione e' Konstantinos Panagiotou, player_id 682959, con bday «1937», precisione all'anno). Manca invece la NOSTRA data (players.csv) in 3 casi su 555. Il limbo nasce da una DISCORDANZA, non da un'assenza: scarto mediano 51 gg in quarantena, 3.419 gg fra le respinte. Comando: python -c "import pandas as pd; e=pd.read_csv('data/carriere_wikipedia/esiti_riepilogo.csv',low_memory=False); l=e[e.identita.isin(['quarantena','respinta'])]; print('bday assente:',int(l.bday_pagina.isna().sum()),'| nostra data assente:',int(l.nascita_attesa.isna().sum()),'| tot',len(l))"

### Riparazione proposta

Riscrivere il blocco PERCHE' ESISTE di wikidata_identity.py con la causa misurata: «la verifica HTML mette in limbo quando le due date DISCORDANO (554/555) o quando manca la nostra (3/555); il caso 'markup assente' e' zero nel perimetro raccolto». La differenza non e' cosmetica: se la causa fosse l'assenza, l'unica via sarebbe una terza fonte (rete); essendo una discordanza, il dato per decidere e' gia' in casa (vedi difetto seguente).

### Guadagno atteso

Riapre a costo zero un fronte che il documento dichiara chiudibile solo con la rete.

---

## 3. La regola persona_diversa applicata alla bday HTML riproduce il verdetto Wikidata al 99,8%: le 477 richieste di rete non servivano

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `docs/DIARIO.md`, `docs/PANCHINA.md`, `src/data/wikidata_identity.py`, `scripts/verifica_identita_wikidata.py`

### Evidenza

Validazione sui 456 casi in cui esiste ENTRAMBE le cose (bday HTML gia' su disco + verdetto Wikidata da rete): la regola WD.persona_diversa(forma_discrepanza(bday_html, nostra_data), scarto) concorda col verdetto Wikidata su 455/456 = 99,78% IC95 [98,8%, 100%]; precisione 145/146, richiamo 145/145. Un solo disaccordo su 456. Lo script scratchpad che lo ricalcola e' riprodotto qui: carica esiti_riepilogo.csv + verdetti_wikidata.csv.gz, calcola forma_discrepanza(bday_pagina, nascita_attesa) e confronta con (esito=='smentita' & persona_diversa).

### Riparazione proposta

NON e' una proposta di sostituire Wikidata (P569 e' strutturata e resta la fonte migliore, e la militanza P54 dara' altro). E' un risultato da mettere a verbale in DIARIO/PANCHINA e da usare come PRIMO passaggio: si decide offline con la forma HTML, e si spende rete solo sui casi grigi. Sul perimetro attuale questo porta le richieste necessarie da 92 a 11 (-88%). Regola: prima di pagare una fonte nuova, misurare quanto ne resta gia' in casa — qui non e' mai stato fatto, e il costo e' stato 477 richieste per 1 caso di guadagno.

### Guadagno atteso

Il costo di ogni verifica futura scende di un ordine di grandezza, e la verifica diventa eseguibile senza rete (oggi non lo e': la cache HTML e la cache Wikidata non sono versionate e in questo container non esistono).

---

## 4. 25 respinte con verdetto «smentita» ma forma STRUTTURATA restano fuori dal database, e FORME_STRUTTURATE e' una costante MORTA

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `False`

**File**: `scripts/export_wikipedia_careers.py`, `src/data/wikidata_identity.py`, `tests/test_careers.py`, `docs/DATI.md`

### Evidenza

wikidata_identity.py righe 282-286 definisce FORME_STRUTTURATE (le forme che il modulo stesso documenta come «firme di refuso», non di persona diversa) e NESSUNO la usa: grep FORME_STRUTTURATE su tutto il repo da' 1 sola occorrenza, la definizione. Conseguenza misurata: 180 giocatori hanno esito «smentita» senza persona_diversa; 136 sono in quarantena e RESTANO nel database (voluto, e docs/DATI.md lo dichiara), 44 sono respinte e restano FUORI. Di quelle 44, 25 hanno forma strutturata — 4 scambio_giorno_mese, 20 stesso_anno_*, 1 stesso_giorno_mese_anno_diverso — con scarto mediano 61 gg. Caso conclamato: player_id 19979, Q313441, 1982-06-07 contro 1982-07-06, scambio giorno/mese, 29 giorni. La stessa evidenza produce esiti opposti a seconda di un criterio (copertura-club >=50%) che l'audit del progetto definisce inaffidabile («il nome di un club non identifica nessuno», docs/AUDIT_DATABASE_CARRIERE.md riga 94).

### Riparazione proposta

In scripts/export_wikipedia_careers.py, dove oggi c'e' solo `elif bool(vd['persona_diversa']): dentro=False`, aggiungere il ramo simmetrico: se il verdetto e' «smentita» MA la forma sta in WD.FORME_STRUTTURATE, la riga rientra con identita='confermata_wikidata_forma' (etichetta NUOVA, non 'confermata_wikidata': l'evidenza e' piu' debole e deve restare distinguibile a valle). Prerequisito bloccante: serve data/carriere_wikipedia/esiti.jsonl, che non e' versionato (vedi difetto dedicato).

### Guadagno atteso

25 giocatori rientrano con la carriera pre-2012. Ordine di grandezza: la mediana e' ~9 tappe a testa, quindi ~200-250 tappe. Il rischio residuo e' che 1-2 siano davvero altre persone: contenuto dall'etichetta separata.

---

## 5. 3 respinte hanno bday HTML e P569 di Wikidata IDENTICHE, e sono escluse perche' manca la NOSTRA data

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `False`

**File**: `src/data/wikipedia_careers.py`, `scripts/export_wikipedia_careers.py`, `tests/test_careers.py`

### Evidenza

player_id 299 (Q160890, 1979-05-30), 42463 (1989-04-12), 16565 (1988-01-07): in tutti e tre bday_pagina == nascita_wikidata alla cifra, e nascita_attesa (players.csv) e' NaN. Due fonti indipendenti — l'HTML della pagina e l'entita' Wikidata della stessa pagina — concordano; il verdetto e' «indeterminato» e lo stato resta «respinta», quindi le tappe sono fuori dal database. E' la stessa classe di errore gia' diagnosticata dall'audit sul ramo k==0 (docs/AUDIT_DATABASE_CARRIERE.md riga 52: «confonde PROVA CONTRARIA e ASSENZA DI PROVA»), qui su un ramo diverso. Comando: python -c "import pandas as pd; e=pd.read_csv('data/carriere_wikipedia/esiti_riepilogo.csv',low_memory=False); v=pd.read_csv('data/carriere_wikipedia/verdetti_wikidata.csv.gz'); m=e.merge(v[['player_id','esito']],on='player_id'); s=m[(m.esito=='indeterminato')&(m.identita=='respinta')]; print(s[['player_id','bday_pagina','nascita_wikidata','nascita_attesa']].to_string())"

### Riparazione proposta

In wikipedia_careers.verifica_identita, il ramo `if a is None or b is None` tratta allo stesso modo «manca la data di Wikipedia» e «manca la nostra». Non sono la stessa cosa: se manca la NOSTRA, non abbiamo prova contraria — non abbiamo proprio il confronto, e respingere significa perdere un dato per un buco che sta da noi. Aggiungere uno stato esplicito `nostra_data_assente` (dentro il database, dichiarato) invece di respinta. Verifica indipendente disponibile a costo zero prima di applicarlo: controllare che l'ultimo anno delle militanze P54 non preceda la nostra prima presenza (ramo 2 di wikidata_identity.verifica, che su questi tre non ha trovato incompatibilita').

### Guadagno atteso

3 giocatori, ma soprattutto chiude la classe: oggi la regola non distingue un buco nostro da una smentita, e ogni giocatore futuro senza date_of_birth in players.csv (25 su 29.816) prendera' la stessa strada.

---

## 6. 92 dei 555 non sono MAI stati verificati: il file dei Q-id e' fermo a meta' raccolta

**categoria** `bug-codice` · **rischio** `basso` · **riparabile ora** `True`

**File**: `scripts/verifica_identita_wikidata.py`, `data/carriere_wikipedia/wikidata_qid.csv.gz`, `src/data/wikidata_identity.py`

### Evidenza

463 dei 555 hanno un verdetto Wikidata, 92 no (56 respinte + 36 quarantena). Causa misurata: 88 dei 92 non compaiono affatto in wikidata_qid.csv.gz, e gli altri 4 ci sono con l'identita' vecchia («non_verificata»), quindi il filtro `q[q.identita.isin(DA_DIRIMERE)]` di scripts/verifica_identita_wikidata.py non li seleziona. In generale il file dei Q-id copre 24.413 dei 29.816 giocatori tentati: 5.117 mancano (1.672 dei quali con stato ok) e 253 righe portano un'identita' ormai superata. Il file e' stato costruito il 01/08 dalla cache HTML a raccolta in corso e non e' mai stato rigenerato. Comando: python -c "import pandas as pd; e=pd.read_csv('data/carriere_wikipedia/esiti_riepilogo.csv',low_memory=False); q=pd.read_csv('data/carriere_wikipedia/wikidata_qid.csv.gz'); print('esiti',len(e),'qid',len(q),'| mancanti',int((~e.player_id.isin(q.player_id)).sum()),'| limbo senza qid',int(e[e.identita.isin(['quarantena','respinta'])&~e.player_id.isin(q.player_id)].shape[0]))"

### Riparazione proposta

Due passi, in quest'ordine. (1) Offline, subito: applicare ai 92 la regola persona_diversa sulla bday HTML — validata al 99,8% qui sopra. Decide 81 casi su 92: 36 respinte confermate come persone diverse (gia' fuori, giustamente) e 45 con forma strutturata = refuso, di cui 13 respinte oggi ESCLUSE che vanno recuperate. (2) Rigenerare wikidata_qid.csv.gz dalla cache HTML e ri-lanciare la verifica sui soli 11 grigi. Nota di processo: il vero difetto e' che il file dei Q-id non dichiara la propria data ne' la propria copertura, quindi nessuno si accorge che e' vecchio. Aggiungere una guardia in verifica_identita_wikidata.py che confronti len(qid) con len(esiti) e si fermi se divergono.

### Guadagno atteso

Il passo (1) e' offline e recupera 13 giocatori; il passo (2) costa 11 richieste di rete invece delle 92 che servirebbero senza il passo (1). In totale, con i 25+3 degli altri difetti: 41 giocatori recuperabili, 11 casi residui.

---

## 7. Il segnaposto 0000 di Wikipedia sopravvive nel deliverable come anno_a, e il test che dovrebbe fermarlo guarda solo anno_da

**categoria** `finto-pieno` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `tests/test_careers.py`, `scripts/export_wikipedia_careers.py`

### Evidenza

1 riga: player_id 484215 (Toby Sibbick), club «Feltham», anno_da NaN, anno_a = 0.0, giovanili. E' esattamente il finto pieno raccontato in data/carriere_wikipedia/README.md righe 87-110 («0000 come segnaposto quando l'anno e' ignoto») e che il fix di wikipedia_careers._parse_anni righe 209-212 copre su ENTRAMBI gli estremi — ma il deliverable accumula righe scritte da versioni diverse del parser lungo ore di raccolta, e la guardia d'uscita di export_wikipedia_careers.py controlla solo `anno_a < anno_da`, che qui e' False perche' anno_da e' NaN. Il test tests/test_careers.py::test_strato2_struttura_delle_tappe asserisce `not (w['anno_da']==0).any()` e non dice nulla su anno_a. Comando: python -c "import pandas as pd; t=pd.read_csv('data/carriere_wikipedia/tappe.csv.gz',low_memory=False); print(int((t.anno_a==0).sum()), t[t.anno_a==0][['player_id','club','anno_da','anno_a','source_url']].to_string())"

### Riparazione proposta

Tre righe, nessuna delle quali basta da sola: (a) nel test, aggiungere `not (w['anno_a']==0).any()` accanto all'assert esistente; (b) nella guardia d'uscita dell'export, azzerare a NA gli anni == 0 su entrambe le colonne prima di scrivere; (c) documentare il principio: una guardia d'uscita che presidia una sola direzione di un invariante simmetrico e' meta' guardia.

### Guadagno atteso

1 riga corretta oggi; la classe chiusa per sempre. Il valore e' nel test: e' il difetto che rientra in silenzio a ogni ri-export.

---

## 8. Nessuna guardia sul RANGE FISICO degli anni: 9 tappe fuori dal calendario possibile (fino al 2205)

**categoria** `finto-pieno` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/wikipedia_careers.py`, `scripts/export_wikipedia_careers.py`, `tests/test_careers.py`

### Evidenza

8 tappe con anno_a > 2026 e 1 con anno_da > 2026: Clement Libertiaux/Francs Borains 2024-2205, David Crespo/Mafra 2016-2107, Sanel Saljic/Admira Wacker 2014-2028, Darijo Grujcic/Dornbirn 2017-2028, Edan Diop/Chambray 2014-2027, Yannick Eduardo/ADO Den Haag 2026-2027, Valy Konate/Cercle Brugge 2025-2027, Conor McAleny/Marine 2026-2027, e Aleksandr Sandrachuk/SDYuSShOR con anno_da = 2080. Sono refusi della fonte (stessa classe degli intervalli rovesciati gia' gestiti), ma qui non c'e' nessuna guardia: il test controlla `anno_da >= 1900` e non pone tetto. Il numero e' un intero valido e la cella e' piena — nessun conteggio di completezza lo vede. Comando: python -c "import pandas as pd; t=pd.read_csv('data/carriere_wikipedia/tappe.csv.gz',low_memory=False); print(t[(t.anno_da>2026)|(t.anno_a>2026)][['player_id','club','anno_da','anno_a','source_url']].to_string())"

### Riparazione proposta

Stesso trattamento gia' scelto per gli intervalli rovesciati, e per lo stesso motivo (l'anno giusto non lo sappiamo, indovinarlo sarebbe inventare): azzerare a NA l'estremo fuori range invece di correggerlo. Tetto = anno corrente + 1 (una tappa firmata puo' legittimamente arrivare all'anno prossimo). Va sia in _parse_anni sia nella guardia d'uscita dell'export, per lo stesso motivo del difetto precedente. Aggiungere l'assert nel test.

### Guadagno atteso

9 celle. Il valore e' la classe: e' l'argomento della nota finale del README («test sui RANGE FISICI dei dati, non solo sulla forma»), scritta e poi applicata a un solo estremo di una sola colonna.

---

## 9. gol = -63: la regex delle presenze accetta il segno meno

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/wikipedia_careers.py`, `scripts/export_wikipedia_careers.py`, `tests/test_careers.py`

### Evidenza

1 riga: player_id 678503 (Danylo Varakuta), Chornomorets Odesa 2020-2024, presenze 39, gol -63. Causa nel codice: wikipedia_careers._RE_NUM = re.compile(r'-?\\d+') cattura il trattino, e _parse_intero lo restituisce. Su una cella tipo «39 (-63)» o con un trattino tipografico residuo il risultato e' un intero negativo, che nessuna guardia rifiuta. Comando: python -c "import pandas as pd; t=pd.read_csv('data/carriere_wikipedia/tappe.csv.gz',low_memory=False); print(t[t.gol<0][['player_id','club','anno_da','anno_a','presenze','gol','source_url']].to_string())"

### Riparazione proposta

Togliere il `-?` dalla regex: presenze e gol sono conteggi, un negativo non e' un valore raro, e' un valore impossibile. Piu' la guardia d'uscita `presenze >= 0 and gol >= 0` (altrimenti NA) e l'assert nel test. Attenzione a non 'correggere' in valore assoluto: 63 potrebbe non essere il numero giusto.

### Guadagno atteso

1 cella; classe chiusa.

---

## 10. 7 tappe dichiarano 0 presenze e gol > 0 — combinazione impossibile, nessuna guardia

**categoria** `finto-pieno` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `scripts/export_wikipedia_careers.py`, `src/data/wikipedia_careers.py`, `tests/test_careers.py`

### Evidenza

Abdoul Kader Bamba/Granada 2026: 0 presenze, 8 gol. Fabio Lucioni/Ternana 2009-10: 0 e 6. Bamba Anderson/Tombense: 0 e 2. Bahadir Gungordu/Trabzonspor: 0 e 1. Nico Fernandez/Olimpo: 0 e 3. Jacob Devaney/Manchester United 2025: 0 e 1. Jonas Auer/Slavia Praga: 0 e 4. Il 4-1 di questa combinazione e' che dimostra, con informazione interna alla riga stessa, che almeno uno dei due numeri NON e' una misura — probabilmente uno slittamento di colonna nell'infobox (le celle vengono lette per posizione, celle[2] e celle[3], senza controllare l'intestazione). Comando: python -c "import pandas as pd; t=pd.read_csv('data/carriere_wikipedia/tappe.csv.gz',low_memory=False); print(t[(t.presenze==0)&(t.gol>0)][['player_id','club','anno_da','anno_a','presenze','gol','source_url']].to_string())"

### Riparazione proposta

Guardia d'uscita: se presenze == 0 e gol > 0, mettere ENTRAMBI a NA (non uno dei due — non sappiamo quale sia sbagliato) e contare le righe colpite nel log dell'export. Un test che asserisce l'assenza della combinazione. Diagnosi a monte, se un giorno si rifa' la raccolta: parse_career legge celle[2]/celle[3] per posizione; leggerle per intestazione (Apps/Gls) chiuderebbe la causa invece del sintomo.

### Guadagno atteso

7 righe. Vale come sentinella: e' l'unico controllo che intercetta lo slittamento di colonna senza rileggere l'HTML.

---

## 11. «presenze = 0» NON e' un finto pieno: misurato, e va scritto (R4)

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `docs/DATI.md`, `data/carriere_wikipedia/README.md`, `docs/DIARIO.md`

### Evidenza

Sospetto legittimo — 11.134 tappe senior con presenze == 0 (6,40%) — e smentito. Test costruito con informazione indipendente (strato 1, competizioni TOP5, dove Wikipedia e appearances contano per forza le stesse partite): su un perimetro conservativo di 8.412 tappe CHIUSE 2013-2024, club agganciato univoco, escluse le tappe che condividono (giocatore, club) con un'altra tappa, e con presenze TOP5 misurate > 0 nello strato 1, gli zeri falsificati sono 1 su 8.412 = 0,012% IC95 [0,002%, 0,067%] (Koray Gunter, Borussia Dortmund 2013-14, 1 presenza). Lo zero e' vero: e' il giocatore sotto contratto che non e' mai sceso in campo nel campionato nazionale (Filipe Luis all'Ajax 2004-08, Fraser Forster al Newcastle 2006-12, Abate al Milan 2003-07). ⚠️ Una misura ingenua dava 56/10.691 = 0,52%: erano tutte righe di contratto sovrapposte allo stesso club (Bruno Fernandes ha DUE tappe Sampdoria, il prestito con 33 presenze e l'acquisto con 0), non zeri falsi. La differenza fra le due misure e' interamente l'artefatto descritto nel difetto seguente.

### Riparazione proposta

Scrivere il risultato negativo con il suo perimetro e il suo intervallo in docs/DATI.md e nel README della cartella, come contro-esempio: «lo 0 di presenze e' un dato, non un 'non lo so' — misurato». Serve perche' il sospetto e' ovvio e la prossima sessione lo rifara' da capo, e perche' senza il perimetro qualcuno 'correggera' 11.134 celle buone. Nota metodologica da riportare: la prima misura era gonfiata 43 volte dall'aliasing di grana, non dal dato.

### Guadagno atteso

Nessuno diretto. Evita una correzione sbagliata su 11.134 celle e un esperimento rifatto.

---

## 12. L'IDENTITA' DI RIGA e' ambigua: 26.880 tappe senior (15,4%) condividono (giocatore, club) e alla grana anno sono indistinguibili

**categoria** `finto-pieno` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/careers.py`, `scripts/export_wikipedia_careers.py`, `docs/DATI.md`, `tests/test_careers.py`

### Evidenza

Il finto pieno vero non e' lo zero: e' che load_database non offre nessuna chiave che separi due permanenze allo stesso club. Cristante ha «Atalanta 2017-2018, 48 presenze, prestito» e «Atalanta 2018-2019, 0 presenze, definitivo»: chi chiede «presenze di Cristante all'Atalanta nel 2018» — l'unico join che la tabella unificata consente, perche' data_da/data_a sono NaN su tutte le 209.809 righe Wikipedia — riceve due righe che si contraddicono e nessun campo per scegliere. 26.880 tappe senior su 174.098 stanno in questa condizione; 1.333 di esse portano presenze == 0. Comando: python -c "import pandas as pd; t=pd.read_csv('data/carriere_wikipedia/tappe.csv.gz',low_memory=False); s=t[~t.giovanili]; k=s.groupby(['player_id','club']).size(); m=s.set_index(['player_id','club']).index.map(k)>1; print('tappe ambigue:',int(m.sum()),f'= {100*m.mean():.1f}%','| con presenze==0:',int(((m)&(s.presenze.values==0)).sum()))"

### Riparazione proposta

Non e' riparabile ricostruendo le date (non ci sono nella fonte). Si ripara DICHIARANDO: (a) documentare in careers.load_database che la chiave naturale delle righe Wikipedia e' (player_id, ordine) e NON (player_id, club_id, anno) — `ordine` esiste gia' ed e' l'unica chiave sicura; (b) esporre una colonna `tappa_ambigua` booleana calcolata all'export, cosi' chi aggrega sa dove non puo'; (c) aggiungere l'avvertenza accanto a quella sulle presenze, con lo stesso rilievo. Consiglio di priorita': questo e' il difetto piu' pericoloso del blocco (c), perche' l'errore che produce e' silenzioso e ha la forma di un dato.

### Guadagno atteso

Chiude l'unico modo in cui una query ragionevole su questa tabella restituisce un numero sbagliato senza accorgersene.

---

## 13. 5 club_id assegnati «univoco» sono il club SBAGLIATO — stessa classe di Brest e PAOK, mai ricontrollata dopo il primo audit

**categoria** `alias-mancante` · **rischio** `basso` · **riparabile ora** `True`

**File**: `src/data/club_matching.py`, `scripts/_run_verifica_aggancio_club.py`, `tests/test_careers.py`

### Evidenza

Test con informazione indipendente (dove va davvero il giocatore secondo lo strato 1, negli stessi anni): su 53.955 tappe verificabili l'aggancio conferma nel 71,3% dei casi, e 5 nomi hanno un'alternativa DOMINANTE, cioe' la firma di Brest/PAOK. «Beerschot» -> 566 «Beerschot AC» (club sciolto nel 2013) mentre 62 tappe su 76 puntano a 41274 «Beerschot VA»; «Dnipro» -> 60551 «SC Dnipro-1» contro 339 «Dnipro Dnipropetrovsk» (10/11); «Dynamo-2 Kyiv» -> 338 «Dynamo Kyiv», cioe' la PRIMA SQUADRA invece delle riserve (6/10) — proprio il caso che tests/test_careers.py::test_club_riserve_non_si_agganciano_alla_prima_squadra presidia per Bilbao e Real Madrid B; «Sumy» -> 80916 «FK Sumy» contro 21216 «PFK Sumy» (5/6); «Roda» -> 27448 «CD Roda» (spagnolo) contro 192 «Roda JC Kerkrade» (olandese) (4/6). Meccanismo: normalizza('Beerschot AC') scarta 'ac' come stopword e produce {beerschot}, che combacia ESATTAMENTE con 'Beerschot', mentre 'Beerschot VA' resta {beerschot, va} e non e' un match esatto -> candidato unico -> «univoco». 493 tappe totali sui 5 nomi. ⚠️ Gli altri 102 nomi con zero conferme NON sono errori: sono campionati che lo strato 1 non copre (AEL Limassol, Ujpest, Pogon Szczecin) — verificato che non hanno un'alternativa dominante, alt_n <= 6 su n >= 20.

### Riparazione proposta

Aggiungere le 5 voci a club_matching.ALIAS con la stessa forma delle correzioni gia' presenti (nome Wikipedia -> nome nostro, con il conteggio delle conferme nel commento), e per «Dynamo-2 Kyiv» aggiungerlo invece a NON_AGGANCIARE come le altre riserve. Poi — ed e' la parte che manca davvero — versionare il test come script _run_*: oggi la verifica dell'aggancio esiste solo come misura una-tantum dentro un audit, quindi la classe si ripresenta a ogni nuovo club raccolto e nessuno se ne accorge. Il criterio e' oggettivo e riproducibile: nome con >= 5 tappe verificabili, zero conferme, e un club_id alternativo su >= 50% delle tappe.

### Guadagno atteso

493 tappe riassegnate al club giusto; e soprattutto la classe passa da 'trovata due volte per caso durante un audit' a 'presidiata da un comando'. Beerschot da solo attribuisce 62 permanenze a un club che nel 2013 non esisteva piu'.

---

## 14. L'avvertenza «non sommare le presenze fra le due fonti» non e' presidiata da una riga di codice: la somma ingenua gonfia 22.637 giocatori su 22.665

**categoria** `bug-codice` · **rischio** `medio` · **riparabile ora** `True`

**File**: `src/data/careers.py`, `tests/test_careers.py`, `docs/DATI.md`

### Evidenza

L'avvertenza compare tre volte in docstring (careers.py righe 17-19, 315-317, README della cartella punto 2) e zero volte in codice o test. Misurato: TUTTI i 22.665 giocatori con righe Wikipedia hanno anche righe strato 1 (100%); 43.961 tappe senior Wikipedia (25,3%) si sovrappongono a una riga strato 1 sulla stessa terna (giocatore, club, anno), per 1.848.327 presenze Wikipedia contro 1.410.252 presenze strato 1 sulle stesse coppie; `db.groupby('player_id')['appearances'].sum()` supera il totale della sola fonte primaria per 22.637 giocatori, con gonfiaggio mediano +225 presenze e rapporto mediano 6,4x. Nota aggravante: career_before — l'unica API dichiarata sicura — ignora del tutto lo strato 2, quindi non esiste NESSUN modo corretto di usare le presenze Wikipedia, solo modi sbagliati non segnalati.

### Riparazione proposta

Tre livelli, dal piu' economico. (1) Test: `test_le_due_fonti_non_si_sommano` che verifica su un campione noto che sommare dia un numero diverso dal vero, e fallisca se un giorno qualcuno 'armonizza' le due colonne. (2) Codice: rinominare la colonna dello strato 2 da `appearances` a `appearances_lega_nazionale` in load_database — la difesa piu' forte, perche' un groupby().sum() su nomi diversi non si scrive per sbaglio; costo, un rename da propagare. (3) API: una funzione `presenze_per_fonte(player_id)` che restituisce le due cifre affiancate e mai sommate, cosi' il modo giusto esiste. La (2) e' quella che consiglio: l'avvertenza in docstring ha gia' avuto tre occasioni per funzionare e non e' un meccanismo.

### Guadagno atteso

Chiude un errore che oggi e' a un groupby di distanza e produce numeri gonfiati di 6,4 volte con l'aria di essere giusti. E' l'unico difetto di questo elenco che puo' entrare direttamente in una feature di modello.

---

## 15. load_wikipedia_careers(solo_ok=False) e' un parametro morto: restituisce lo stesso identico DataFrame

**categoria** `bug-codice` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `src/data/careers.py`, `tests/test_careers.py`

### Evidenza

careers.py righe 250-257: se il deliverable versionato esiste, la funzione ritorna il CSV e non guarda mai `solo_ok`. Misurato: a = load_wikipedia_careers(solo_ok=True); b = load_wikipedia_careers(solo_ok=False); a.equals(b) -> True, entrambi (209809, 17). Chi chiama con solo_ok=False crede di ottenere anche gli esiti non-ok e riceve in silenzio l'insieme filtrato. Gia' segnalato come 'non verificato' in docs/AUDIT_FASI/AUDIT_DATABASE_CARRIERE.md riga 195, mai chiuso.

### Riparazione proposta

O si toglie il parametro dalla firma (il deliverable versionato non contiene le tappe non-ok per costruzione, quindi la promessa non e' mantenibile), o si alza un ValueError quando solo_ok=False e si sta leggendo il CSV versionato. Non lasciarlo com'e': un parametro che non fa nulla e' peggio di un parametro assente, perche' documenta una capacita' che non c'e'.

### Guadagno atteso

Nessuno sui dati. Toglie una promessa falsa dall'API.

---

## 16. Il deliverable non e' ri-derivabile da un clone: esiti.jsonl non e' versionato, e serve per ogni riparazione

**categoria** `assenza-a-monte` · **rischio** `medio` · **riparabile ora** `False`

**File**: `data/carriere_wikipedia/README.md`, `.gitignore`, `docs/DATI.md`

### Evidenza

.gitignore riga 40 esclude data/carriere_wikipedia/esiti.jsonl; la cartella in un clone contiene solo README.md, tappe.csv.gz, esiti_riepilogo.csv, verdetti_wikidata.csv.gz, wikidata_qid.csv.gz. Anche le due cache (data/wikipedia_cache/, data/wikidata_cache/) sono escluse e in questo container non esistono. Conseguenza operativa diretta: scripts/export_wikipedia_careers.py si ferma alla prima riga di main() («esiti.jsonl non esiste: eseguire prima fetch_wikipedia_careers.py»), quindi i 41 giocatori recuperabili dei difetti 4-6 NON sono recuperabili senza ri-scaricare 29.816 pagine. Il README della cartella, per di piu', descrive esiti.jsonl come l'UNICO file presente («Cosa c'e'», riga 16) e non menziona i quattro che ci sono davvero.

### Riparazione proposta

Serve una decisione dell'utente, non una scelta tecnica: (a) versionare esiti.jsonl compresso (le sole tappe delle pagine non-ok, che sono l'unica cosa che manca al deliverable: ~7.000 giocatori) — costo di spazio da misurare; oppure (b) accettare che le riparazioni richiedano una ri-raccolta, e allora scriverlo esplicitamente. La regola 5-ter del CLAUDE.md («si conserva l'ORIGINALE come consegnato, perche' e' l'unico modo per accorgersi di un bug nella conversione») punta verso (a): tappe.csv.gz e' una nostra conversione di esiti.jsonl, e senza l'originale un errore dell'export e' indistinguibile dal dato. In ogni caso, correggere subito la tabella «Cosa c'e'» del README, che oggi descrive un file assente e tace su quattro presenti.

### Guadagno atteso

Sblocca le riparazioni dei difetti 4, 5 e 6 (41 giocatori). Senza, restano diagnosi e basta.

---

## 17. I «limiti misurati» del README sono quelli del lotto pilota di 60 e sovrastimano il deliverable di 2,3 volte

**categoria** `documentazione` · **rischio** `nullo` · **riparabile ora** `True`

**File**: `data/carriere_wikipedia/README.md`, `docs/DATI.md`, `src/data/careers.py`

### Evidenza

README di data/carriere_wikipedia, sezione «Limiti misurati (primo lotto di 60)»: pagine risolte 95% -> oggi 22.653/29.816 = 76,0%; tappe senior con presenze 99,8% -> 97,5%; guadagno pre-2012 su 84% dei giocatori -> 8.119/22.665 = 35,8%. La sezione dichiara onestamente il proprio perimetro («primo lotto di 60»), ma e' l'unica documentazione della cartella e chi la legge la prende per una proprieta' del file. In piu' docs/DATI.md riga 1042 dice «~202.000 tappe su ~21.600 giocatori» contro 209.809 su 22.665, e careers.py righe 13-15 dice 29.531 giocatori / 197.812 tappe contro 29.532 / 197.813 (la differenza e' la riga di data/presenze_integrate.csv che passa la deduplica — corretta, ma non riflessa nella docstring). Comando: lo script che ricalcola tutti questi numeri e' tre righe di pandas su tappe.csv.gz e esiti_riepilogo.csv.

### Riparazione proposta

Sostituire la sezione con i numeri sul deliverable INTERO, tenendo il lotto pilota come nota storica («al primo lotto di 60 il tasso era 95%: la caduta al 76% e' la coda dei mononimi e delle voci assenti, non un peggioramento del parser» — affermazione da verificare, non da assumere). Allineare DATI.md e le docstring di careers.py. E aggiungere accanto a ogni numero il comando che lo ricalcola, che e' la regola gia' scritta al punto 4 del §2-bis e qui non applicata.

### Guadagno atteso

Nessuno sui dati. Ma il 95% contro il 76% e' la differenza fra 'lo strato 2 e' quasi completo' e 'un giocatore su quattro non ce l'ha', e su quella cifra si decide se vale la pena costruirci sopra una feature.

---
