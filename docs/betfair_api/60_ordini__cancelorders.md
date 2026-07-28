# cancelOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687491>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687491`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

cancelOrders

#FFFFFF#C8D0E4cancelOrders

**CancelExecutionReport** [**cancelOrders#cancelOrders**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687491#cancelOrders-cancelOrders) **(** StringmarketId,List< CancelInstruction >instructions,StringcustomerRef **)**  **throws** **APINGException**

Cancel all bets OR cancel all bets on a market OR fully or partially cancel particular orders on a market. Only LIMIT orders can be cancelled or partially cancelled once placed.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | If marketId **and** betId aren't supplied **all bets** are cancelled. **Please note:** Concurrent requests to cancel all bets will be rejected until the initial request to cancel all bets is complete. |
| instructions | List< CancelInstruction > |  | All instructions need to be on the same market. If not supplied all unmatched bets on the market (if market id is passed) are fully cancelled.  The limit of cancel instructions per request is 60 |
| customerRef | String |  | Optional parameter allowing the client to pass a unique string (up to 32 chars) that is used to de-dupe mistaken re-submissions. |

| **Return type** | **Description** |
| --- | --- |
| CancelExecutionReport |  |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
