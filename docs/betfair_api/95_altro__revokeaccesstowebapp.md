# revokeAccessToWebApp

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687722>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687722`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

#FFFFFF#C8D0E4revokeAccessToWebApp

**Status**  **(** **long vendorId** **)** **throws AccountAPINGException**

Remove the link between an account and a vendor web app. This will remove the refreshToken for this user-vendor pair subscription.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorId | long |  | The id of the vendor to revoke access for |

| Return type | Description |
| --- | --- |
| Status | Returns whether the request was successful or not |

| Throws | Description |
| --- | --- |
| AccountAPINGException |  |

**Since 1.0.0**
