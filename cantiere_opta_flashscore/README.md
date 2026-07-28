# Cantiere — sessione Opta / WhoScored / diretta.it-Flashscore / SofaScore

Questa cartella è un **contenitore temporaneo**, non la destinazione finale.
Contiene il lavoro di una sessione (28/07/2026) che ha valutato quattro fonti
dati esterne per colmare due piste già note del progetto — le **formazioni
ufficiali** pre-partita e i **corner/cartellini** mancanti per Bundesliga e
Ligue 1 — e le ha chiuse tutte negativamente.

**Un lavoro successivo deve smontare questa cartella**, cioè integrare le tre
parti nei documenti ufficiali del progetto e poi cancellare la cartella:

1. `diario_da_integrare.md` → va incollato in `docs/DIARIO.md` come nuova
   fase, **rinumerata all'ultima fase realmente libera** al momento
   dell'integrazione (non "Fase 126": quel numero era corretto solo rispetto
   allo stato del repo del 28/07/2026 sera, prima serie A/B di sessioni
   parallele — verificare con `grep -n "^## Fase " docs/DIARIO.md | tail -5`
   prima di assegnare il numero), con la relativa voce aggiunta all'indice in
   testa al file.
2. `piste_pista20_da_integrare.md` → va incollato in `docs/PISTE.md` §3 come
   nuova pista, **rinumerata analogamente** (verificare l'ultima pista
   effettivamente libera in `docs/PISTE.md`, tabella di stato §0-bis inclusa,
   e aggiornare il conteggio delle piste chiuse nello stesso paragrafo).
3. `manuale_sopravvivenza_righe_da_integrare.md` → le 4 righe vanno aggiunte
   alla tabella "Fonti esterne valutate in sessione" in
   `docs/MANUALE_SOPRAVVIVENZA.md` §4 (i riferimenti a "pista 20" nel testo
   vanno aggiornati al numero pista reale assegnato al punto 2).

**Perché non è già stato fatto in questa sessione**: per evitare un altro
conflitto di merge sugli stessi file condivisi (`DIARIO.md`/`PISTE.md`) che
un'altra sessione stava modificando in parallelo nello stesso momento (Fasi
123-125, già su `main`). Consolidare qui evita di dover rinegoziare numerazioni
e conflitti adesso; l'integrazione vera si fa quando non c'è una sessione
parallela attiva sugli stessi file.

Nessun codice è coinvolto — solo tre frammenti di documentazione. Non c'è
rischio del tipo già visto in passato con la cartella `cantiere/` (script con
percorsi assoluti che puntavano lì): qui non ci sono script, solo testo da
copiare e incollare nei punti giusti.
