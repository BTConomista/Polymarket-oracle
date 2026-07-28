# `data/ricerca_esterna/` — dati trovati FUORI dalle fonti di produzione

**86 file.** Tutto ciò che sta qui è stato cercato e scaricato durante l'audit
delle 5 leghe (Fase 100) da fonti che **non** sono quelle della pipeline
(football-data, Understat, player-scores, openfootball). Serve una cartella a
parte per una ragione precisa, che è anche la regola di questa cartella:

> ⚠️ **Niente di ciò che sta qui è dentro gli snapshot.** Sono dati **reali**,
> non stime — ma provengono da fonti secondarie e restano fuori da
> `data/*_matches.csv` finché una decisione esplicita non li fa entrare. L'unica
> eccezione mai concessa sono **6 celle 1X2** (regola R2, dichiarate in
> `docs/DATI.md` §4 e registrate in `data/correzioni_dichiarate.csv`), e vengono
> da un dataset che non è nemmeno depositato qui.

Il catalogo generale dei dati è **[`docs/DATI.md`](../../docs/DATI.md)** §4 —
questo file descrive solo il contenuto della cartella.

---

## 1 · Le quote 1xBet via `footiqo.com` (26 file)

La scoperta della Fase 100: un book che football-data **non contiene**, con le
quote di **chiusura** delle stagioni in cui a noi manca la chiusura O/U.

| file | quanti | cosa |
|---|--:|---|
| `footiqo_{lega}_{stagione}.json` | **15** | 1X2 + O/U 2.5 di chiusura, 5 leghe × 3 stagioni (2017-18, 2018-19, 2019-20) |
| `footiqo_gol_{lega}_{stagione}.json` | **10** | GG/NG di chiusura, 5 leghe × 2 stagioni (2017-18, 2018-19) |
| `footiqo_manifest.json` | 1 | provenienza: endpoint, `table_id`, righe e **SHA256** per ciascuno dei file scaricati |

Prodotti da `_fetch_footiqo.py` e `_fetch_footiqo_gol.py` (endpoint permesso dal
`robots.txt` del sito).

### Perché NON sono negli snapshot

Non per un dubbio sulla loro autenticità — quella è stata dimostrata — ma per una
**incompatibilità di regime**, ed è la parte che va letta prima di riproporre la
cosa:

- gli snapshot dal 2019-20 contengono la **media multi-book** (`AvgC*`);
- 1xBet è **un solo book**;
- come proxy di quella media è **peggiore della stima che già abbiamo**:
  `scarto_book_2019_20.json` misura `MAE_1xBetClose_vs_AvgClose = 0.0156` sulle
  **1.687** partite 2019-20 dove esistono entrambi, contro il **~0.012**
  dichiarato dalla stima `ou_close_2017_19.csv`;
- inserirlo creerebbe una **rottura di regime a metà colonna**.

*(Per riferimento, dallo stesso file: non avere affatto la chiusura costa
`MAE_Apertura_vs_AvgClose = 0.0206`; overround 1.0349 per 1xBet contro 1.0537
per la media football-data.)*

**Trovare il dato vero non significa automaticamente che sia il dato giusto da
usare.** Il ragionamento completo è in
[`docs/CACCIA_OU_2017_19.md`](../../docs/CACCIA_OU_2017_19.md).

### Le validazioni (4 file) — è davvero una chiusura?

La domanda non è retorica: una fonte terza potrebbe ri-etichettare un'apertura,
o ricostruire i prezzi da un modello. Testata, non assunta:

| file | cosa contiene |
|---|---|
| `validazione_footiqo.json` | criteri, confutazioni tentate, dettaglio per lega-stagione (copertura 100% su tutte e 10 le coppie) |
| `confutazione_footiqo.json` | il test del **movimento**: correlazione con la chiusura vera Pinnacle **0.9976** contro **0.9897** con l'apertura, e correlazione del *movimento* apertura→chiusura **0.881**, su 3.645 righe |
| `confutazione_footiqo_G.json` | la **scala di riferimento**: due book veri allo stesso istante correlano 0.9982-0.9987, mentre apertura-contro-chiusura sta a 0.9898 — 1xBet-contro-Pinnacle-chiusura è a 0.9976, cioè dalla parte dei «due book veri». Zero righe identiche a Pinnacle (`identita_riga_per_riga = 0.0`) |
| `ricalibrazione_book_2019_20.json` | quanto si recupererebbe ricalibrando il book verso la media: MAE 0.0156 → 0.0122, ma **in-sample** (dichiarato ottimistico) — non abbastanza per cambiare la decisione |

---

## 2 · I calendari di coppa da Wikipedia (50 file, 3.045 righe)

`fixtures_{lega}_{competizione}.csv`, colonne
`season, team, date, competition, home_away, opponent, metodo_nome, pagina`.

| lega | file | righe |
|---|--:|--:|
| Serie A | 9 | 499 |
| Premier League | 10 | 526 |
| La Liga | 10 | 677 |
| Bundesliga | 9 | 326 |
| Ligue 1 | 12 | 1.017 |

**A cosa servirebbero, e perché non sono applicati.** Il calendario di club di
produzione viene da openfootball, che non copre tutte le coppe: ne risultano
**1.603 celle `midweek_europe` a zero** che dovrebbero essere 1, e ~1.700 valori
di riposo sbagliati di conseguenza (§1-bis di `docs/DATI.md` — è il caso da
manuale della regola **R6**: il buco peggiore non è il `NaN`, è il finto pieno).

Queste righe sono la materia prima per chiudere quel buco **senza stimare
niente**. Non sono state applicate perché **Wikipedia non è una fonte primaria**:
la decisione di promuoverla, o di cercare altrove, non è stata presa. Finché non
lo è, il difetto resta **dichiarato** e i dati restano qui.

---

## 3 · `manifest_fonti_audit.json` — le impronte delle fonti di produzione

**90 impronte SHA256** (45 CSV football-data + 45 JSON Understat, una per
lega-stagione), scritte da `scripts/fetch_sources.py`. È l'unico modo per
verificare che gli snapshot di **Bundesliga e Ligue 1** derivino da grezzi
identici a quelli scaricati: quelle due leghe sono le sole senza fonte grezza
congelata in repo (`data/fonti/` è in `.gitignore`, 135 MB).

⚠️ **Trappola nota**: le chiavi sono nella forma `cantiere/data/fonti/…`. Per
confrontarle con quelle che `fetch_sources.py` scrive oggi va tolto il prefisso
`cantiere/`.

---

## 4 · Gli script (4 file)

Vivono qui, accanto ai dati che producono, e non in `scripts/`: sono strumenti di
**ricerca una tantum**, non pipeline.

| script | cosa fa |
|---|---|
| `_fetch_footiqo.py` | scarica 1X2 + O/U di chiusura e scrive il manifest |
| `_fetch_footiqo_gol.py` | idem per il GG/NG |
| `_valida_footiqo.py` | i criteri di autenticità (copertura, margine, ultima cifra, movimento) |
| `_confuta_footiqo.py` | i tentativi di **confutare** l'ipotesi «è una chiusura» — l'ordine giusto: prima si prova a demolirla, poi la si accetta |
