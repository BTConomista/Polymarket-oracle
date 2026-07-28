# getAffiliateRelation

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687655>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687655`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

#FFFFFF#C8D0E4getAffiliateRelation

**List<AffiliateRelation>** **getAffiliateRelation** **(** **List<String> vendorClientIds** **)** **throws AccountAPINGException**

Return relation between a list of users and an affiliate

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| vendorClientIds | List<String> |  | List of client ids to check affiliation on |

| Return type | Description |
| --- | --- |
| List<AffiliateRelation> | List of affiliate relation status per user |

| Throws | Description |
| --- | --- |
| AccountAPINGException |  |

**Since 1.0.0**
