# getAccountStatement

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687876>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687876`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

#FFFFFF#C8D0E4getAccountStatement

[**AccountStatementReport**](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Accounts+TypeDefinitions#AccountsTypeDefinitions-AccountStatementReport) **getAccountStatement** **(** String locale, int fromRecord, int recordCount, TimeRange itemDateRange, includeItem, Wallet wallet**)** **throws****AccountAPINGException**

**Please note:** You can only retrieve account statement items for the last **90 days**

Please see the Additional Information for details of how getAccountStatement output is affected in the event of market resettlement.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| locale | String |  | The language to be used where applicable. If not specified, the customer account default is returned. |
| fromRecord | int |  | Specifies the first record that will be returned. Records start at index zero. If not specified then it will default to 0. |
| recordCount | int |  | Specifies the maximum number of records to be returned. Note that there is a page size limit of 100. |
| itemDateRange | TimeRange |  | Return items with an itemDate within this date range. Both from and to date times are inclusive. If from is not specified then the oldest available items will be in range. If to is not specified then the latest items will be in range. nb. This itemDataRange is currently only applied when includeItem is set to ALL or not specified, else items are NOT bound by itemDate.  **Please note:** You can only retrieve account statement items for the last 90 days. |
| includeItem | IncludeItem |  | Which items to include, if not specified then defaults to ALL. |
| wallet | Wallet |  | Which wallet to return statementItems for. If unspecified then the UK wallet will be selected |

| **Return type** | **Description** |
| --- | --- |
| AccountStatementReport | List of statement items chronologically ordered plus moreAvailable boolean to facilitate paging |

| **Throws** | **Description** |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |
