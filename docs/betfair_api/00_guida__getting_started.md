# Getting Started

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687786>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687786`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

1330pxcircleflatpipe

## Login

**The Betfair API offers three login flows for developers, depending on the use case of your application:**.

* **Non-Interactive login**- if you are building an application that will run autonomously, there is a separate login flow to follow to ensure your account remains secure.
* **Interactive login** - if you are building an application that will be used interactively, then this is the flow for you. This flow has two variants:

  + Interactive login - API method - This flow makes use of a JSON API Endpoint and is the simplest way to get started if you are looking to create your own login form.
  + Interactive login - Desktop Application- This login flow makes use of Betfair's login pages and allows your app to gracefully handle  all errors and re-directions in the same way as the Betfair website

## Request Headers

:info:atlassian-info#B3D4FF

* All requests must include a HTTP header named **"X-Application"** containing the Application Key assigned to you.
* All requests must include a HTTP header **"X-Authentication"** containing your sessionToken.
* All requests must include a HTTP header **"Accept"** with the value application/json

**Please note**: The only exceptions to the above are some of the [Account Operations](https://betfair-developer-docs.atlassian.net/wiki/pages/createpage.action?spaceKey=1smk3cen4v3lu3yomq5qye0ni&title=Accounts%20Operations%20%28Vendor%20API%29&linkCreation=true&fromPageId=2687786) ([Vendor API](https://betfair-developer-docs.atlassian.net/wiki/pages/createpage.action?spaceKey=1smk3cen4v3lu3yomq5qye0ni&title=Accounts%20Operations%20%28Vendor%20API%29&linkCreation=true&fromPageId=2687786) ) which require the **X-Authentication** HTTP header only.

**You can call the API at one of two endpoints, depending on which style of request you want to use.**

## API Endpoints

You can make requests and place bets on UK & international markets by accessing the Global Exchange via the following endpoints.

:info:atlassian-info#B3D4FF

All API requests should be sent as **POST**.

## Betting API

Please find the details for the current **Betting API** endpoints:

**Global Exchange**

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<method> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/betting/json-rpc/v1> | <method> | SportsAPING/v1.0/listMarketBook |
| JSON REST | <https://api.betfair.com/exchange/betting/rest/v1.0>/ |  | listMarketBook/ |

## Account API

You can make requests for your UK Exchange wallet information by accessing the Global Exchange via the following endpoints.

Please find the details for the current **Accounts API** endpoints:

**Global Exchange**

| **Interface** | **Endpoint** | **JSON-RPC Prefix** | **<method> Example** |
| --- | --- | --- | --- |
| JSON-RPC | <https://api.betfair.com/exchange/account/json-rpc/v1> | <method> | AccountAPING/v1.0/getAccountFunds |
| JSON REST | <https://api.betfair.com/exchange/account/rest/v1.0> |  | getAccountFunds/ |

## **Spanish & Italian Exchange**

Please see separate documentation for the Spanish & Italian Exchange

## JSON

You can POST a request to the API at:

<https://api.betfair.com/exchange/betting/rest/v1.0/><operation name>. So, to call the listEventTypes method, you would POST to: <https://api.betfair.com/exchange/betting/rest/v1.0>[/listEventTypes/](https://beta-api.betfair.com/rest/v1.0/listEventTypes/)

The POST data contains the request parameters. For listEventTypes, the only required parameter is a filter to select markets. You can pass an empty filter to select all markets, in which case listEventTypes returns the EventTypes associated with all available markets.

**JSON POST Data**

none{
"filter" : { }
}

**Python Example JSON Request**

noneimport requests
import json
endpoint = "https://api.betfair.com/exchange/betting/rest/v1.0/"
header = { 'X-Application' : 'APP\_KEY\_HERE', 'X-Authentication' : 'SESSION\_TOKEN\_HERE' ,'content-type' : 'application/json' }
json\_req='{"filter":{ }}'
url = endpoint + "listEventTypes/"
response = requests.post(url, data=json\_req, headers=header)
print json.dumps(json.loads(response.text), indent=3)

## JSON-RPC

You can POST a request to the API using [JSON-RPC](http://en.wikipedia.org/wiki/JSON-RPC) at:

<https://api.betfair.com/exchange/betting/json-rpc/v1>

The POST data should contain a valid JSON-RPC formatted request where the "params" field contains the request parameters and the "method" field contains the API method you are calling, specified like "SportsAPING/v1.0/<operation name>.

For example, if you were calling the listCompetitions operation and passing in a filter to find all markets with a corresponding event type id of 1 (i.e., all Football markets), the POST data for the JSON-RPC endpoint would be:

**Example JSON-RPC POST data**

js{
"params": {
"filter": {
"eventTypeIds": [1]
}
},
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listCompetitions",
"id": 1
}

Here's a quick example Python program that uses JSON-RPC and returns the list of EventTypes (Sports) available:

##### **JSON-RPC Python Example**

pyimport requests
import json
url="https://api.betfair.com/exchange/betting/json-rpc/v1"
header = { 'X-Application' : 'APP\_KEY\_HERE', 'X-Authentication' : 'SESSION\_TOKEN' ,'content-type' : 'application/json' }
jsonrpc\_req='{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEventTypes", "params": {"filter":{ }}, "id": 1}'
response = requests.post(url, data=jsonrpc\_req, headers=header)
print json.dumps(json.loads(response.text), indent=3)

And the response from the above:

**EventTypeResult**

json[
{
"jsonrpc": "2.0",
"result": [
{
"eventType": {
"id": "468328",
"name": "Handball"
},
"marketCount": 11
},
{
"eventType": {
"id": "1",
"name": "Soccer"
},
"marketCount": 25388
},
{
"eventType": {
"id": "2",
"name": "Tennis"
},
"marketCount": 402
},
{
"eventType": {
"id": "3",
"name": "Golf"
},
"marketCount": 79
},
{
"eventType": {
"id": "4",
"name": "Cricket"
},
"marketCount": 192
},
{
"eventType": {
"id": "5",
"name": "Rugby Union"
},
"marketCount": 233
},
{
"eventType": {
"id": "6",
"name": "Boxing"
},
"marketCount": 18
},
{
"eventType": {
"id": "7",
"name": "Horse Racing"
},
"marketCount": 398
},
{
"eventType": {
"id": "8",
"name": "Motor Sport"
},
"marketCount": 50
},
{
"eventType": {
"id": "7524",
"name": "Ice Hockey"
},
"marketCount": 521
},
{
"eventType": {
"id": "10",
"name": "Special Bets"
},
"marketCount": 39
},
{
"eventType": {
"id": "451485",
"name": "Winter Sports"
},
"marketCount": 7
},
{
"eventType": {
"id": "11",
"name": "Cycling"
},
"marketCount": 1
},
{
"eventType": {
"id": "136332",
"name": "Chess"
},
"marketCount": 1
},
{
"eventType": {
"id": "7522",
"name": "Basketball"
},
"marketCount": 617
},
{
"eventType": {
"id": "1477",
"name": "Rugby League"
},
"marketCount": 91
},
{
"eventType": {
"id": "4339",
"name": "Greyhound Racing"
},
"marketCount": 298
},
{
"eventType": {
"id": "6231",
"name": "Financial Bets"
},
"marketCount": 44
},
{
"eventType": {
"id": "2378961",
"name": "Politics"
},
"marketCount": 23
},
{
"eventType": {
"id": "998917",
"name": "Volleyball"
},
"marketCount": 66
},
{
"eventType": {
"id": "998919",
"name": "Bandy"
},
"marketCount": 4
},
{
"eventType": {
"id": "998918",
"name": "Bowls"
},
"marketCount": 17
},
{
"eventType": {
"id": "26420387",
"name": "Mixed Martial Arts"
},
"marketCount": 52
},
{
"eventType": {
"id": "3503",
"name": "Darts"
},
"marketCount": 21
},
{
"eventType": {
"id": "2152880",
"name": "Gaelic Games"
},
"marketCount": 2
},
{
"eventType": {
"id": "6422",
"name": "Snooker"
},
"marketCount": 22
},
{
"eventType": {
"id": "6423",
"name": "American Football"
},
"marketCount": 171
},
{
"eventType": {
"id": "315220",
"name": "Poker"
},
"marketCount": 2
},
{
"eventType": {
"id": "7511",
"name": "Baseball"
},
"marketCount": 7
}
],
"id": 1
}
]

## API Demo Tools

Our **Demo Tools** can be used by developers for quick experimentation and interaction with the production API system

## Example Requests

This section shows how you might call the Betting API  to retrieve information.

This section includes examples of how to request the following information in jsonrpc format:

33falsenonelisttrue

### Request A List Of Available Event Types listEvents

You can make a request using the listEventTypes service which will return a response containing the eventTypes (e.g. Soccer, Horse Racing etc.) that are currently available on Betfair.

**listEventTypes Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listEventTypes",
"params": {
"filter": {}
},
"id": 1
}
]

**listEventTypes Response**

json[
{
"jsonrpc": "2.0",
"result": [
{
"eventType": {
"id": "468328",
"name": "Handball"
},
"marketCount": 11
},
{
"eventType": {
"id": "1",
"name": "Soccer"
},
"marketCount": 25388
},
{
"eventType": {
"id": "2",
"name": "Tennis"
},
"marketCount": 402
},
{
"eventType": {
"id": "3",
"name": "Golf"
},
"marketCount": 79
},
{
"eventType": {
"id": "4",
"name": "Cricket"
},
"marketCount": 192
},
{
"eventType": {
"id": "5",
"name": "Rugby Union"
},
"marketCount": 233
},
{
"eventType": {
"id": "6",
"name": "Boxing"
},
"marketCount": 18
},
{
"eventType": {
"id": "7",
"name": "Horse Racing"
},
"marketCount": 398
},
{
"eventType": {
"id": "8",
"name": "Motor Sport"
},
"marketCount": 50
},
{
"eventType": {
"id": "7524",
"name": "Ice Hockey"
},
"marketCount": 521
},
{
"eventType": {
"id": "10",
"name": "Special Bets"
},
"marketCount": 39
},
{
"eventType": {
"id": "451485",
"name": "Winter Sports"
},
"marketCount": 7
},
{
"eventType": {
"id": "11",
"name": "Cycling"
},
"marketCount": 1
},
{
"eventType": {
"id": "136332",
"name": "Chess"
},
"marketCount": 1
},
{
"eventType": {
"id": "7522",
"name": "Basketball"
},
"marketCount": 617
},
{
"eventType": {
"id": "1477",
"name": "Rugby League"
},
"marketCount": 91
},
{
"eventType": {
"id": "4339",
"name": "Greyhound Racing"
},
"marketCount": 298
},
{
"eventType": {
"id": "6231",
"name": "Financial Bets"
},
"marketCount": 44
},
{
"eventType": {
"id": "2378961",
"name": "Politics"
},
"marketCount": 23
},
{
"eventType": {
"id": "998917",
"name": "Volleyball"
},
"marketCount": 66
},
{
"eventType": {
"id": "998919",
"name": "Bandy"
},
"marketCount": 4
},
{
"eventType": {
"id": "998918",
"name": "Bowls"
},
"marketCount": 17
},
{
"eventType": {
"id": "26420387",
"name": "Mixed Martial Arts"
},
"marketCount": 52
},
{
"eventType": {
"id": "3503",
"name": "Darts"
},
"marketCount": 21
},
{
"eventType": {
"id": "2152880",
"name": "Gaelic Games"
},
"marketCount": 2
},
{
"eventType": {
"id": "6422",
"name": "Snooker"
},
"marketCount": 22
},
{
"eventType": {
"id": "6423",
"name": "American Football"
},
"marketCount": 171
},
{
"eventType": {
"id": "315220",
"name": "Poker"
},
"marketCount": 2
},
{
"eventType": {
"id": "7511",
"name": "Baseball"
},
"marketCount": 7
}
],
"id": 1
}
]

### Request a List of Events for an Event Type eventType

The below example demonstrates how to retrieve a list of events using listEvents (eventIds) for a specific event type. The request shows how to retrieve all Soccer events that are taking place in a single day.

**listEvents Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listEvents",
"params": {
"filter": {
"eventTypeIds": [
"1"
],
"marketStartTime": {
"from": "2014-03-13T00:00:00Z",
"to": "2014-03-13T23:59:00Z"
}
}
},
"id": 1
}
]

**listEvents Response**

json[
{
"jsonrpc": "2.0",
"result": [
{
"event": {
"id": "27165668",
"name": "Al-Wahda (KSA) v Hajer (KSA)",
"countryCode": "SA",
"timezone": "GMT",
"openDate": "2014-03-13T13:30:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165665",
"name": "Al Hussein v Mansheyat Bani Hasan",
"countryCode": "JO",
"timezone": "GMT",
"openDate": "2014-03-13T15:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165425",
"name": "Daily Goals",
"countryCode": "GB",
"timezone": "Europe/London",
"openDate": "2014-03-13T18:00:00.000Z"
},
"marketCount": 1
},
{
"event": {
"id": "27165667",
"name": "Al Jeel v Al Draih",
"countryCode": "SA",
"timezone": "GMT",
"openDate": "2014-03-13T12:45:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165677",
"name": "Daventry Town v Kettering",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27160160",
"name": "Porto v Napoli",
"countryCode": "PT",
"timezone": "GMT",
"openDate": "2014-03-13T18:00:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27162435",
"name": "Bishops Stortford v Hayes And Yeading",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 2
},
{
"event": {
"id": "27166333",
"name": "Bosnia U19 v Serbia U19",
"timezone": "GMT",
"openDate": "2014-03-13T12:30:00.000Z"
},
"marketCount": 25
},
{
"event": {
"id": "27162436",
"name": "Maidenhead v Gosport Borough",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165673",
"name": "ASA Tel Aviv Uni (W) v FC Ramat Hasharon (W)",
"countryCode": "IL",
"timezone": "GMT",
"openDate": "2014-03-13T17:15:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27164435",
"name": "Forest Green v Braintree",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165684",
"name": "FC Lokomotivi Tbilisi v FC Saburtalo Tbilisi",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165686",
"name": "FC Sasco Tbilisi v Matchak Khelvachauri",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 18
},
{
"event": {
"id": "27165680",
"name": "FAR Rabat v Maghreb Fes",
"countryCode": "MA",
"timezone": "GMT",
"openDate": "2014-03-13T15:30:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165683",
"name": "FC Kolkheti Khobi v Samgurali Tskaltubo",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165682",
"name": "FC Dila Gori II v FC Dinamo Batumi",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165693",
"name": "Tilbury FC v Redbridge",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165688",
"name": "HUJK Emmaste v Kohtla-Jarve JK Jarve",
"countryCode": "EE",
"timezone": "GMT",
"openDate": "2014-03-13T17:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165690",
"name": "M Kishronot Hadera (W) v Maccabi Holon FC (W)",
"countryCode": "IL",
"timezone": "GMT",
"openDate": "2014-03-13T17:30:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27166225",
"name": "Litex Lovech v Cherno More",
"countryCode": "BG",
"timezone": "GMT",
"openDate": "2014-03-13T15:30:00.000Z"
},
"marketCount": 27
},
{
"event": {
"id": "27162412",
"name": "KR Reykjavik v IA Akranes",
"countryCode": "IS",
"timezone": "GMT",
"openDate": "2014-03-13T19:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27162473",
"name": "Atletico Huila v Tolima",
"countryCode": "CO",
"timezone": "GMT",
"openDate": "2014-03-13T23:00:00.000Z"
},
"marketCount": 27
},
{
"event": {
"id": "27162413",
"name": "KV v Selfoss",
"countryCode": "IS",
"timezone": "GMT",
"openDate": "2014-03-13T21:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165159",
"name": "August Town FC v Boys Town FC",
"countryCode": "JM",
"timezone": "GMT",
"openDate": "2014-03-13T20:30:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27165161",
"name": "Bogota v CD Barranquilla",
"countryCode": "CO",
"timezone": "GMT",
"openDate": "2014-03-13T20:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27166474",
"name": "Brasilia FC v Formosa",
"countryCode": "BR",
"timezone": "GMT",
"openDate": "2014-03-13T19:00:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27162538",
"name": "Arsenal FC v Penarol",
"countryCode": "AR",
"timezone": "GMT",
"openDate": "2014-03-13T22:00:00.000Z"
},
"marketCount": 40
},
{
"event": {
"id": "27166478",
"name": "Ware FC v AFC Sudbury",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27165505",
"name": "Tomsk v Tyumen",
"countryCode": "RU",
"timezone": "GMT",
"openDate": "2014-03-13T11:30:00.000Z"
},
"marketCount": 28
},
{
"event": {
"id": "27166477",
"name": "Needham Market FC v Thurrock",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27160154",
"name": "Lyon v Plzen",
"countryCode": "FR",
"timezone": "GMT",
"openDate": "2014-03-13T20:05:00.000Z"
},
"marketCount": 41
},
{
"event": {
"id": "27160155",
"name": "Ludogorets v Valencia",
"countryCode": "BG",
"timezone": "GMT",
"openDate": "2014-03-13T18:00:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27160152",
"name": "Tottenham v Benfica",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T20:05:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27162428",
"name": "Wadi Degla v El Shorta",
"countryCode": "EG",
"timezone": "GMT",
"openDate": "2014-03-13T13:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27160158",
"name": "FC Basel v Red Bull Salzburg",
"countryCode": "CH",
"timezone": "GMT",
"openDate": "2014-03-13T18:00:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27162427",
"name": "Ismaily v El Qanah",
"countryCode": "EG",
"timezone": "GMT",
"openDate": "2014-03-13T13:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27160159",
"name": "AZ Alkmaar v Anzhi Makhachkala",
"countryCode": "NL",
"timezone": "GMT",
"openDate": "2014-03-13T20:05:00.000Z"
},
"marketCount": 41
},
{
"event": {
"id": "27162426",
"name": "Al Ahly v El Entag El Harby",
"countryCode": "EG",
"timezone": "GMT",
"openDate": "2014-03-13T15:30:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27160156",
"name": "Sevilla v Betis",
"countryCode": "ES",
"timezone": "GMT",
"openDate": "2014-03-13T20:05:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27160157",
"name": "Juventus v Fiorentina",
"countryCode": "IT",
"timezone": "GMT",
"openDate": "2014-03-13T20:05:00.000Z"
},
"marketCount": 84
},
{
"event": {
"id": "27166336",
"name": "Becamex Binh Duong U19 v Khanh Hoa U19",
"countryCode": "VN",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27163800",
"name": "Lokomotiv Sofia v Chernomorets Burgas",
"countryCode": "BG",
"timezone": "GMT",
"openDate": "2014-03-13T12:00:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27162481",
"name": "Ljungskile v Torslanda",
"countryCode": "SE",
"timezone": "GMT",
"openDate": "2014-03-13T18:00:00.000Z"
},
"marketCount": 27
},
{
"event": {
"id": "27166338",
"name": "H Ironi Petah Tikva (W) v Maccabi Beer Sheva (W)",
"countryCode": "IL",
"timezone": "GMT",
"openDate": "2014-03-13T18:15:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27163801",
"name": "Concord Rangers v Havant and W",
"countryCode": "GB",
"timezone": "GMT",
"openDate": "2014-03-13T19:45:00.000Z"
},
"marketCount": 2
},
{
"event": {
"id": "27166340",
"name": "Maccabi Ironi Bat Yam v Hapoel Mahane Yehuda",
"countryCode": "IL",
"timezone": "GMT",
"openDate": "2014-03-13T17:00:00.000Z"
},
"marketCount": 15
},
{
"event": {
"id": "27162418",
"name": "Courts Young Lions v Woodlands Wellington",
"countryCode": "SG",
"timezone": "GMT",
"openDate": "2014-03-13T11:30:00.000Z"
},
"marketCount": 20
},
{
"event": {
"id": "27162417",
"name": "Balestier Khalsa v Tanjong Pagar Utd",
"countryCode": "SG",
"timezone": "GMT",
"openDate": "2014-03-13T11:30:00.000Z"
},
"marketCount": 20
}
],
"id": 1
}
]

### Request the Market Information for an Event market

The below example demonstrates how to retrieve all the market information that belongs to an event (excluding price data) using listMarketCatalogue. You can include one or more eventId's in the requests provide that you stay within the [Market Data Limits](https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Market+Data+Request+Limits)

**listMarketCatalogue Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listMarketCatalogue",
"params": {
"filter": {
"eventIds": [
"27165685"
]
},
"maxResults": "200",
"marketProjection": [
"COMPETITION",
"EVENT",
"EVENT\_TYPE",
"RUNNER\_DESCRIPTION",
"RUNNER\_METADATA",
"MARKET\_START\_TIME"
]
},
"id": 1
}
]

##### **listMarketCatalogue Response**

json[
{
"jsonrpc": "2.0",
"result": [
{
"marketId": "1.113197547",
"marketName": "FC Betlemi Keda +1",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 12,
"runners": [
{
"selectionId": 6843871,
"runnerName": "FC Betlemi Keda +1",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123618"
}
},
{
"selectionId": 6830600,
"runnerName": "FC Samtredia -1",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123619"
}
},
{
"selectionId": 151478,
"runnerName": "Draw",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123620"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197546",
"marketName": "FC Samtredia +1",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 0,
"runners": [
{
"selectionId": 6830597,
"runnerName": "FC Samtredia +1",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123615"
}
},
{
"selectionId": 6843874,
"runnerName": "FC Betlemi Keda -1",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123616"
}
},
{
"selectionId": 151478,
"runnerName": "Draw",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123617"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197492",
"marketName": "Total Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 246.82,
"runners": [
{
"selectionId": 285469,
"runnerName": "1 goals or more",
"handicap": -1,
"sortPriority": 1,
"metadata": {
"runnerId": "63123486"
}
},
{
"selectionId": 285470,
"runnerName": "2 goals or more",
"handicap": -2,
"sortPriority": 2,
"metadata": {
"runnerId": "63123487"
}
},
{
"selectionId": 285471,
"runnerName": "3 goals or more",
"handicap": -3,
"sortPriority": 3,
"metadata": {
"runnerId": "63123488"
}
},
{
"selectionId": 2795170,
"runnerName": "4 goals or more",
"handicap": -4,
"sortPriority": 4,
"metadata": {
"runnerId": "63123489"
}
},
{
"selectionId": 285473,
"runnerName": "5 goals or more",
"handicap": -5,
"sortPriority": 5,
"metadata": {
"runnerId": "63123490"
}
},
{
"selectionId": 285474,
"runnerName": "6 goals or more",
"handicap": -6,
"sortPriority": 6,
"metadata": {
"runnerId": "63123491"
}
},
{
"selectionId": 8215951,
"runnerName": "7 goals or more",
"handicap": -7,
"sortPriority": 7,
"metadata": {
"runnerId": "63123492"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197491",
"marketName": "Match Odds",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 7707.52,
"runners": [
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123483"
}
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123484"
}
},
{
"selectionId": 58805,
"runnerName": "The Draw",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123485"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197550",
"marketName": "Both teams to Score?",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 14.78,
"runners": [
{
"selectionId": 30246,
"runnerName": "Yes",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123625"
}
},
{
"selectionId": 30247,
"runnerName": "No",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123626"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197501",
"marketName": "Next Goal",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 3.34,
"runners": [
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123495"
}
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123496"
}
},
{
"selectionId": 69852,
"runnerName": "No Goal",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123497"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197502",
"marketName": "Over/Under 6.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 1255.79,
"runners": [
{
"selectionId": 2542448,
"runnerName": "Under 6.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123498"
}
},
{
"selectionId": 2542449,
"runnerName": "Over 6.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123499"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197505",
"marketName": "Correct Score",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 2380.92,
"runners": [
{
"selectionId": 1,
"runnerName": "0 - 0",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123505"
}
},
{
"selectionId": 4,
"runnerName": "0 - 1",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123506"
}
},
{
"selectionId": 9,
"runnerName": "0 - 2",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123507"
}
},
{
"selectionId": 16,
"runnerName": "0 - 3",
"handicap": 0,
"sortPriority": 4,
"metadata": {
"runnerId": "63123508"
}
},
{
"selectionId": 2,
"runnerName": "1 - 0",
"handicap": 0,
"sortPriority": 5,
"metadata": {
"runnerId": "63123509"
}
},
{
"selectionId": 3,
"runnerName": "1 - 1",
"handicap": 0,
"sortPriority": 6,
"metadata": {
"runnerId": "63123510"
}
},
{
"selectionId": 8,
"runnerName": "1 - 2",
"handicap": 0,
"sortPriority": 7,
"metadata": {
"runnerId": "63123511"
}
},
{
"selectionId": 15,
"runnerName": "1 - 3",
"handicap": 0,
"sortPriority": 8,
"metadata": {
"runnerId": "63123512"
}
},
{
"selectionId": 5,
"runnerName": "2 - 0",
"handicap": 0,
"sortPriority": 9,
"metadata": {
"runnerId": "63123513"
}
},
{
"selectionId": 6,
"runnerName": "2 - 1",
"handicap": 0,
"sortPriority": 10,
"metadata": {
"runnerId": "63123514"
}
},
{
"selectionId": 7,
"runnerName": "2 - 2",
"handicap": 0,
"sortPriority": 11,
"metadata": {
"runnerId": "63123515"
}
},
{
"selectionId": 14,
"runnerName": "2 - 3",
"handicap": 0,
"sortPriority": 12,
"metadata": {
"runnerId": "63123516"
}
},
{
"selectionId": 10,
"runnerName": "3 - 0",
"handicap": 0,
"sortPriority": 13,
"metadata": {
"runnerId": "63123517"
}
},
{
"selectionId": 11,
"runnerName": "3 - 1",
"handicap": 0,
"sortPriority": 14,
"metadata": {
"runnerId": "63123518"
}
},
{
"selectionId": 12,
"runnerName": "3 - 2",
"handicap": 0,
"sortPriority": 15,
"metadata": {
"runnerId": "63123519"
}
},
{
"selectionId": 13,
"runnerName": "3 - 3",
"handicap": 0,
"sortPriority": 16,
"metadata": {
"runnerId": "63123520"
}
},
{
"selectionId": 4506345,
"runnerName": "Any Unquoted ",
"handicap": 0,
"sortPriority": 17,
"metadata": {
"runnerId": "63123521"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197506",
"marketName": "Over/Under 2.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 4149.36,
"runners": [
{
"selectionId": 47972,
"runnerName": "Under 2.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123522"
}
},
{
"selectionId": 47973,
"runnerName": "Over 2.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123523"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197504",
"marketName": "Over/Under 5.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 2216.24,
"runners": [
{
"selectionId": 1485567,
"runnerName": "Under 5.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123503"
}
},
{
"selectionId": 1485568,
"runnerName": "Over 5.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123504"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197509",
"marketName": "Half Time/Full Time",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 97.3,
"runners": [
{
"selectionId": 6830596,
"runnerName": "FC Samtredia/FC Samtredia",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123536"
}
},
{
"selectionId": 6830599,
"runnerName": "FC Samtredia/Draw",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123537"
}
},
{
"selectionId": 8380726,
"runnerName": "FC Samtredia/FC Betlemi Ked",
"handicap": 0,
"sortPriority": 3,
"metadata": {
"runnerId": "63123538"
}
},
{
"selectionId": 6830595,
"runnerName": "Draw/FC Samtredia",
"handicap": 0,
"sortPriority": 4,
"metadata": {
"runnerId": "63123539"
}
},
{
"selectionId": 3710152,
"runnerName": "Draw/Draw",
"handicap": 0,
"sortPriority": 5,
"metadata": {
"runnerId": "63123540"
}
},
{
"selectionId": 6843869,
"runnerName": "Draw/FC Betlemi Ked",
"handicap": 0,
"sortPriority": 6,
"metadata": {
"runnerId": "63123541"
}
},
{
"selectionId": 8380727,
"runnerName": "FC Betlemi Ked/FC Samtredia",
"handicap": 0,
"sortPriority": 7,
"metadata": {
"runnerId": "63123542"
}
},
{
"selectionId": 6843873,
"runnerName": "FC Betlemi Ked/Draw",
"handicap": 0,
"sortPriority": 8,
"metadata": {
"runnerId": "63123543"
}
},
{
"selectionId": 6843870,
"runnerName": "FC Betlemi Ked/FC Betlemi Ked",
"handicap": 0,
"sortPriority": 9,
"metadata": {
"runnerId": "63123544"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197510",
"marketName": "Over/Under 1.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 1879.69,
"runners": [
{
"selectionId": 1221385,
"runnerName": "Under 1.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123545"
}
},
{
"selectionId": 1221386,
"runnerName": "Over 1.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123546"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197507",
"marketName": "Over/Under 4.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 3189.28,
"runners": [
{
"selectionId": 1222347,
"runnerName": "Under 4.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123524"
}
},
{
"selectionId": 1222346,
"runnerName": "Over 4.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123525"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197511",
"marketName": "Over/Under 3.5 Goals",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 3934.41,
"runners": [
{
"selectionId": 1222344,
"runnerName": "Under 3.5 Goals",
"handicap": 0,
"sortPriority": 1,
"metadata": {
"runnerId": "63123547"
}
},
{
"selectionId": 1222345,
"runnerName": "Over 3.5 Goals",
"handicap": 0,
"sortPriority": 2,
"metadata": {
"runnerId": "63123548"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
},
{
"marketId": "1.113197512",
"marketName": "Asian Handicap",
"marketStartTime": "2014-03-13T11:00:00.000Z",
"totalMatched": 1599.38,
"runners": [
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -4,
"sortPriority": 1
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 4,
"sortPriority": 2
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -3.75,
"sortPriority": 3
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 3.75,
"sortPriority": 4
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -3.5,
"sortPriority": 5
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 3.5,
"sortPriority": 6
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -3.25,
"sortPriority": 7
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 3.25,
"sortPriority": 8
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -3,
"sortPriority": 9
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 3,
"sortPriority": 10
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -2.75,
"sortPriority": 11
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 2.75,
"sortPriority": 12
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -2.5,
"sortPriority": 13
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 2.5,
"sortPriority": 14
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -2.25,
"sortPriority": 15
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 2.25,
"sortPriority": 16
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -2,
"sortPriority": 17
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 2,
"sortPriority": 18
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -1.75,
"sortPriority": 19
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 1.75,
"sortPriority": 20
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -1.5,
"sortPriority": 21
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 1.5,
"sortPriority": 22
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -1.25,
"sortPriority": 23
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 1.25,
"sortPriority": 24
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -1,
"sortPriority": 25
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 1,
"sortPriority": 26
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -0.75,
"sortPriority": 27
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0.75,
"sortPriority": 28
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -0.5,
"sortPriority": 29
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0.5,
"sortPriority": 30
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": -0.25,
"sortPriority": 31
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0.25,
"sortPriority": 32
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0,
"sortPriority": 33
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": 0,
"sortPriority": 34
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0.25,
"sortPriority": 35
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -0.25,
"sortPriority": 36
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0.5,
"sortPriority": 37
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -0.5,
"sortPriority": 38
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 0.75,
"sortPriority": 39
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -0.75,
"sortPriority": 40
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 1,
"sortPriority": 41
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -1,
"sortPriority": 42
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 1.25,
"sortPriority": 43
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -1.25,
"sortPriority": 44
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 1.5,
"sortPriority": 45
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -1.5,
"sortPriority": 46
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 1.75,
"sortPriority": 47
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -1.75,
"sortPriority": 48
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 2,
"sortPriority": 49
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -2,
"sortPriority": 50
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 2.25,
"sortPriority": 51
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -2.25,
"sortPriority": 52
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 2.5,
"sortPriority": 53
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -2.5,
"sortPriority": 54
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 2.75,
"sortPriority": 55
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -2.75,
"sortPriority": 56
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 3,
"sortPriority": 57
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -3,
"sortPriority": 58
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 3.25,
"sortPriority": 59
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -3.25,
"sortPriority": 60
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 3.5,
"sortPriority": 61
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -3.5,
"sortPriority": 62
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 3.75,
"sortPriority": 63
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -3.75,
"sortPriority": 64
},
{
"selectionId": 6830593,
"runnerName": "FC Samtredia",
"handicap": 4,
"sortPriority": 65,
"metadata": {
"runnerId": "63123613"
}
},
{
"selectionId": 6843866,
"runnerName": "FC Betlemi Keda",
"handicap": -4,
"sortPriority": 66,
"metadata": {
"runnerId": "63123614"
}
}
],
"eventType": {
"id": "1",
"name": "Soccer"
},
"competition": {
"id": "2356065",
"name": "Pirveli Liga"
},
"event": {
"id": "27165685",
"name": "FC Samtredia v FC Betlemi Keda",
"countryCode": "GE",
"timezone": "GMT",
"openDate": "2014-03-13T11:00:00.000Z"
}
}
],
"id": 1
}
]

### Horse Racing - Today's Win & Place Markets horseracing

The below request is an example of retrieving the available win/place horse racing markets for a specific day using listMarketCatalogue. The marketStartTime (from & to) should be updated accordingly.

**listMarketCatalogue Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listMarketCatalogue",
"params": {
"filter": {
"eventTypeIds": [
"7"
],
"marketTypeCodes": [
"WIN",
"PLACE"
],
"marketStartTime": {
"from": "2013-10-16T00:00:00Z",
"to": "2013-10-16T23:59:00Z"
}
},
"maxResults": "200",
"marketProjection": [
"MARKET\_START\_TIME",
"RUNNER\_METADATA",
"RUNNER\_DESCRIPTION",
"EVENT\_TYPE",
"EVENT",
"COMPETITION"
]
},
"id": 1
}
]

### Request a List of Football Competitions listcompetitions

To retrieve all football competitions, you can make a request to the listCompetitions operation with the following market filter:

**listCompetitions Request**

json{
"params": {
"filter": {
"eventTypeIds": [1]
}
},
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listCompetitions",
"id": 1
}

The "filter" selects all markets that have an eventTypeId of 1 (which is the event type for Football).

Then returns a list of Competitions and their Ids and how many markets are in each competition which are associated with those markets:

**listCompetitions Response**

json{
"jsonrpc": "2.0",
"result": [
{
"marketCount": 16,
"competition": {
"id": "833222",
"name": "Turkish Division 2"
}
},
{
"marketCount": 127,
"competition": {
"id": "5",
"name": "A-League 2012/13"
}
},
{
"marketCount": 212,
"competition": {
"id": "7",
"name": "Austrian Bundesliga"
}
},
{
"marketCount": 243,
"competition": {
"id": "11",
"name": "Dutch Jupiler League"
}
},
{
"marketCount": 206,
"competition": {
"id": "26207",
"name": "Greek Cup"
}
},
{
"marketCount": 117,
"competition": {
"id": "2129602",
"name": "Professional Development League"
}
},
{
"marketCount": 68,
"competition": {
"id": "803237",
"name": "Argentinian Primera B"
}
},
{
"marketCount": 1,
"competition": {
"id": "1842928",
"name": "OTB Bank Liga"
}
}
],
"id": 1
}

**Python Example**

import requests
import json
url="https://api.betfair.com/betting/json-rpc"
header = { 'X-Application' : "APP\_KEY\_HERE", 'X-Authentication : 'SESSION\_TOKEN', 'content-type' : 'application/json' }
jsonrpc\_req='{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCompetitions", "params": {"filter":{ "eventTypeIds" : [1] }}, "id": 1}'
print json.dumps(json.loads(jsonrpc\_req), indent=3)
print " "
response = requests.post(url, data=jsonrpc\_req, headers=header)
print json.dumps(json.loads(response.text), indent=3)

### Request Market Prices #marketprice

Once you have identified the market (marketId) that your interested in using the listMarketCatalogue service, you can request prices for that market using the listMarketBook API call.

This is an example showing a request for the best prices (back and lay) and trading volume including virtual bets.

**listMarketBook Request**

json[{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/listMarketBook",
"params": {
"marketIds": ["1.127771425"],
"priceProjection": {
"priceData": ["EX\_BEST\_OFFERS", "EX\_TRADED"],
"virtualise": "true"
}
},
"id": 1
}]
 
 

**listMarketBook Response**

json[{
"jsonrpc": "2.0",
"result": [{
"marketId": "1.127771425",
"isMarketDataDelayed": false,
"status": "OPEN",
"betDelay": 0,
"bspReconciled": false,
"complete": true,
"inplay": false,
"numberOfWinners": 1,
"numberOfRunners": 3,
"numberOfActiveRunners": 3,
"lastMatchTime": "2016-10-28T12:25:30.235Z",
"totalMatched": 188959.22,
"totalAvailable": 172932.96,
"crossMatching": true,
"runnersVoidable": false,
"version": 1469071410,
"runners": [{
"selectionId": 44790,
"handicap": 0.0,
"status": "ACTIVE",
"lastPriceTraded": 7.0,
"totalMatched": 12835.46,
"ex": {
"availableToBack": [{
"price": 7.0,
"size": 75.53
}, {
"price": 6.8,
"size": 538.6
}, {
"price": 6.6,
"size": 612.2
}],
"availableToLay": [{
"price": 7.2,
"size": 152.12
}, {
"price": 7.4,
"size": 1446.28
}, {
"price": 7.6,
"size": 1250.26
}],
"tradedVolume": [{
"price": 6.4,
"size": 3.0
}, {
"price": 6.6,
"size": 3.59
}, {
"price": 6.8,
"size": 1.42
}, {
"price": 7.0,
"size": 1736.55
}, {
"price": 7.2,
"size": 1601.31
}, {
"price": 7.4,
"size": 3580.1
}, {
"price": 7.6,
"size": 4236.59
}, {
"price": 7.8,
"size": 1367.18
}, {
"price": 8.0,
"size": 305.29
}, {
"price": 8.2,
"size": 0.39
}]
}
}, {
"selectionId": 489720,
"handicap": 0.0,
"status": "ACTIVE",
"lastPriceTraded": 1.63,
"totalMatched": 163020.94,
"ex": {
"availableToBack": [{
"price": 1.62,
"size": 4921.06
}, {
"price": 1.61,
"size": 3230.34
}, {
"price": 1.6,
"size": 2237.71
}],
"availableToLay": [{
"price": 1.63,
"size": 1001.76
}, {
"price": 1.64,
"size": 6737.59
}, {
"price": 1.65,
"size": 1701.27
}],
"tradedVolume": [{
"price": 1.53,
"size": 31.38
}, {
"price": 1.54,
"size": 3.77
}, {
"price": 1.57,
"size": 3582.76
}, {
"price": 1.58,
"size": 12037.21
}, {
"price": 1.59,
"size": 16530.57
}, {
"price": 1.6,
"size": 54607.84
}, {
"price": 1.61,
"size": 36015.53
}, {
"price": 1.62,
"size": 21108.23
}, {
"price": 1.63,
"size": 17575.94
}, {
"price": 1.64,
"size": 1527.67
}]
}
}, {
"selectionId": 58805,
"handicap": 0.0,
"status": "ACTIVE",
"lastPriceTraded": 4.2,
"totalMatched": 13102.81,
"ex": {
"availableToBack": [{
"price": 4.1,
"size": 3243.85
}, {
"price": 4.0,
"size": 1158.17
}, {
"price": 3.95,
"size": 254.04
}],
"availableToLay": [{
"price": 4.2,
"size": 1701.15
}, {
"price": 4.3,
"size": 3072.55
}, {
"price": 4.4,
"size": 2365.76
}],
"tradedVolume": [{
"price": 4.0,
"size": 457.79
}, {
"price": 4.1,
"size": 4434.67
}, {
"price": 4.2,
"size": 7845.01
}, {
"price": 4.3,
"size": 354.7
}, {
"price": 4.4,
"size": 6.6
}, {
"price": 4.9,
"size": 4.0
}]
}
}]
}],
"id": 1
}]

### Placing a Bet

**To place a bet you require the marketId and selectionId parameters from the****listMarketCatalogue****API call. The below parameters will place a normal Exchange bet at odds of 3.0 for a stake of £2.0.**

If the bet is placed successfully, a betId is returned in the placeOrders response

**placeOrders Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/placeOrders",
"params": {
"marketId": "1.109850906",
"instructions": [
{
"selectionId": "237486",
"handicap": "0",
"side": "LAY",
"orderType": "LIMIT",
"limitOrder": {
"size": "2",
"price": "3",
"persistenceType": "LAPSE"
}
}
]
},
"id": 1
}
]

**placeOrders Response**

json[
{
"jsonrpc": "2.0",
"result": {
"marketId": "1.109850906",
"instructionReports": [
{
"instruction": {
"selectionId": 237486,
"handicap": 0,
"limitOrder": {
"size": 2,
"price": 3,
"persistenceType": "LAPSE"
},
"orderType": "LIMIT",
"side": "LAY"
},
"betId": "31242604945",
"placedDate": "2013-10-30T14:22:47.000Z",
"averagePriceMatched": 0,
"sizeMatched": 0,
"status": "SUCCESS"
}
],
"status": "SUCCESS"
},
"id": 1
}
]

### Placing a Keep Bet placekeepbet

To place a Keep bet (bet remains unmatched until matched/cancelled) you need to specify the parameters below in the placeOrders request.

**placeOrders Request**

json[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.240636817","instructions":[{"selectionId":"47999","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"2","price":"10","persistenceType":"PERSIST"}}]}, "id": 1}]

**placeOrders Response**

json[{"jsonrpc":"2.0","result":{"status":"SUCCESS","marketId":"1.240636817","instructionReports":[{"status":"SUCCESS","instruction":{"selectionId":47999,"handicap":0.0,"limitOrder":{"size":2.0,"price":10.0,"persistenceType":"PERSIST"},"orderType":"LIMIT","side":"BACK"},"betId":"383626336337","placedDate":"2025-04-02T13:23:40.000Z","averagePriceMatched":0.0,"sizeMatched":0.0,"orderStatus":"EXECUTABLE"}]},"id":1}]

### Placing a Betfair SP Bet - MARKET\_ON\_CLOSE #PlacingABetfairSPBet

To place a bet on a selection at Betfair SP, you need to specify the parameters below in the placeOrders request. The below example would place a Betfair SP back bet on the required selection for a stake of £2.00.

**placeOrders Request**

json[
{
"jsonrpc": "2.0",
"method": "SportsAPING/v1.0/placeOrders",
"params": {
"marketId": "1.111836557",
"instructions": [
{
"selectionId": "5404312",
"handicap": "0",
"side": "BACK",
"orderType": "MARKET\_ON\_CLOSE",
"marketOnCloseOrder": {
"liability": "10"
}
}
]
},
"id": 1
}
]

**placeOrders Response**

json[
{
"jsonrpc": "2.0",
"result": {
"marketId": "1.111836557",
"instructionReports": [
{
"instruction": {
"selectionId": 5404312,
"handicap": 0,
"marketOnCloseOrder": {
"liability": 2
},
"orderType": "MARKET\_ON\_CLOSE",
"side": "BACK"
},
"betId": "31645233727",
"placedDate": "2013-11-12T12:07:29.000Z",
"status": "SUCCESS"
}
],
"status": "SUCCESS"
},
"id": 1
}
]

### Placing a Betfair SP Bet - LIMIT\_ON\_CLOSE

Below is an example of a Betfair SP Bet - using the orderType LIMIT\_ON\_CLOSE . Please refer to Additional Information#CurrencyParameters for Min BSP liability.

json[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"1.148683414","instructions":[{"selectionId":"15319829","handicap":"0","side":"LAY","orderType":"LIMIT\_ON\_CLOSE","limitOnCloseOrder":{"price":"5","liability":"10"}}]}, "id": 1}

### Retrieving Details of Bet/s Placed on a Market/s #openbets

You can use the listCurrentOrders request to retrieve a bet/s placed on a specific market/s.

**listCurrentOrders request**

json[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCurrentOrders", "params": {"marketIds":["1.117020524"],"orderProjection":"ALL","dateRange":{}}, "id": 1}]

**listCurrentOrders response**

json[{"jsonrpc":"2.0","result":{"currentOrders":[{"betId":"45496907354","marketId":"1.117020524","selectionId":9170340,"handicap":0.0,"priceSize":{"price":10.0,"size":5.0},"bspLiability":0.0,"side":"BACK","status":"EXECUTABLE","persistenceType":"LAPSE","orderType":"LIMIT","placedDate":"2015-01-22T13:01:53.000Z","averagePriceMatched":0.0,"sizeMatched":0.0,"sizeRemaining":5.0,"sizeLapsed":0.0,"sizeCancelled":0.0,"sizeVoided":0.0,"regulatorCode":"GIBRALTAR REGULATOR"}],"moreAvailable":false},"id":1}]

### Retrieving the Result of a Settled Market settledresult

To retrieve the result of a settled market, request listMarketBook **after** the market has been settled. The response will indicate whether the selection was settled as a 'WINNER' or 'LOSER' in the runners 'status' field. Settled market information is available for 90 days after settlement.

**listMarketBook Request to a Settled market**

json[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds":["1.114363660"],"priceProjection":{"priceData":["EX\_BEST\_OFFERS"]}}, "id": 1}]  

##### **listMarketBook Response**

json[
{
"jsonrpc": "2.0",
"result": [
{
"marketId": "1.114363660",
"isMarketDataDelayed": false,
"status": "CLOSED",
"betDelay": 0,
"bspReconciled": false,
"complete": true,
"inplay": false,
"numberOfWinners": 1,
"numberOfRunners": 14,
"numberOfActiveRunners": 0,
"totalMatched": 0,
"totalAvailable": 0,
"crossMatching": false,
"runnersVoidable": false,
"version": 767398001,
"runners": [
{
"selectionId": 8611526,
"handicap": 0,
"status": "REMOVED",
"adjustmentFactor": 9.1,
"removalDate": "2014-06-13T08:44:17.000Z",
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 8611527,
"handicap": 0,
"status": "REMOVED",
"adjustmentFactor": 3.5,
"removalDate": "2014-06-13T08:44:29.000Z",
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7920154,
"handicap": 0,
"status": "WINNER",
"adjustmentFactor": 17.5,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 1231425,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 4.3,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7533866,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 11.4,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 8220841,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 5.4,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7533883,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 8.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 8476712,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 8.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7012263,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 5.4,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7374225,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 8.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 8611525,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 0.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7659121,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 26.8,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 6996332,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 0.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
},
{
"selectionId": 7137541,
"handicap": 0,
"status": "LOSER",
"adjustmentFactor": 1.7,
"ex": {
"availableToBack": [],
"availableToLay": [],
"tradedVolume": []
}
}
]
}
],
"id": 1
}
]

### Retrieving Details of Bets on a Settled Market - including P&L & Commission paid. listClearedOrders

You can retrieve details of a settled bet/market using the listClearedOrders request. The below request uses a specific settledDatRange to limit the returned records and groupBy MARKET [**rollup**](https://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/listClearedOrders+-+Roll-up+Fields+Available) to group results at markeId level.

**listClearedOrders Request for bets on SETTLED markets**

json[{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listClearedOrders", "params": {"betStatus":"SETTLED","settledDateRange":{"from":"2018-04-30T23:00:00Z","to":"2018-05-31T23:00:00Z"},"groupBy":"MARKET"}, "id": 1}]

**Response**

json[{
"jsonrpc": "2.0",
"result": {
"clearedOrders": [{
"eventTypeId": "1",
"eventId": "28746818",
"marketId": "1.144281274",
"placedDate": "2018-05-29T10:48:50.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"betOutcome": "LOST",
"settledDate": "2018-05-29T19:12:41.000Z",
"lastMatchedDate": "2018-05-29T15:25:26.000Z",
"betCount": 8,
"commission": 0.0,
"priceReduced": false,
"profit": -16.0
}, {
"eventTypeId": "2",
"eventId": "28741289",
"marketId": "1.144157120",
"selectionId": 2830908,
"handicap": 0.0,
"betId": "126613673925",
"placedDate": "2018-05-25T08:26:20.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"side": "BACK",
"betOutcome": "WON",
"priceRequested": 1.28,
"settledDate": "2018-05-25T10:19:02.000Z",
"lastMatchedDate": "2018-05-25T08:26:40.000Z",
"betCount": 1,
"commission": 0.03,
"priceMatched": 1.28,
"priceReduced": false,
"sizeSettled": 2.0,
"profit": 0.56
}, {
"eventTypeId": "7",
"eventId": "28739568",
"marketId": "1.144114832",
"selectionId": 11295111,
"handicap": 0.0,
"placedDate": "2018-05-23T21:27:52.000Z",
"orderType": "LIMIT",
"betOutcome": "WON",
"settledDate": "2018-05-24T13:06:01.000Z",
"lastMatchedDate": "2018-05-24T13:04:24.000Z",
"betCount": 2,
"commission": 0.11,
"priceReduced": true,
"profit": 2.14,
"customerStrategyRef": "HedgerPro\_216"
}, {
"eventTypeId": "7",
"eventId": "28739518",
"marketId": "1.144114517",
"selectionId": 8912176,
"handicap": 0.0,
"betId": "126486489864",
"placedDate": "2018-05-23T15:31:57.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"side": "BACK",
"betOutcome": "LOST",
"priceRequested": 11.5,
"settledDate": "2018-05-23T17:12:22.000Z",
"lastMatchedDate": "2018-05-23T15:31:57.000Z",
"betCount": 1,
"commission": 0.0,
"priceMatched": 11.5,
"priceReduced": false,
"sizeSettled": 2.65,
"profit": -2.65
}, {
"eventTypeId": "1",
"eventId": "28724382",
"marketId": "1.143781550",
"selectionId": 2081063,
"handicap": 0.0,
"placedDate": "2018-05-21T15:43:12.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"side": "BACK",
"betOutcome": "LOST",
"priceRequested": 4.4,
"settledDate": "2018-05-21T20:53:27.000Z",
"lastMatchedDate": "2018-05-21T15:43:12.000Z",
"betCount": 3,
"commission": 0.0,
"priceMatched": 4.4,
"priceReduced": false,
"sizeSettled": 6.0,
"profit": -6.0
}, {
"eventTypeId": "1",
"eventId": "28717428",
"marketId": "1.143588270",
"selectionId": 18565,
"handicap": 0.0,
"betId": "125772703658",
"placedDate": "2018-05-16T14:48:53.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"side": "BACK",
"betOutcome": "WON",
"priceRequested": 2.18,
"settledDate": "2018-05-16T20:43:37.000Z",
"lastMatchedDate": "2018-05-16T14:48:53.000Z",
"betCount": 1,
"commission": 0.12,
"priceMatched": 2.18,
"priceReduced": false,
"sizeSettled": 2.0,
"profit": 2.36
}, {
"eventTypeId": "1",
"eventId": "28722989",
"marketId": "1.143732676",
"selectionId": 198689,
"handicap": 0.0,
"placedDate": "2018-05-14T13:22:56.000Z",
"persistenceType": "LAPSE",
"orderType": "LIMIT",
"side": "BACK",
"betOutcome": "WON",
"priceRequested": 1.42,
"settledDate": "2018-05-14T18:22:07.000Z",
"lastMatchedDate": "2018-05-14T13:22:56.000Z",
"betCount": 2,
"commission": 0.13,
"priceMatched": 1.42,
"priceReduced": false,
"sizeSettled": 6.0,
"profit": 2.52
}],
"moreAvailable": false
},
"id": 1
}]
