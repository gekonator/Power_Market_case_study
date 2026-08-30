from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
auctions_path = project_root / "data/raw/neso_auctions.csv"
flows_path = project_root / "data/raw/nl_flows.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_dir = project_root / "outputs/figures"

publication_time_text = "03:18:41"
decision_time_text = "08:00:00"
delivery_starts = ["09:00:00", "10:00:00", "11:00:00"]

publication_time = pd.to_datetime(publication_time_text, format="%H:%M:%S")
decision_time = pd.to_datetime(decision_time_text, format="%H:%M:%S")
output_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: information already known from DA schedules and the NESO disclosure.
auctions = pd.read_csv(auctions_path)
flows = pd.read_csv(flows_path)

neso_hourly = (
    auctions[
        (auctions["published_time_utc"] == publication_time_text)
        & (auctions["delivery_start_time_utc"].isin(delivery_starts))
    ]
    .groupby("delivery_start_time_utc", as_index=False)["bn_volume_mw"]
    .sum()
    .rename(columns={"bn_volume_mw": "neso_britned_buy_mw"})
)

britned_da = flows[
    (flows["border"] == "GB")
    & (flows["time_utc"].isin(delivery_starts))
][["time_utc", "da_net_nl_exports_mw"]].copy()
britned_da["da_britned_import_mw"] = (
    -britned_da["da_net_nl_exports_mw"]
).clip(lower=0)

known_shock = neso_hourly.merge(
    britned_da,
    left_on="delivery_start_time_utc",
    right_on="time_utc",
    how="left",
    validate="one_to_one",
).sort_values("delivery_start_time_utc")

if known_shock[["neso_britned_buy_mw", "da_britned_import_mw"]].isna().any().any():
    raise ValueError("Missing DA BritNed schedule or NESO volume")

labels = known_shock["delivery_start_time_utc"].str.slice(0, 5)
x = list(range(len(known_shock)))
bar_width = 0.36

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(
    [position - bar_width / 2 for position in x],
    known_shock["da_britned_import_mw"],
    width=bar_width,
    color="tab:blue",
    alpha=0.8,
    label="DA scheduled BritNed import into NL",
)
ax.bar(
    [position + bar_width / 2 for position in x],
    known_shock["neso_britned_buy_mw"],
    width=bar_width,
    color="tab:red",
    alpha=0.8,
    label="BritNed Buy published by NESO at 03:18",
)
for position, (_, row) in zip(x, known_shock.iterrows()):
    ax.text(
        position - bar_width / 2,
        row["da_britned_import_mw"] + 10,
        f'{row["da_britned_import_mw"]:.0f}',
        ha="center",
        va="bottom",
        fontsize=9,
    )
    ax.text(
        position + bar_width / 2,
        row["neso_britned_buy_mw"] + 10,
        f'{row["neso_britned_buy_mw"]:.0f}',
        ha="center",
        va="bottom",
        fontsize=9,
    )
ax.set_title("Known BritNed supply shock at the 08:00 decision time")
ax.set_xlabel("Hourly delivery product, UTC")
ax.set_ylabel("Power, MW")
ax.set_xticks(x, [f"{start[:5]}–{(pd.to_datetime(start, format='%H:%M:%S') + pd.Timedelta(hours=1)):%H:%M}" for start in delivery_starts])
ax.grid(axis="y", alpha=0.3)
ax.legend()
fig.tight_layout()
known_shock_output = output_dir / "neso_known_britned_shock_0800_09_12.png"
fig.savefig(known_shock_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 2: only continuous executions available before the 08:00 decision.
trades = pd.read_csv(trades_path)
market = pd.read_csv(market_path)
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(delivery_starts))
].copy()
trades = trades.drop_duplicates(subset="trade_id")
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)
trades = trades[trades["execution_time"] < decision_time].copy()
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")

fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
for ax, delivery_start in zip(axes, delivery_starts):
    delivery_time = pd.to_datetime(delivery_start, format="%H:%M:%S")
    delivery_end = delivery_time + pd.Timedelta(hours=1)
    product_trades = trades[
        trades["delivery_start_time_utc"] == delivery_start
    ]
    tape_5min = product_trades.groupby("execution_5min", as_index=False).agg(
        median_price_eur_mwh=("price_eur_mwh", "median"),
        traded_volume_mwh=("volume_mwh", "sum"),
    )
    delivery_market = market[
        (market["time"] >= delivery_time)
        & (market["time"] < delivery_end)
    ]
    da_price = delivery_market["price_da_eur_mwh"].mean()

    volume_ax = ax.twinx()
    volume_ax.bar(
        tape_5min["execution_5min"],
        tape_5min["traded_volume_mwh"],
        width=pd.Timedelta(minutes=4),
        color="tab:gray",
        alpha=0.18,
        label="5-minute traded volume",
    )
    volume_ax.set_ylabel("Volume, MWh", color="tab:gray")
    volume_ax.tick_params(axis="y", labelcolor="tab:gray")

    ax.plot(
        tape_5min["execution_5min"],
        tape_5min["median_price_eur_mwh"],
        color="tab:blue",
        linewidth=1.6,
        label="5-minute median ID price",
    )
    ax.axhline(
        da_price,
        color="black",
        linestyle=":",
        linewidth=1.5,
        label=f"Mean DA price: {da_price:.2f} EUR/MWh",
    )
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        linewidth=1.5,
        label="NESO disclosure, 03:18 UTC",
    )
    ax.axvline(
        decision_time,
        color="tab:green",
        linestyle="--",
        linewidth=1.5,
        label="Decision time and data cutoff, 08:00 UTC",
    )
    ax.set_title(
        f"Hourly product: {delivery_start[:5]}–{delivery_end:%H:%M} UTC"
    )
    ax.set_ylabel("Price, EUR/MWh")
    ax.grid(alpha=0.3)
    ax.set_xlim(pd.to_datetime("00:00:00", format="%H:%M:%S"), decision_time + pd.Timedelta(minutes=5))

    price_handles, price_labels = ax.get_legend_handles_labels()
    volume_handles, volume_labels = volume_ax.get_legend_handles_labels()
    ax.legend(
        price_handles + volume_handles,
        price_labels + volume_labels,
        loc="upper left",
        fontsize=8,
    )

axes[-1].set_xlabel("Trade execution time, UTC")
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Ex-ante intraday price and liquidity snapshot at 08:00 UTC",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
decision_output = output_dir / "intraday_decision_snapshot_0800_09_12.png"
fig.savefig(decision_output, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {known_shock_output}")
print(f"Saved to: {decision_output}")
