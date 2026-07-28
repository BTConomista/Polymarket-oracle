# listMarketTypes

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687525>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687525`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

listMarketTypes

#FFFFFF#C8D0E4listMarketTypes
**List<

MarketTypeResult
>**

**(**
**MarketFilter
filter**
,Stringlocale
**)**
**throws

APINGException**

Returns a list of market types (i.e. MATCH\_ODDS, NEXT\_GOAL) associated with the markets selected by the MarketFilter. The market types are always the same, regardless of locale.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| filter | MarketFilter |  | The filter to select desired markets. All markets that match the criteria in the filter are selected. |
| locale | String |  | The language used for the response. If not specified, the default is returned. |

| Return type | Description |
| --- | --- |
| List<  MarketTypeResult > | output data |

| Throws | Description |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
