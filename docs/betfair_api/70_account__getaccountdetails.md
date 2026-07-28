# getAccountDetails

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699900>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699900`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## OperationgetAccountDetails

#FFFFFF#C8D0E4getAccountDetails

**AccountDetailsResponse** [**getAccountDetails#getAccountDetails**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699900#getAccountDetails-getAccountDetails) **(** **)**  **throws** **AccountAPINGException**

Returns the details relating your account, including your discount rate and Betfair point balance.

| **Return type** | **Description** |
| --- | --- |
| AccountDetailsResponse | Response for retrieving account details. |

| **Throws** | **Description** |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**

**Please note:** The data returned by **getAccountDetails** relies on two underlying services. The **pointsBalance** is returned by a separate service from the other data.

As a consequence of this, in the event of a failure to a single underlying service, either the **pointsBalance** or the remaining data may not be included in the **getAccountDetails** response. If both services fail, the error UNEXPECTED\_ERROR will be returned.
