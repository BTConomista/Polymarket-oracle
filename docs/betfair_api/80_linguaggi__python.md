# Python

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687059>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687059`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

12flat

This documentation refers to the code available at <https://github.com/betfair/API-NG-sample-code/tree/master/python>.

## Prerequisites:

1. python v 2.7.2  - <http://www.python.org/getit/releases/2.7.2/>
2. urllib2 python module  - <http://docs.python.org/2/library/urllib2.html>
3. json python module - <http://docs.python.org/2/library/json.html>
4. datetime python module - <http://docs.python.org/2/library/datetime.html>
5. sys python module - <http://docs.python.org/2/library/sys.html>

### A note on Python3:

We have added a python3 version of the json-rpc script, which is in the [python subdirectory](https://github.com/betfair/API-NG-sample-code/tree/master/python) of the github sample code repo named ApiNgDemoJsonRpc-python3.py. This functions exactly the same way as the python 2.7X sample, but with compatibility tweaks for Python 3. The documentation below reflects the python 2.7X code, but the

## Installation:

You only need to clone or download the repository linked to above. If you do not have a valid Python 2.7.X installation already then please follow the download and installation instructions from the [python wiki](http://wiki.python.org/moin/BeginnersGuide/Download).

### Run the scripts

Change to the directory where you cloned the repository to and run the sample of your choice as follows:

JSON-RPC  **→**

python ApiNgDemoJsonRpc.py <appkey> <sessiontoken>

Rescript  **→**

python ApiNgDemoRescript.py <appkey> <sessiontoken>

 Note:  If the command line arguments for application key and session token are not provided then the script will prompt for application key and session token

## Calling API-NG with JSON-RPC protoco**l**

Method and param values need to be changed based on the required service operation.You can execute multiple service operation together with a single call using batch json-rpc call where you can correlate the responses with value of the id.

pyURL = url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
jsonrpc\_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEventTypes", "params": {"filter":{ }}, "id": 1}'
headers = {'X-Application': appKey, 'X-Authentication': sessionToken, 'content-type': 'application/json'}
def callAping(jsonrpc\_req):
try:
req = urllib2.Request(url, jsonrpc\_req, headers)
response = urllib2.urlopen(req)
jsonResponse = response.read()
return jsonResponse
except urllib2.URLError:
print 'Oops no service available at ' + str(url)
exit()
except urllib2.HTTPError:
print 'Oops not a valid operation from the service ' + str(url)
exit()

## Calling API-NG with Rescript protocol

pyurl = 'https://api.betfair.com/rest/v1.0/${operationName}/'
headers = {'X-Application': appKey, 'X-Authentication': sessionToken, 'content-type': 'application/json', 'accept': 'application/json'}
request = '{"filter":{"eventTypeIds":["7"],"marketCountries":["GB"],"marketStartTime":{"from":"2013-05-21T00:00:00Z"}},"sort":"FIRST\_TO\_START","maxResults":"1","marketProjection":["RUNNER\_METADATA"]}'
def callAping(url, request):
try:
req = urllib2.Request(url, request, headers)
response = urllib2.urlopen(req)
jsonResponse = response.read()
return jsonResponse
except urllib2.URLError:
print 'Oops there is some issue with the request'
exit()
except urllib2.HTTPError:
print 'Oops there is some issue with the request' + urllib2.HTTPError.getcode()
exit()

### Get next available horse racing market and runner information using listMarketCatalogue

**JSON-RPC**

pydef getMarketCatalogueForNextGBWin(eventTypeID):
if (eventTypeID is not None):
print 'Calling listMarketCatalouge Operation to get MarketID and selectionId'
now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
market\_catalogue\_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", "params": {"filter":{"eventTypeIds":["' + eventTypeID + '"],"marketCountries":["GB"],"marketTypeCodes":["WIN"],'\
'"marketStartTime":{"from":"' + now + '"}},"sort":"FIRST\_TO\_START","maxResults":"1","marketProjection":["RUNNER\_METADATA"]}, "id": 1}'
"""
print market\_catalogue\_req
"""
market\_catalogue\_response = callAping(market\_catalogue\_req)
"""
print market\_catalogue\_response
"""
market\_catalouge\_loads = json.loads(market\_catalogue\_response)
try:
market\_catalouge\_results = market\_catalouge\_loads['result']
return market\_catalouge\_results
except:
print 'Exception from API-NG' + str(market\_catalouge\_results['error'])
exit()
def getMarketId(marketCatalougeResult):
if( marketCatalougeResult is not None):
for market in marketCatalougeResult:
return market['marketId']
def getSelectionId(marketCatalougeResult):
if(marketCatalougeResult is not None):
for market in marketCatalougeResult:
return market['runners'][0]['selectionId']
marketCatalougeResult = getMarketCatalogueForNextGBWin(horseRacingEventTypeID)
marketid = getMarketId(marketCatalougeResult)
runnerId = getSelectionId(marketCatalougeResult)

### **Rescript**

pydef getMarketCatalouge(eventTypeID):
if(eventTypeID is not None):
print 'Calling listMarketCatalouge Operation to get MarketID and selectionId'
endPoint = 'https://api.betfair.com/rest/v1.0/listMarketCatalogue/'
now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
market\_catalouge\_req = '{"filter":{"eventTypeIds":["' + eventTypeID + '"],"marketCountries":["GB"],"marketStartTime":{"from":"' + now + '"}},"sort":"FIRST\_TO\_START","maxResults":"1","marketProjection":["RUNNER\_METADATA"]}'
market\_catalouge\_response = callAping(endPoint, market\_catalouge\_req)
market\_catalouge\_loads = json.loads(market\_catalouge\_response)
return market\_catalouge\_loads
def getMarketId(marketCatalougeResult):
if(marketCatalougeResult is not None):
for market in marketCatalougeResult:
return market['marketId']
def getSelectionId(marketCatalougeResult):
if(marketCatalougeResult is not None):
for market in marketCatalougeResult:
return market['runners'][0]['selectionId']
marketCatalougeResult = getMarketCatalouge(horseRacingEventTypeID)
marketid = getMarketId(marketCatalougeResult)
runnerId = getSelectionId(marketCatalougeResult)

### Get available price for the next horse racing market using listMarketBook

**JSON-RPC**

pydef getMarketBookBestOffers(marketId):
print 'Calling listMarketBook to read prices for the Market with ID :' + marketId
market\_book\_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds":["' + marketId + '"],"priceProjection":{"priceData":["EX\_BEST\_OFFERS"]}}, "id": 1}'
"""
print market\_book\_req
"""
market\_book\_response = callAping(market\_book\_req)
"""
print market\_book\_response
"""
market\_book\_loads = json.loads(market\_book\_response)
try:
market\_book\_result = market\_book\_loads['result']
return market\_book\_result
except:
print 'Exception from API-NG' + str(market\_book\_result['error'])
exit()
def printPriceInfo(market\_book\_result):
if(market\_book\_result is not None):
print 'Please find Best three available prices for the runners'
for marketBook in market\_book\_result:
runners = marketBook['runners']
for runner in runners:
print 'Selection id is ' + str(runner['selectionId'])
if (runner['status'] == 'ACTIVE'):
print 'Available to back price :' + str(runner['ex']['availableToBack'])
print 'Available to lay price :' + str(runner['ex']['availableToLay'])
else:
print 'This runner is not active'
market\_book\_result = getMarketBookBestOffers(marketid)
printPriceInfo(market\_book\_result)

**Rescript**

pydef getMarketBook(marketId):
if( marketId is not None):
print 'Calling listMarketBook to read prices for the Market with ID :' + marketId
market\_book\_req = '{"marketIds":["' + marketId + '"],"priceProjection":{"priceData":["EX\_BEST\_OFFERS"]}}'
endPoint = 'https://api.betfair.com/rest/v1.0/listMarketBook/'
market\_book\_response = callAping(endPoint, market\_book\_req)
market\_book\_loads = json.loads(market\_book\_response)
return market\_book\_loads
def printPriceInfo(market\_book\_result):
print 'Please find Best three available prices for the runners'
for marketBook in market\_book\_result:
try:
runners = marketBook['runners']
for runner in runners:
print 'Selection id is ' + str(runner['selectionId'])
if (runner['status'] == 'ACTIVE'):
print 'Available to back price :' + str(runner['ex']['availableToBack'])
print 'Available to lay price :' + str(runner['ex']['availableToLay'])
else:
print 'This runner is not active'
except:
print 'No runners available for this market'
market\_book\_result = getMarketBook(marketid)
printPriceInfo(market\_book\_result)

### Placing a bet on first active runner from next horse racing market using placeOrders

**JSON-RPC**

pydef placeFailingBet(marketId, selectionId):
if( marketId is not None and selectionId is not None):
print 'Calling placeOrder for marketId :' + marketId + ' with selection id :' + str(selectionId)
place\_order\_Req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"' + marketId + '","instructions":'\
'[{"selectionId":"' + str(
selectionId) + '","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"0.01","price":"1.50","persistenceType":"LAPSE"}}],"customerRef":"test12121212121"}, "id": 1}'
"""
print place\_order\_Req
"""
place\_order\_Response = callAping(place\_order\_Req)
place\_order\_load = json.loads(place\_order\_Response)
try:
place\_order\_result = place\_order\_load['result']
print 'Place order status is ' + place\_order\_result['status']
"""
print 'Place order error status is ' + place\_order\_result['errorCode']
"""
print 'Reason for Place order failure is ' + place\_order\_result['instructionReports'][0]['errorCode']
except:
print 'Exception from API-NG' + str(place\_order\_result['error'])
placeBet(marketid, runnerId)

**Rescript**

pydef placeBet(marketId, selectionId):
if( marketId is not None and selectionId is not None):
print 'Calling placeOrder for marketId :' + marketId + ' with selection id :' + str(selectionId)
place\_order\_Req = '{"marketId":"' + marketId + '","instructions":'\
'[{"selectionId":"' + str(
selectionId) + '","handicap":"0","side":"BACK","orderType":"LIMIT","limitOrder":{"size":"1.01","price":"1.50","persistenceType":"LAPSE"}}],"customerRef":"test12121212121"}'
endPoint = 'https://api.betfair.com/rest/v1.0/placeOrders/'
place\_order\_Response = callAping(endPoint, place\_order\_Req)
place\_order\_load = json.loads(place\_order\_Response)
print 'Place order status is ' + place\_order\_load['status']
print 'Reason for Place order failure is ' + place\_order\_load['instructionReports'][0]['errorCode']
placeBet(marketid, runnerId)
