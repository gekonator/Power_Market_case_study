# AOX_case_study

#### Q0. Explain the three stages in your own words 

The day-ahead market is a call market for short-term delivery contracts. On the afternoon before delivery, a lot of market participants submit buy and sell volume-price orders, and the auction determines one clearing price per 15-minute delivery block, which maximizes overall economic surplus. All accepted orders are executed at the same clearing price. The auction price of day-ahead market shows us the market's expectations, based on information available at the time of the auction, about supply and demand during that future delivery period

After the day-ahead auction clears there is an intraday market for the same delivery products. Unlike day-ahead, intraday is not a single auction with one clearing price. Trades execute continuously whenever buy and sell orders match. In this market participants can adjust their positions as new market information arrives. For the same delivery period, a producer sold 10 MWh but expects to generate only 8 MWh, so he can buy 2 MWh of the same delivery product on the intraday market to to reduce his expected imbalance exposure. Intraday price reflects updated estimates relative to day-ahead and the market’s updated estimate of the probability that the system will be short or long at delivery, and other important factors.

The imbalance settlement mechanism can charge or pay participants based on their contribution to system imbalance. There are two possible system states: the system can be short or long. If the system is long, additional energy is not needed and a long participant may receive a very low or negative imbalance price for that surplus. If the system is short, there is a deficit of electricity in the system, so TenneT activates upward balancing reserves, which can result in a very high imbalance settlement price. The imbalance price reflects the realised marginal cost of balancing the system.

I had never seen this market before, so the imbalance settlement mechanism was the most surprising thing for me. I did not realize that the electricity market and the settlement system can be so complex, and that generation plus imports must equal consumption plus exports. TenneT can activate balancing reserves, which can result in a very low or negative imbalance price for surplus energy when the system is long, and in a very high imbalance price when the system is short.

The second thing that surprised me was that the day-ahead market is a call market. During my CFA Level I preparation, when I read about this type of market, I thought that it was not useful because I did not know its practical application. But now I realize that this market is really useful here.


#### Data

The workbook does not explicitly state the unit for renewable forecast and outturn columns. I interpret them as average MW per 15-minute interval, based on their consistency with installed capacity, demand and flow data.

The workbook says that at this time UTC is one hour ahead of CET, but it is not true
CET is one hour ahead of UTC

/data/processed/nl_market_15m.csv :
time_utc | solar_da_mw | solar_actual_mw | solar_capacity_mw | wind_da_mw | wind_actual_total_mw | wind_actual_offshore_mw | wind_actual_onshore_mw | wind_capacity_mw | demand_DA_mw | demand_actual_mw | price_da_eur_mwh | price_imbalance_long_eur_mwh | price_imbalance_short_eur_mwh