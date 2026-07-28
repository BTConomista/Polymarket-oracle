# listMarketCatalogue

> **COPIA DI LAVORO** — testo di **Betfair**, non del progetto.
> Fonte: *Betfair Exchange API Documentation* — <https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687517>
> (spazio Confluence `1smk3cen4v3lu3yomq5qye0ni`, pagina id `2687517`; estratto il 2026-07-28
> con `scripts/fetch_betfair_docs.py`).
> **In caso di dubbio vince la pagina online**, che può essere più
> recente di questa copia: ri-esegui lo script per aggiornarla.

---

## Operation

listMarketCatalogue

#FFFFFF#C8D0E4listMarketCatalogue

**List<** **MarketCatalogue** **>**  [**listMarketCatalogue#listMarketCatalogue**](/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687517#listMarketCatalogue-listMarketCatalogue) **(** **MarketFilter** **filter**  ,Set< MarketProjection >marketProjection, MarketSort sort, **intmaxResults** ,Stringlocale **)**  **throws** **APINGException**

Returns a list of information about published (ACTIVE/SUSPENDED) markets that does not change (or changes very rarely). You use listMarketCatalogue to retrieve the name of the market, the names of selections and other information about markets.  Market Data Request Limits apply to requests made to listMarketCatalogue.

**Please note:** listMarketCatalogue does not return markets that are CLOSED.

| **Parameter name** | **Type** | **Required** | **Description** |
| --- | --- | --- | --- |
| filter | MarketFilter |  | The filter to select desired markets. All markets that match the criteria in the filter are selected. |
| marketProjection | Set< MarketProjection > |  | The type and amount of data returned about the market. |
| sort | MarketSort |  | The order of the results. Will default to **RANK** if not passed. **RANK** is an assigned priority that is determined by our Market Operations team in our back-end system. A result's overall rank is derived from the ranking given to the flowing attributes for the result. EventType, Competition, StartTime, MarketType, MarketId. For example, EventType is ranked by the most popular sports types and marketTypes are ranked in the following order: ODDS ASIAN LINE RANGE If all other dimensions of the result are equal, then the results are ranked in MarketId order. |
| maxResults | int |  | limit on the total number of results returned, must be greater than 0 and less than or equal to 1000 |
| locale | String |  | The language used for the response. If not specified, the default is returned. |

| **Return type** | **Description** |
| --- | --- |
| List< MarketCatalogue > | output data |

| **Throws** | **Description** |
| --- | --- |
| APINGException | Generic exception that is thrown if this operation fails for any reason. |

**Since 1.0.0**

## RUNNER\_METADATA Description

The RUNNER\_METADATA returned by listMarketCatalogue for **Horse Racing**(when available) is described in the table below.

| **Parameter** | **Description** | **Example** |
| --- | --- | --- |
| WEIGHT\_UNITS | The unit of weight used | pounds |
| ADJUSTED\_RATING | Adjusted ratings are race-specific ratings which reflect weights allocated in the race and, in some circumstances, the age of the horse. Collectively they represent the chance each runner has on form. <https://www.timeform.com/Racing/Articles/How_the_ratings_for_a_race_are_calculated> | 79 |
| DAM\_YEAR\_BORN | The year the horse’s mother's birth | 1997 |
| DAYS\_SINCE\_LAST\_RUN | The number of days since the horse last ran | 66 |
| WEARING | Any extra equipment the horse is wearing | tongue strap |
| DAMSIRE\_YEAR\_BORN | The year in which the horse's grandfather was born on its mothers side | 1988 |
| SIRE\_BRED | The country were the horse's father was bred | IRE |
| TRAINER\_NAME | The name of the horse's trainer | Fergal O'Brien |
| STALL\_DRAW | The stall number the horse is starting from | 10 |
| SEX\_TYPE | The sex of the horse | f |
| OWNER\_NAME | The owner of the horse | Mr M. C. Fahy |
| SIRE\_NAME | The name of the horse's father | Revoque |
| FORECASTPRICE\_NUMERATOR | The forecast price numerator | 13 |
| FORECASTPRICE\_DENOMINATOR | The forecast price denominator | 8 |
| JOCKEY\_CLAIM | The reduction in the weight that the horse carries for a particular jockey | 5 |
| WEIGHT\_VALUE | The weight of the horse | 163 |
| DAM\_NAME | The name of the horse's mother | Rare Gesture |
| AGE | The age of the horse | 7 |
| COLOUR\_TYPE | The colour of the horse | b |
| DAMSIRE\_BRED | The country were the horse's grandfather was born | IRE |
| DAMSIRE\_NAME | The name of the horse's grandfather | Shalford |
| SIRE\_YEAR\_BORN | The year the horse's father was born | 1994 |
| OFFICIAL\_RATING | The horses official rating | 97 |
| FORM | The horses recent form | 212246 |
| BRED | The country in which the horse was born | IRE |
| runnerId | The runnerId for the horse | 62434983 |
| JOCKEY\_NAME | The name of the jockey. **Please note**: This field will contain '**Reserve**' in the event that the horse has been entered into the market as a reserve runner. Any reserve runners will be withdrawn from the market once it has been confirmed that they will not run. | Paddy Brennan |
| DAM\_BRED | The country where the horse's mother was born | IRE |
| COLOURS\_DESCRIPTION | The textual description of the jockey silk | Royal blue and black check, white sleeves and cap |
| COLOURS\_FILENAME | A relative URL to an image file corresponding to the jockey silk. You must add the value of this field to the base URL: <https://content.betfair.com/feeds_images/Horses/SilkColours/> | c20140225lei/00058836.jpg |
| CLOTH\_NUMBER | The number on the saddle-cloth | 5 |
| CLOTH\_NUMBER ALPHA | The number on the saddle-cloth. For US Racing were the runner is paired, this field will display the cloth number of the paired runner e.g. "1A" |  |
