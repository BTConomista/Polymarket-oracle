# createDeveloperAppKeys

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687897>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687897`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## OperationcreateDeveloperAppKeys

#FFFFFF#C8D0E4createDeveloperAppKeys

**DeveloperApp** [**createDeveloperAppKeys#createDeveloperAppKeys**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687897#createDeveloperAppKeys-createDeveloperAppKeys) **(** **String appName** **)**  **throws** **AccountAPINGException**

Create 2 Application Keys for a given user; one 'Delayed and the other 'Live'. You must apply to have your 'Live' App Key activated.  **Please Note:** The**appName must be unique** and cannot contain your username. A UNEXPECTED\_ERROR will be returned in these circumstances.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| appName | String |  | A Display name for the application. |

| **Return type** | **Description** |
| --- | --- |
| DeveloperApp | A map of application keys, one marked ACTIVE, and the other DELAYED |

| **Throws** | **Description** |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**
