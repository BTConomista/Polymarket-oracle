# replaceOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687487>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687487`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## OperationreplaceOrders

#FFFFFF#C8D0E4replaceOrders

**ReplaceExecutionReport** [**replaceOrders#replaceOrders**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687487#replaceOrders-replaceOrders) **(** **StringmarketId** ,  **List<** **ReplaceInstruction** **>instructions**  ,StringcustomerRef, MarketVersion marketVersion,  boolean async **)**  **throws** **APINGException**

This operation is logically a bulk cancel followed by a bulk place. The cancel is completed first then the new orders are placed. The new orders will be placed atomically in that they will all be placed or none will be placed. In the case where the new orders cannot be placed the cancellations will not be rolled back. See ReplaceInstruction.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | The market id these orders are to be placed on |
| instructions | List< ReplaceInstruction > |  | The number of replace instructions.  The limit of replace instructions per request is 60. |
| customerRef | String |  | Optional parameter allowing the client to pass a unique string (up to 32 chars) that is used to de-dupe mistaken re-submissions. |
| marketVersion | MarketVersion |  | Optional parameter allowing the client to specify which version of the market the  orders should be placed on. If the current market version is higher than that sent on an order,  the bet will be lapsed. |
| async | boolean |  | An optional flag (not setting equates to false) which specifies if the orders should be replaced asynchronously.  Orders can be tracked via the Exchange Stream API or the API-NG by providing a customerOrderRef for each replace order.  Not available for MOC or LOC bets. |

| **Return type** | **Description** |
| --- | --- |
| ReplaceExecutionReport |  |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
