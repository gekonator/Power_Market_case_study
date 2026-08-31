from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
trades_path = project_root / "data/raw/trades.csv"
output_path = (
    project_root
    / "outputs/figures/intraday_decision_snapshot_1740_20_22.png"
)

products = ["20:00:00", "21:00:00"]
publication_time = pd.to_datetime("17:28:08", format="%H:%M:%S")
decision_time = pd.to_datetime("17:40:00", format="%H:%M:%S")
chart_start = pd.to_datetime("14:00:00", format="%H:%M:%S")
chart_end = pd.to_datetime("17:45:00", format="%H:%M:%S")

market = pd.read_csv(market_path)
trades = pd.read_csv(trades_path)
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)

# Decision snapshot: no execution at or after 17:40 is shown.
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(products))
    & (trades["execution_time"] < decision_time)
].drop_duplicates("trade_id").copy()
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
for ax, delivery_start in zip(axes, products):
    delivery_time = pd.to_datetime(delivery_start, format="%H:%M:%S")
    delivery_end = delivery_time + pd.Timedelta(hours=1)
    product_trades = trades[
        trades["delivery_start_time_utc"] == delivery_start
    ]
    tape_5min = product_trades.groupby(
        "execution_5min",
        as_index=False,
    ).agg(
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
        label=f"Mean DA price: {da_price:.2f} EUR/MWh",
    )
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        linewidth=1.5,
        label="NESO disclosure, 17:28 UTC",
    )
    ax.axvline(
        decision_time,
        color="tab:green",
        linestyle="--",
        linewidth=1.5,
        label="Failed-reaction decision cutoff, 17:40 UTC",
    )
    ax.set_title(
        f"Hourly product: {delivery_start[:5]}–{delivery_end:%H:%M} UTC"
    )
    ax.set_ylabel("Price, EUR/MWh")
    ax.grid(alpha=0.3)

    price_handles, price_labels = ax.get_legend_handles_labels()
    volume_handles, volume_labels = volume_ax.get_legend_handles_labels()
    ax.legend(
        price_handles + volume_handles,
        price_labels + volume_labels,
        loc="upper left",
        fontsize=8,
    )

axes[-1].set_xlabel("Trade execution time, UTC")
axes[-1].set_xlim(chart_start, chart_end)
axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Ex-ante failed-reaction snapshot at 17:40 UTC",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
