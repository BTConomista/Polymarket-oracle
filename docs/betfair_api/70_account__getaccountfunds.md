# getAccountFunds

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687888>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687888`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## OperationgetAccountFunds

#FFFFFF#C8D0E4getAccountFunds

**AccountFundsResponse** **getAccountFunds** **(** **)**  **throws** **AccountAPINGException**

Returns the available to bet amount, exposure and commission information.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| wallet | Wallet |  | Name of the wallet in question. Global wallet is returned by default |

| **Return type** | **Description** |
| --- | --- |
| AccountFundsResponse | Response for retrieving available to bet. |

| **Throws** | **Description** |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
