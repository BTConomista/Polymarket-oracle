# getVendorClientId

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687115>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687115`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

**getVendorClientId**

**String** **getVendorClientId** **(** **)** **throws AccountAPINGException**

Returns the vendor client id for customer account which is a unique identifier for that customer.  The vendor client Id can be used to obtain the customers application subscription history via getApplicationSubscriptionHistory.  The request requires the X-Authentication header only

| Return type | Description |
| --- | --- |
| String | Vendor client id. |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
