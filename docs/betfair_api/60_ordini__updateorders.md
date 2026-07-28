# updateOrders

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687485>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687485`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## OperationupdateOrders

#FFFFFF#C8D0E4updateOrders

**UpdateExecutionReport** [**updateOrders#updateOrders**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687485#updateOrders-updateOrders) **(** **StringmarketId** ,  **List<** **UpdateInstruction** **>instructions**  ,StringcustomerRef **)**  **throws** **APINGException**

Update non-exposure changing fields

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| marketId | String |  | The market id these orders are to be placed on |
| instructions | List< UpdateInstruction > |  | The number of update instructions.  The limit of update instructions per request is 60 |
| customerRef | String |  | Optional parameter allowing the client to pass a unique string (up to 32 chars) that is used to de-dupe mistaken re-submissions. |

| **Return type** | **Description** |
| --- | --- |
| UpdateExecutionReport |  |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
