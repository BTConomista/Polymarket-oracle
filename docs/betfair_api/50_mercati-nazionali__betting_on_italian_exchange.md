# Betting On Italian Exchange

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687808>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687808`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

12flatpipe

## How to Access the Italian Exchange API

Italian residents who have registered an Italian Exchange account can access the Betfair Exchange API. Italian residents can register an account via [**https://register.betfair.it/account/registration**](https://register.betfair.it/account/registration)

To use the Italian Exchange API you need to **Create an Application Key** for your Italian Exchange account.

Once you have done created an App Key, you will need to login to the Exchange API using the appropriate Italian Exchange endpoint which are as follows:

Please see full technical details relating to the above API Login endpoints via Login & Session Management

## Non-interactive Login

For fully automated applications

https://identitysso-cert.betfair.it/api/certlogin

## API Login - Desktop Application

https://identitysso.betfair.it/api/login

## Interactive Login - Desktop Application

https://identitysso.betfair.it/view/login?product=<AppKey>&url=https://www.betfair.it

Once a session token has been obtained via the .it login methods above, any further API requests should be sent to the Exchange endpoints indicated below.

Requests to these endpoints will automatically return the markets that are available to Italian Exchange customers via the [Betfair.it](http://Betfair.it) domain.

## Betting API Endpoints

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<methodname> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/betting/json-rpc/v1> | <methodname> | SportsAPING/v1.0/listMarketBook |
| JSON REST | <https://api.betfair.com/exchange/betting/rest/v1.0>/ |  |  |

## Accounts API Endpoints

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<methodname> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/account/json-rpc/v1> | <methodname> | AccountAPING/v1.0/getAccountFunds |
| JSON REST | <https://api.betfair.com/exchange/account/rest/v1.0> |  |  |

## Exchange Stream API

The Exchange Stream is available to Betfair Italy customers. Please see documentation via Exchange Stream API and Stream API endpoint details below:

### TCP / SSL Connection

Connection is established with an SSL socket to the following address:

##### **External (SSL):**

stream-api.betfair.com:443

## [Italian Exchange Specific Bet Rules](https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Italian+Exchange+Specific+Bet+Rules)

There are several additional regulatory rules which apply specifically and only to accounts betting on the Italian Exchange (<https://www.betfair.it/exchange):>

1. The stake for each back offer is a minimum of 200 Euro Cents and can only be incremented in multiples of 50 Euro Cents.
2. Any lay offers placed by the customer, must be placed in such a way as to ensure that the stake for any corresponding back offer amounts to a minimum of 50 Euro Cents.
3. A placeOrders request may contain up to 50 bet instructions.  Any submissions containing more than 50 instructions will fail.
4. We cannot accept betting offers with potential winnings, calculated on the basis of the pre-selected odds that exceed the amount envisaged by article 12, paragraph 4, of Finance Minister Decree no. 111 of 1 March 2006 (10,000 Euros). **N.B. This amount includes the original stake.**
5. placeOrders request containing both back and lay bets in the same order will be rejected.
