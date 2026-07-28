# Report 7 — Le righe corrotte: recupero, ritiro di un errore, stima

> **Che cos'è questo documento.** Il settimo degli **11 report integrali
> dell'audit a 5 leghe (Fase 100)** — verbale esteso di ciò che `docs/DIARIO.md`
> riassume nella voce «Cinque leghe». Indice: [`00_indice.md`](00_indice.md).
> Documento **storico**: la stima del §3 (MAE 0.0267) è stata **superata** dal
> secondo giro di lavoro ([`09_chiusura_buchi.md`](09_chiusura_buchi.md) §5).
>
> ⚠️ **Sigle delle regole.** Le «R6» citate qui sono nella numerazione **storica
> del cantiere**: nella numerazione **vigente** (`CLAUDE.md` §5-bis) quella
> regola è la **R5** («procedura per una riga che sembra corrotta», 5 passi). La
> tabella di corrispondenza è in testa a [`REGOLE.md`](REGOLE.md).

Domanda posta: *«come hai sistemato gli errori? cerca su internet… se non riesci
a risalire ai dati reali, riesci a fare delle stime?»*

Tre risposte, in ordine di importanza:

1. **una delle "correzioni" era sbagliata, l'ho ritirata** (§1);
2. il dato vero delle 8 quote **non è recuperabile**, e ora so esattamente
   perché, fonte per fonte (§2);
3. le ho **stimate** con un errore misurato: MAE 0.0267 contro 0.0743 di una
   baseline banale (§3).

La procedura completa per i casi futuri è la regola **R6** di
[`REGOLE.md`](REGOLE.md).

---

## 1 · L'errore che avevo fatto io: Bielefeld-Leverkusen

Avevo segnalato come «xG impossibile» la riga Bielefeld-Leverkusen del
21/11/2020: xG = 0.00 per una squadra che aveva **segnato un gol** e che
football-data dava con **1 tiro in porta**. Il ragionamento sembrava solido —
non si segna con zero occasioni — e avevo portato `home_xg` e `home_npxg` a NaN.

**Era sbagliato.** Sono andato a prendere il dato tiro-per-tiro della stessa
fonte (`understat.com/getMatchData/15207`) e dice questo:

- il Bielefeld ha **0 tiri**, nessuno;
- nella lista tiri del **Leverkusen** compare, al 46′, una voce con
  `result: "OwnGoal"` e xG 0.0.

Il gol del Bielefeld era un **autogol del portiere avversario Hrádecky**
(verificato anche su fonte indipendente: il 47′ della cronaca). Una squadra che
non tira e segna solo perché l'avversario si infila la palla in porta **ha
davvero xG = 0.00**. Il dato era giusto; era il mio controllo a essere cieco.

Anche il «tiro in porta» di football-data si spiega: quella fonte conta
l'autogol come tiro in porta della squadra che ne beneficia, Understat no. Due
convenzioni diverse sullo stesso evento, nessuna delle due sbagliata.

### Cosa ho fatto

- **ritirata la correzione** e ripristinato lo 0.00 originale. Nel registro non
  ho cancellato niente: le due righe sbagliate restano con `stato = ritirata` e
  il motivo per esteso, più due righe di ripristino. Il registro deve
  raccontare anche gli errori, altrimenti la prossima sessione li rifà;
- **corretto il controllo automatico**: ora, prima di dichiarare impossibile un
  xG nullo, `audit_anomalie.check_xg` scarica il dato tiro-per-tiro e verifica
  se i gol sono spiegati da autogol. Con la verifica attiva: **0 xG impossibili
  su tutte e 5 le leghe**, e la riga del Bielefeld risulta correttamente
  legittima (`autogol_ricevuti: 1`, `tiri_understat: 0`);
- scritta la lezione in **R6, passo 1**: l'impossibilità fisica va verificata
  sul dato più fine della *stessa* fonte, mai dedotta da una regola generale.

Le altre correzioni **restano valide**: le 8 linee O/U (diagnosticate con
un'informazione indipendente, §2) e Union Berlin-Bochum (verificata su più
fonti).

---

## 2 · Le 8 quote: ho cercato, non ci sono

Le righe: 6 Bundesliga e 2 Ligue 1, tutte 2017-19, tutte con la linea O/U di
apertura a overround impossibile (fino a 1.339 — il 34% di margine su un mercato
a due esiti).

### Perché non sono recuperabili

| fonte | esito | cosa ho verificato |
|---|---|---|
| football-data.co.uk | ❌ | è **la fonte corrotta stessa**: quelle celle vengono da lì. Non esiste una seconda colonna O/U in quelle stagioni |
| BetExplorer | ❌ | per il 2017-19 la funzione confronto-quote è stata **ritirata**: tab «1X2» disabilitato, nessun tab O/U (ri-verificato in questa sessione) |
| OddsPortal | ❌ **vietato** | il `robots.txt` contiene `Disallow: *-2017*`, `*-2018*`: esattamente le pagine storiche che servirebbero. Non si scrape |
| diretta.it / Flashscore | ❌ | `robots.txt` consente le pagine partita, ma i dati arrivano da feed interni — e le quote storiche vengono dallo stesso gruppo di BetExplorer, che le ha ritirate |
| Sofascore | ❌ | 403 anche sul `robots.txt`: bloccati a monte |
| ricerca web | ❌ | risultati e marcatori si trovano ovunque; le **quote storiche per singola partita** no |

È lo stesso muro della caccia alle quote O/U 2017-19 già documentata dal
progetto, e per la stessa ragione: quell'epoca ha una sola rilevazione O/U, e
chi la ripubblica eredita anche i suoi difetti.

### Un successo, però: FotMob è utilizzabile per altro

Per l'xG, FotMob risponde e ha i dati. Due trappole scoperte sul campo e messe
in R6: (a) il `robots.txt` vieta il loro `/api/*`, quindi si usano solo le
pagine; (b) l'URL senza il frammento `#matchId` **rende un'altra partita** della
stessa coppia — mi ha servito una DFB Pokal del 2025 al posto della partita del
2020. Va sempre verificato `matchTimeUTC` prima di leggere i numeri. E resta il
punto di merito: il loro xG è un **modello diverso** da Understat, quindi non va
mescolato dentro la stessa colonna.

---

## 3 · La stima: sì, e con un errore misurato

> ⚠️ **SUPERATA dal report 9 §5.** Un bakeoff di 26 varianti ha battuto questo
> metodo (chiamato lì **M1**): **M5g** scende a **MAE 0.0143** usando la chiusura
> 1xBet, **M4** (superficie di debias sul solo 1X2, senza contaminazione) a
> **0.0197**. Il fattore d'effetto onesto è **1,87×** (0.0267 → 0.0143), non
> «2,6×». Lo 0.0267 di questo paragrafo vale come **misura interna a questo
> report**, non come errore corrente della stima pubblicata.

Se il dato vero non c'è, si stima — con informazione **integra** e un errore
**misurato**, tenendo il risultato fuori dallo snapshot.

**L'idea.** Per quelle 8 partite l'**1X2 di apertura è intatto**: è un'altra
colonna, da un altro provider. 1X2 e O/U descrivono la stessa distribuzione di
gol, quindi invertendo il solo 1X2 nei tassi (λ, μ) e leggendo dalla matrice la
P(Over 2.5) si ottiene una stima che **non tocca mai la riga corrotta**. È lo
stesso ragionamento con cui, in fase di diagnosi, ho stabilito quale dei due
lati fosse rotto.

**L'errore, misurato dove la verità esiste** — le 3.643 partite 2017-19 delle
cinque leghe con linea O/U integra:

| metodo | MAE (probabilità) |
|---|--:|
| baseline: media della lega | 0.0743 |
| stima grezza dall'1X2 | 0.0345 (bias −0.0225) |
| **stima debiasata** (correzione leave-one-league-out) | **0.0267** |

La stima grezza sotto-stima sistematicamente la P(Over) di 2.25 punti — la
matrice con ρ = −0.06 tarata sull'1X2 è un po' troppo "difensiva". La correzione
è stabile fra le leghe (+0.021…+0.024) e fittata **escludendo la lega su cui si
applica**, quindi non è un aggiustamento in-sample. Risultato: **2.8 volte
meglio della baseline**, p90 dell'errore 0.056.

Onestà sul confronto: 0.0267 è circa **il doppio** dell'errore della stima di
chiusura O/U che il progetto già usa (0.012). Normale — quella parte da una
linea O/U vera e aggiunge il movimento; questa deve dedurre il totale dal solo
1X2. Va usata sapendo che è più grezza.

**Le 8 stime** (probabilità, mai quote), in
[`data/estimates/ou_open_corrotte_2017_19.csv`](../../data/estimates/ou_open_corrotte_2017_19.csv):

| lega | stagione | partita | P(Over 2.5) stimata |
|---|---|---|--:|
| bundesliga | 2017-18 | Leverkusen-Dortmund | 0.6135 |
| bundesliga | 2017-18 | Hoffenheim-RB Leipzig | 0.5560 |
| bundesliga | 2017-18 | Ein Frankfurt-Bayern Munich | 0.6354 |
| bundesliga | 2017-18 | Bayern Munich-Hertha | 0.7043 |
| bundesliga | 2017-18 | Werder Bremen-Leverkusen | 0.6802 |
| bundesliga | 2018-19 | Dortmund-Wolfsburg | 0.5849 |
| ligue_1 | 2017-18 | Lyon-Metz | 0.8159 |
| ligue_1 | 2017-18 | Monaco-Lyon | 0.5453 |

Restano **fuori dagli snapshot**: nelle colonne quota c'è NaN, la stima vive nel
suo file con metodo ed errore scritti riga per riga. Chi la userà lo dichiarerà.

> Stato oggi di quel file: `data/estimates/ou_open_corrotte_2017_19.csv` ha
> **12 righe** (verificato: 7 bundesliga + 3 la_liga + 2 ligue_1) e porta i
> valori del metodo v2 (M5g e M4). Le 3 righe La Liga sono entrate dopo, quando
> il guard sull'overround ha svuotato anche quelle celle; le 8 di questa tabella
> sono le stesse, ri-stimate. Il diagnostico storico (metodo M1, MAE 0.0267)
> vive in `docs/audit_5_leghe/numeri/stima_ou_corrotte_metodo_storico.csv`.

---

## 4 · Cosa cambia per il futuro

Tutto quanto sopra è diventato la regola **R6** di `REGOLE.md`, in cinque passi:
spiegare prima di accusare → diagnosticare con informazione indipendente →
cercare il dato vero nell'ordine giusto (con la tabella delle fonti verificate)
→ stimare con errore misurato se non c'è → registrare, errori compresi.
