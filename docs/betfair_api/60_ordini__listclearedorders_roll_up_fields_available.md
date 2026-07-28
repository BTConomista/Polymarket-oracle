# listClearedOrders - Roll-up Fields Available

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687679>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687679`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

The below table indicates fields will be available at each roll-up when making requests to **listClearedOrders** using the **groupBy** parameter.

**listClearedOrders** will 'hoist'  data into higher rollup levels whenever the value is unambiguous, this can occur when,

* SIDE, RUNNER & MARKET level when only 1 bet is involved in the rollup - only 1 possible value for each field so they are all unambiguous (in particular, betId)
* RUNNER level when all bets are on the same side - value of side is unambiguous, priceRequested and priceMatched can be averaged, sizeSettled can be totalled.
* MARKET level when all bets are on the same selection/side combo - value of selectionId, handicap and side are unambiguous, priceRequested and priceMatched can be averaged, sizeSettled can be totalled.
* PersistenceType and OrderType are only displayed above BET level if all bets in the rollup have the same type
* Only BET returns LAPSED or CANCELLED bets.

\*=fields that may be hoisted (if lower level fields are unambiguous or the rollup contains only 1 bet)

| **Rollup level:** | **BET** | **SIDE** | **MARKET** | **EVENT** | **EVENT\_TYPE** | **EXCHANGE** |
| --- | --- | --- | --- | --- | --- | --- |
| Settled As | Y | Y | Y | Y | Y | Y |
| Settled Date | Y | MAX | MAX | MAX | MAX | MAX |
| Bet Count | Y | Y | Y | Y | Y | Y |
| Profit | Y | SUM | SUM | SUM | SUM | SUM |
| Exchange Id | Y | Y | Y | Y | Y | Y |
| Event Type Id | Y | Y | Y | Y | Y | N |
| Event Id | Y | Y | Y | Y | N | N |
| Market Id | Y | Y | Y | N | N | N |
| Selection Id | Y | Y | N\* | N | N | N |
| Handicap | Y | Y | N\* | N | N | N |
| Side | Y | Y | N\* | N | N | N |
| Price Requested | Y | AVG | N\*(AVG) | N | N | N |
| Price Matched | Y | AVG | N\*(AVG) | N | N | N |
| Size Settled | Y | SUM | N\*(SUM) | N | N | N |
| Price Reduced | Y | Y | Y | N | N | N |
| Commission | N | N | Y | SUM | SUM | SUM |
| Bet Id | Y | N\* | N\* | N | N | N |
| Placed Date | Y | MAX | MAX | N | N | N |
| Persistence Type | Y | Y | Y | N | N | N |
| Order Type | Y | Y | Y | N | N | N |
| Regulator Code | Y | Y | Y | N | N | N |
| Regulator Auth Code | Y | Y | Y | N | N | N |
| Voided Date(where applicable) | Y | MAX | MAX | N | N | N |
| BetOutcome | Y | N | N | N | N | N |
