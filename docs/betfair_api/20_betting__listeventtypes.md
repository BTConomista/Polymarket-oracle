# listEventTypes

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687448>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687448`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation listEventTypes

#FFFFFF#C8D0E4listEventTypes

**List<****EventTypeResult****>**
[**listEventTypes#listEventTypes**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687448#listEventTypes-listEventTypes)
**(**
**MarketFilter****filter**
,Stringlocale
**)**
**throws****APINGException**

Returns a list of Event Types (i.e. Sports) associated with the markets selected by the MarketFilter.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| filter | MarketFilter |  | The filter to select desired markets. All markets that match the criteria in the filter are selected. |
| locale | String |  | The language used for the response. If not specified, the default is returned. |

| **Return type** | **Description** |
| --- | --- |
| List< EventTypeResult > | output data |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
