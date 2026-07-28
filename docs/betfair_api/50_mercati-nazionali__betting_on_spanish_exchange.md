# Betting on Spanish Exchange

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687649>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687649`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

12flatpipe

## How to Access the Spanish Exchange API

Customers who have registered an Spanish Exchange account can access the Betfair Exchange API.  Customers  can register an account via <https://www.betfair.es/prospect/exchange>

To use the Spanish Exchange with the API you need to create an Application Key for your Spanish Exchange account by following the process outlined via Application Keys

Once you have  created an App Key, you will need to login the API using the Spanish Exchange endpoint which is as follows:

## Non-interactive Login

For fully automated applications

|  |
| --- |
| `https://`[identitysso-cert.betfair.es](http://identitysso-cert.betfair.es)[/api/certlogin](http://identitysso.betfair.it/api/certlogin) |

## Interactive Login - Desktop Application

|  |
| --- |
| `https://`[identitysso.betfair.es/view/login?product=](http://identitysso.betfair.it/view/login?product=)`<AppKey>&url=`[https://www.betfair.e](https://www.betfair.it/)`s` |

## Interactive Login - API Endpoint

|  |
| --- |
| `https://`[identitysso.betfair.es/api/login](http://identitysso.betfair.it/api/login) |

Once a session token has been obtained via the .es login methods above, any further API requests should be sent to the UK Exchange endpoints indicated below.

 Requests to these endpoints will automatically return the markets that are available to Spanish Exchange customers

## Betting API Endpoints

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<method> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/betting/json-rpc/v1> | <method> | SportsAPING/v1.0/listMarketBook |
| JSON REST | <https://api.betfair.com/exchange/betting/rest/v1.0>/ |  |  |

## Accounts API Endpoints

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<method> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/account/json-rpc/v1> | <method> | AccountAPING/v1.0/getAccountFunds |
| JSON REST | <https://api.betfair.com/exchange/account/rest/v1.0> |  |  |

## Exchange Stream API

The Exchange Stream is available to Betfair Spain customers. Please see documentation via Exchange Stream API and Stream API endpoint details below:

### TCP / SSL Connection

Connection is established with an SSL socket to the following address:

##### **External (SSL):**

stream-api.betfair.com:443
