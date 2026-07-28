# listCurrencyRates

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687935>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687935`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

#FFFFFF#C8D0E4listCurrencyRates

**List<CurrencyRate>** **listCurrencyRates** **(** String fromCurrency **)** **throws AccountAPINGException**

Returns a list of currency rates based on given currency. **Please note:** the currency rates are updated once every hour a few seconds after the hour.

| Parameter name | Type | Required | Description |
| --- | --- | --- | --- |
| fromCurrency | String |  | The currency from which the rates are computed. **Please note:** GBP is currently the only based currency support |

| Return type | Description |
| --- | --- |
| List<CurrencyRate> | List of currency rates |

| Throws | Description |
| --- | --- |
| AccountAPINGException | Generic exception that is thrown if this operation fails for any reason. |
