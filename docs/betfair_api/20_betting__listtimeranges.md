# listTimeRanges

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687444>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687444`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation listTimeRanges

#FFFFFF#C8D0E4listTimeRanges

**List<****TimeRangeResult****>**
[**listTimeRanges#listTimeRanges**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687444#listTimeRanges-listTimeRanges)
**(**
**MarketFilter****filter**
,
**TimeGranularity****granularity**
**)**
**throws****APINGException**

Returns a list of time ranges in the granularity specified in the request (i.e. 3PM to 4PM, Aug 14th to Aug 15th) associated with the markets selected by the MarketFilter.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| filter | MarketFilter |  | The filter to select desired markets. All markets that match the criteria in the filter are selected. |
| granularity | TimeGranularity |  | The granularity of time periods that correspond to markets selected by the market filter. |

| **Return type** | **Description** |
| --- | --- |
| List< TimeRangeResult > | output data |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
