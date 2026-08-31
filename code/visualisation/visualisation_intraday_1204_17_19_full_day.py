from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_path = (
    project_root
    / "outputs/figures/intraday_prices_1204_17_19_full_day.png"
)

products = ["17:00:00", "18:00:00"]
publication_time = pd.to_datetime("12:04:00", format="%H:%M:%S")
day_start = pd.to_datetime("00:00:00", format="%H:%M:%S")
chart_end = pd.to_datetime("19:00:00", format="%H:%M:%S")

trades = pd.read_csv(trades_path)
market = pd.read_csv(market_path)

trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(products))
].drop_duplicates("trade_id").copy()
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")

fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

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
        unique_trades=("trade_id", "nunique"),
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
        alpha=0.16,
        label="5-minute traded volume",
    )
    volume_ax.set_ylabel("Volume, MWh", color="tab:gray")
    volume_ax.tick_params(axis="y", labelcolor="tab:gray")

    ax.plot(
        tape_5min["execution_5min"],
        tape_5min["median_price_eur_mwh"],
        color="tab:blue",
        linewidth=1.6,
        label="5-minute median intraday price",
    )
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        linewidth=1.5,
        label="NESO disclosure, 12:04 UTC",
    )
    ax.axhline(
        da_price,
        color="black",
        linestyle=":",
        linewidth=1.4,
        label=f"Mean DA price: {da_price:.2f} EUR/MWh",
    )
    ax.axvspan(
        delivery_time,
        delivery_end,
        color="tab:orange",
        alpha=0.10,
        label="Delivery period (ex post context)",
    )

    ax.set_title(
        f"Hourly product: {delivery_start[:5]}–{delivery_end:%H:%M} UTC"
    )
    ax.set_ylabel("Price, EUR/MWh")
    ax.set_xlim(day_start, chart_end)
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
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.suptitle(
    "Full-day intraday path for hourly products after the 12:04 NESO disclosure",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

for delivery_start in products:
    product_trades = trades[
        trades["delivery_start_time_utc"] == delivery_start
    ]
    print(
        delivery_start,
        "unique trades:",
        product_trades["trade_id"].nunique(),
        "volume MWh:",
        round(product_trades["volume_mwh"].sum(), 1),
    )
print(f"Saved to: {output_path}")
