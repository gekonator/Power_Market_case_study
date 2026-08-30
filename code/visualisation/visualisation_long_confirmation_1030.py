from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
balance_path = project_root / "data/processed/balance_delta_total.csv"
capacity_path = project_root / "data/processed/capacities_total.csv"
trades_path = project_root / "data/raw/trades.csv"
output_dir = project_root / "outputs/figures"

market = pd.read_csv(market_path)
balance = pd.read_csv(balance_path)
capacity = pd.read_csv(capacity_path)
trades = pd.read_csv(trades_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
balance["time"] = pd.to_datetime(balance["time_utc"], format="%H:%M:%S")
capacity["time"] = pd.to_datetime(capacity["time_utc"], format="%H:%M:%S")
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)

decision_time = pd.to_datetime("10:30:00", format="%H:%M:%S")
publication_time = pd.to_datetime("09:46:42", format="%H:%M:%S")
day_start = pd.to_datetime("00:00:00", format="%H:%M:%S")
forward_end = pd.to_datetime("14:00:00", format="%H:%M:%S")
products = ["12:00:00", "13:00:00", "14:00:00"]

output_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: physical and capacity confirmation available at 10:30.
known_market = market[
    (market["time"] >= day_start)
    & (market["time"] < decision_time)
].copy()
known_market["residual_load_error_mw"] = (
    known_market["residual_load_actual_mw"]
    - known_market["residual_load_da_mw"]
)
known_balance = balance[
    (balance["time"] >= day_start)
    & (balance["time"] < decision_time)
].copy()
balance_15min = (
    known_balance.set_index("time")
    .resample("15min")["power_net_total_mw"]
    .mean()
    .reset_index()
)
future_capacity = capacity[
    (capacity["time"] >= day_start)
    & (capacity["time"] <= forward_end)
].copy()

fig, axes = plt.subplots(3, 1, figsize=(12, 11))

axes[0].axhline(0, color="black", linewidth=1)
axes[0].plot(
    known_market["time"],
    known_market["residual_load_error_mw"],
    color="tab:red",
    marker="o",
    label="Residual-load error available by 10:30",
)
axes[0].axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    label="Decision time, 10:30 UTC",
)
axes[0].axvline(
    publication_time,
    color="tab:red",
    linestyle=":",
    linewidth=1.3,
    label="NESO disclosure, 09:46 UTC",
)
axes[0].set_title("Residual-load error turns positive")
axes[0].set_ylabel("Error, MW")
axes[0].set_xlim(day_start, decision_time)
axes[0].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

axes[1].axhline(0, color="black", linewidth=1)
axes[1].plot(
    balance_15min["time"],
    balance_15min["power_net_total_mw"],
    color="tab:purple",
    marker="o",
    label="15-minute mean net balancing contribution",
)
axes[1].axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    label="Decision time, 10:30 UTC",
)
axes[1].axvline(
    publication_time,
    color="tab:red",
    linestyle=":",
    linewidth=1.3,
    label="NESO disclosure, 09:46 UTC",
)
axes[1].set_title("Indicative Balance Delta turns upward")
axes[1].set_ylabel("Power, MW")
axes[1].set_xlim(day_start, decision_time)
axes[1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

axes[2].step(
    future_capacity["time"],
    future_capacity["capacity_to_nl_total"],
    where="post",
    color="tab:blue",
    label="Available transfer capacity into NL",
)
axes[2].axhline(0, color="black", linewidth=1)
axes[2].axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    label="Decision time, 10:30 UTC",
)
axes[2].axvspan(
    pd.to_datetime("12:00:00", format="%H:%M:%S"),
    pd.to_datetime("14:00:00", format="%H:%M:%S"),
    color="tab:orange",
    alpha=0.12,
    label="Candidate delivery products",
)
axes[2].set_title("Reported inbound ATC assumed known at 10:30")
axes[2].set_ylabel("ATC, MW")
axes[2].set_xlabel("Observation / delivery time, UTC")
axes[2].set_xlim(day_start, forward_end)
axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

for ax in axes:
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

fig.suptitle(
    "Long-position confirmation available at 10:30 UTC\n"
    "under zero-lag and future-ATC availability assumptions",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
confirmation_output = output_dir / "long_confirmation_at_1030.png"
fig.savefig(confirmation_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 2: executable intraday price and liquidity available at 10:30.
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(products))
    & (trades["execution_time"] < decision_time)
].drop_duplicates("trade_id").copy()
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")

fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
for ax, delivery_start in zip(axes, products):
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
        label=f"Mean DA price: {da_price:.2f} EUR/MWh",
    )
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        label="NESO disclosure, 09:46 UTC",
    )
    ax.axvline(
        decision_time,
        color="tab:green",
        linestyle="--",
        label="Decision time and cutoff, 10:30 UTC",
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
axes[-1].set_xlim(
    pd.to_datetime("08:00:00", format="%H:%M:%S"),
    decision_time + pd.Timedelta(minutes=5),
)
axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Ex-ante intraday price and liquidity snapshot at 10:30 UTC",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
price_output = output_dir / "intraday_decision_snapshot_1030_12_15.png"
fig.savefig(price_output, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {confirmation_output}")
print(f"Saved to: {price_output}")
