# Optimizing API Application Performance

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2699882>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2699882`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

To optimize performance and ensure that your application is interacting with the Betfair API as efficiently as possible, we strongly recommend the following as best practice.

## Expect: 100- Continue Header

Sending this header will result in the error: **"The remote server returned an error: (417) Expectation Failed."**

You should be aware that if using the .Net Framework you will need to set the relevant property in the ServicePointManager which then prevents the "Expect" header from being added:

***System.Net.ServicePointManager.Expect100Continue = false;***

## **Enabling HTTP compression**

HTTP compression is a capability built into both web servers and web clients to reduce the number of bytes transmitted in an HTTP response. This makes better use of available bandwidth and increases performance while reducing download time. When enabled, HTTP protocol data is compressed before it is sent from the server. Clients capable of receiving compressed HTTP data announce that they support compression in the HTTP header. Almost all modern web browsers support HTTP Compression by default.

The Betfair API uses HTTP to handle communication between API clients and servers. Therefore, the JSON messages can be compressed using the same HTTP compression used by web browsers. Custom API applications may need some modification before they can take advantage of this feature. Specifically, they need to send an additional HTTP header to indicate they support receipt of compressed responses from the API. In addition, some environments require you to explicitly decompress the response.

We would therefore recommend that all Betfair API request are sent with the ‘**Accept-Encoding: gzip, deflate’** request header.

## **HTTP Persistent connection**

We recommend that **Connection: keep-alive** header is set for all requests to guarantee a persistent connection and therefore reducing latency.

## **Other performance tips**

Additional advice regarding optimizing HTTPClient performance can be found via <http://hc.apache.org/httpclient-3.x/performance.html>
