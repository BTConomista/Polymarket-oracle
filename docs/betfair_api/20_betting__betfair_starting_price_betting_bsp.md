# Betfair Starting Price Betting (BSP)

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699885>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699885`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

The Betfair Starting Price will be determined by balancing bets from customers who want to back and lay at Starting Price and matching into the Betfair exchange markets to balance out any residual demand.

The Betfair Starting Price will be calculated exactly to ensure the fairest and most transparent odds possible for both backers and layers. The BSP does not need to account for a profit margin but instead is calculated at the start of an event by looking at the relationship between the amounts of money requested at SP by opposing betting parties. To give an even more accurate price, we will use money where possible that is trading on the exchange at the start of the event. This gives a true reflection of public opinion on a selection.

**How is the BSP calculated?**

The Near Price is based on money currently on the site at SP as well as unmatched money on the same selection in the exchange. To understand this properly, you first need to understand the calculation of the Far Price, which only takes into account the SP bets that have been made. The Far Price is not as complicated but not as accurate and only accounts for money on the site at SP.

Excluding money requested at a fixed price on the exchange, if there are £1000 worth of backers stakes on a selection at SP and £6000 worth of layers liability, we can return an SP at the start of the event of 6/1 (7.0).

If however there were £6000 worth of backers stakes on the selection and £1000 worth of layers liability, we would return an SP of 1/6 (1.17). These are calculations of the Far Price.

The calculation of the final starting price occurs when the market is turned in-play. This is when the market is reconciled.

Further information and detailed working demonstrating how the Betfair SP price is calculated can be found via <https://promo.betfair.com/betfairsp/FAQs_theBasics.html>
