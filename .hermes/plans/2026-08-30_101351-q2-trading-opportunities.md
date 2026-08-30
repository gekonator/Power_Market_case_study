# Q2 trading opportunities plan

**Goal:** Select no more than three or four defensible intraday opportunities and explain the signal, timing, execution and risk for each without using hindsight as if it were available live.

## Working episodes

Start with the timestamped market event and scan the full affected delivery curve before selecting a contract:

1. After the 09:46 NESO publication, compare the 12:00–13:00, 13:00–14:00, 14:00–15:00 and 15:00–16:00 hourly products. Test both outright longs and relative-value differences across the curve.
2. After the 12:04 NESO publication, compare the 16:00–17:00, 17:00–18:00 and 18:00–19:00 hourly products. Again, select the product only after comparing repricing, liquidity, time to delivery and risk.
3. Test any short/mean-reversion idea across the whole curve rather than assigning it to 13:00–14:00 or 17:00–18:00 in advance.

The final opportunities are selected after this comparison. A product with a high realised imbalance price is not automatically the best intraday trade: the position must be exited before gate closure, and the relevant P&L is the intraday entry-to-exit move.

## Process

### 1. Define the information set

For each episode and candidate product, separate:

- information available before entry: publication times, auction volumes, revised schedules, available capacity, live intraday trades and any fundamentals whose publication timing is supported;
- information available only after delivery: actual generation and demand, Balance Delta activations and imbalance prices.

Realised data may validate the outcome but cannot justify the entry.

### 2. Reconstruct each affected delivery curve

Using deduplicated `trade_id` records, calculate for every hourly product affected by the publication:

- price immediately before and after the proposed signal;
- a realistic entry range rather than the best printed trade;
- subsequent maximum and minimum price;
- trading volume around entry;
- time remaining to delivery.

Compare the products first, then nominate candidate trades.

### 3. Test the candidates

A trade survives only if it has:

- a timestamped observable signal;
- a clear direction and named delivery product;
- a plausible entry actually printed after the signal;
- rough position size in MW and resulting MWh exposure;
- an invalidation condition and cut level;
- an exit rule before delivery;
- risks that could have invalidated the thesis.

Reject opportunities that are visible only with realised imbalance prices.

### 4. Choose the final set

Prefer three strong opportunities over four repetitive ones. Possible structures include:

- one outright long in the best risk-adjusted product after the initial publication;
- one curve or mean-reversion trade only if justified live;
- one outright long in the best product after the later NESO shock;
- an optional fourth only if it adds a different mechanism.

### 5. Write Q2

Add a compact comparison table followed by one short explanation per opportunity. Suggested columns:

| First identifiable | Product | Direction | Signal | Entry | Size | Cut | Exit | Ex-post outcome |

Keep the ex-post outcome in a separate column or paragraph.

## Files likely to change

- `README.md`
- possibly one small Q2 calculation script under `code/`
- possibly one compact Q2 figure or table under `outputs/`, only if it adds information beyond the existing intraday charts

## Verification

- Every entry price must exist in the deduplicated trade tape after the signal time.
- Every signal must have a defensible publication timestamp.
- MW sizing must be converted correctly to MWh for the product duration.
- No realised imbalance price or actual fundamental may appear in the entry rationale.
- Q2 must directly answer attractiveness, first identifiability, action, rough size, entry and cut, as requested in the brief.
