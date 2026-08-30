from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_dir = project_root / "outputs/figures"

publication_time = pd.to_datetime("03:18:41", format="%H:%M:%S")
product_groups = [
    (
        ["05:00:00", "06:00:00", "07:00:00", "08:00:00"],
        "intraday_prices_first_disclosure_05_09.png",
    ),
    (
        ["09:00:00", "10:00:00", "11:00:00"],
        "intraday_prices_first_disclosure_09_12.png",
    ),
]

trades = pd.read_csv(trades_path)
market = pd.read_csv(market_path)

all_delivery_starts = [
    delivery_start
    for delivery_starts, _ in product_groups
    for delivery_start in delivery_starts
]
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(all_delivery_starts))
].copy()
trades = trades.drop_duplicates(subset="trade_id")
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")

output_dir.mkdir(parents=True, exist_ok=True)

for delivery_starts, filename in product_groups:
    fig, axes = plt.subplots(
        len(delivery_starts),
        1,
        figsize=(12, 3.5 * len(delivery_starts)),
        sharex=True,
        squeeze=False,
    )
    axes = axes[:, 0]

    group_trades = trades[
        trades["delivery_start_time_utc"].isin(delivery_starts)
    ]
    x_min = group_trades["execution_time"].min().floor("h")
    final_delivery_start = pd.to_datetime(
        delivery_starts[-1],
        format="%H:%M:%S",
    )
    x_max = final_delivery_start + pd.Timedelta(hours=1)

    for ax, delivery_start in zip(axes, delivery_starts):
        delivery_time = pd.to_datetime(delivery_start, format="%H:%M:%S")
        delivery_end = delivery_time + pd.Timedelta(hours=1)

        product_trades = trades[
            trades["delivery_start_time_utc"] == delivery_start
        ]
        price_5min = (
            product_trades.groupby("execution_5min", as_index=False)[
                "price_eur_mwh"
            ]
            .median()
        )

        delivery_market = market[
            (market["time"] >= delivery_time)
            & (market["time"] < delivery_end)
        ]
        da_price = delivery_market["price_da_eur_mwh"].mean()
        short_imbalance_price = delivery_market[
            "price_imbalance_short_eur_mwh"
        ].mean()

        ax.plot(
            price_5min["execution_5min"],
            price_5min["price_eur_mwh"],
            color="tab:blue",
            linewidth=1.5,
            label="5-minute median intraday trade price",
        )
        ax.axvline(
            publication_time,
            color="tab:red",
            linestyle="--",
            linewidth=1.5,
            label="NESO disclosure, 03:18 UTC",
        )
        ax.axhline(
            da_price,
            color="black",
            linestyle=":",
            linewidth=1.5,
            label=f"Mean DA price: {da_price:.2f} EUR/MWh",
        )
        ax.hlines(
            short_imbalance_price,
            xmin=delivery_time,
            xmax=delivery_end,
            color="tab:orange",
            linestyle="-.",
            linewidth=1.5,
            label=(
                "Mean short imbalance price (ex post): "
                f"{short_imbalance_price:.2f} EUR/MWh"
            ),
        )
        ax.set_title(
            f"Hourly product: {delivery_start[:5]}–{delivery_end:%H:%M} UTC"
        )
        ax.set_ylabel("Price, EUR/MWh")
        ax.set_xlim(x_min, x_max)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper left", fontsize=8)

    axes[-1].set_xlabel("Trade execution time, UTC")
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    fig.suptitle(
        "Intraday prices for hourly products in the 03:18:41 NESO disclosure",
        fontsize=14,
        y=1.0,
    )
    fig.tight_layout()
    output_path = output_dir / filename
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved to: {output_path}")
