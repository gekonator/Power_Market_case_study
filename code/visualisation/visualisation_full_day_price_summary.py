from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_path = project_root / "outputs/figures/full_day_price_summary.png"

market = pd.read_csv(market_path)
trades = pd.read_csv(trades_path)

market["delivery_time"] = pd.to_datetime(
    market["time_utc"],
    format="%H:%M:%S",
)

intraday = trades[
    (trades["product"] == "XBID_Quarter_Hour_Power")
    & (trades["trade_phase"] == "CONT")
].copy()
intraday = intraday.drop_duplicates(subset="trade_id")
intraday["execution_time"] = pd.to_datetime(
    intraday["execution_time_utc"],
    format="%H:%M:%S.%f",
)
intraday["execution_5min"] = intraday["execution_time"].dt.floor("5min")

intraday_5min = (
    intraday.groupby(
        ["delivery_start_time_utc", "execution_5min"],
        as_index=False,
    )["price_eur_mwh"]
    .median()
)
final_intraday = (
    intraday_5min.sort_values("execution_5min")
    .groupby("delivery_start_time_utc", as_index=False)
    .tail(1)
    .rename(columns={"price_eur_mwh": "final_intraday_price_eur_mwh"})
)
final_intraday["delivery_time"] = pd.to_datetime(
    final_intraday["delivery_start_time_utc"],
    format="%H:%M:%S",
)
final_intraday = final_intraday.sort_values("delivery_time")

fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)

axes[0].plot(
    market["delivery_time"],
    market["price_da_eur_mwh"],
    color="black",
    linewidth=1.7,
    label="Day-ahead price",
)
axes[0].set_title("Day-ahead prices")
axes[0].set_ylabel("EUR/MWh")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(
    final_intraday["delivery_time"],
    final_intraday["final_intraday_price_eur_mwh"],
    color="tab:blue",
    linewidth=1.7,
    marker="o",
    markersize=2.5,
    label="Final 5-minute median continuous ID price",
)
axes[1].set_title("Intraday prices by quarter-hour delivery product")
axes[1].set_ylabel("EUR/MWh")
axes[1].legend()
axes[1].grid(alpha=0.3)

axes[2].plot(
    market["delivery_time"],
    market["price_imbalance_long_eur_mwh"],
    color="tab:green",
    linewidth=1.7,
    label="Long imbalance price",
)
axes[2].plot(
    market["delivery_time"],
    market["price_imbalance_short_eur_mwh"],
    color="tab:red",
    linewidth=1.7,
    linestyle="--",
    label="Short imbalance price",
)
axes[2].set_title("Realised imbalance prices")
axes[2].set_xlabel("Delivery time, UTC")
axes[2].set_ylabel("EUR/MWh")
axes[2].legend()
axes[2].grid(alpha=0.3)
axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.suptitle("NL price formation across the delivery day", fontsize=15)
fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
print(
    "Intraday delivery periods represented: "
    f"{final_intraday['delivery_start_time_utc'].nunique()}/96"
)
