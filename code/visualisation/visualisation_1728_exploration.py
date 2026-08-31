from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
auctions_path = project_root / "data/raw/neso_auctions.csv"
flows_path = project_root / "data/processed/nl_flows_gb.csv"
trades_path = project_root / "data/raw/trades.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
balance_path = project_root / "data/processed/balance_delta_total.csv"
capacity_path = project_root / "data/processed/capacities_total.csv"
output_dir = project_root / "outputs/figures"

publication_clock = "17:28:08"
publication_time = pd.to_datetime(publication_clock, format="%H:%M:%S")
delivery_hours = ["20:00:00", "21:00:00"]
day_start = pd.to_datetime("00:00:00", format="%H:%M:%S")
chart_end = pd.to_datetime("22:00:00", format="%H:%M:%S")

auctions = pd.read_csv(auctions_path)
flows = pd.read_csv(flows_path)
trades = pd.read_csv(trades_path)
market = pd.read_csv(market_path)
balance = pd.read_csv(balance_path)
capacity = pd.read_csv(capacity_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
balance["time"] = pd.to_datetime(balance["time_utc"], format="%H:%M:%S")
capacity["time"] = pd.to_datetime(capacity["time_utc"], format="%H:%M:%S")
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)

output_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: disclosed BritNed Buy compared with DA scheduled imports.
neso_buy = (
    auctions[
        (auctions["published_time_utc"] == publication_clock)
        & (auctions["delivery_start_time_utc"].isin(delivery_hours))
    ]
    .groupby("delivery_start_time_utc", as_index=False)["bn_volume_mw"]
    .sum()
    .rename(columns={"bn_volume_mw": "neso_britned_buy_mw"})
)
comparison = flows[
    flows["time_utc"].isin(delivery_hours)
][["time_utc", "da_net_nl_exports_mw"]].merge(
    neso_buy,
    left_on="time_utc",
    right_on="delivery_start_time_utc",
    validate="one_to_one",
)
comparison["da_britned_import_into_nl_mw"] = (
    -comparison["da_net_nl_exports_mw"]
).clip(lower=0)
comparison["buy_pct_da_import"] = (
    100
    * comparison["neso_britned_buy_mw"]
    / comparison["da_britned_import_into_nl_mw"]
)
comparison = comparison.sort_values("time_utc")

start_times = pd.to_datetime(comparison["time_utc"], format="%H:%M:%S")
labels = [
    f"{start:%H:%M}–{start + pd.Timedelta(hours=1):%H:%M}"
    for start in start_times
]
x = np.arange(len(comparison))
width = 0.36
fig, ax = plt.subplots(figsize=(9, 6))
da_bars = ax.bar(
    x - width / 2,
    comparison["da_britned_import_into_nl_mw"],
    width,
    color="tab:blue",
    alpha=0.8,
    label="DA scheduled BritNed import into NL",
)
neso_bars = ax.bar(
    x + width / 2,
    comparison["neso_britned_buy_mw"],
    width,
    color="tab:red",
    alpha=0.8,
    label="NESO BritNed Buy for GB, published 17:28",
)
for bars in (da_bars, neso_bars):
    ax.bar_label(bars, fmt="%.0f MW", padding=3, fontsize=9)
for index, percent in enumerate(comparison["buy_pct_da_import"]):
    height = max(
        comparison.iloc[index]["da_britned_import_into_nl_mw"],
        comparison.iloc[index]["neso_britned_buy_mw"],
    )
    ax.text(
        index,
        height + 35,
        f"NESO Buy = {percent:.0f}% of DA import",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )
ax.set_title(
    "Known BritNed supply shock for selected hourly products\n"
    "NESO disclosure at 17:28:08 UTC"
)
ax.set_xlabel("Hourly delivery product, UTC")
ax.set_ylabel("Power, MW")
ax.set_xticks(x, labels)
ax.set_ylim(
    0,
    comparison[[
        "da_britned_import_into_nl_mw",
        "neso_britned_buy_mw",
    ]].to_numpy().max()
    * 1.35,
)
ax.grid(axis="y", alpha=0.3)
ax.legend(loc="upper left")
fig.tight_layout()
supply_output = output_dir / "neso_vs_da_britned_import_1728_20_22.png"
fig.savefig(supply_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 2: full-day intraday price and volume paths.
selected_trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(delivery_hours))
].drop_duplicates("trade_id").copy()
selected_trades["execution_5min"] = (
    selected_trades["execution_time"].dt.floor("5min")
)

fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
for ax, delivery_start in zip(axes, delivery_hours):
    delivery_time = pd.to_datetime(delivery_start, format="%H:%M:%S")
    delivery_end = delivery_time + pd.Timedelta(hours=1)
    product_trades = selected_trades[
        selected_trades["delivery_start_time_utc"] == delivery_start
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
        alpha=0.16,
        label="5-minute traded volume",
    )
    volume_ax.set_ylabel("Volume, MWh", color="tab:gray")
    volume_ax.tick_params(axis="y", labelcolor="tab:gray")

    before = tape_5min["execution_5min"] < publication_time
    ax.plot(
        tape_5min.loc[before, "execution_5min"],
        tape_5min.loc[before, "median_price_eur_mwh"],
        color="tab:blue",
        linewidth=1.6,
        label="Price known before disclosure",
    )
    ax.plot(
        tape_5min.loc[~before, "execution_5min"],
        tape_5min.loc[~before, "median_price_eur_mwh"],
        color="tab:gray",
        linewidth=1.5,
        alpha=0.75,
        label="Later price path (ex post)",
    )
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        linewidth=1.5,
        label="NESO disclosure, 17:28 UTC",
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
    "Full-day intraday paths for products in the 17:28 NESO disclosure",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
price_output = output_dir / "intraday_prices_1728_20_22_full_day.png"
fig.savefig(price_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 3: system context around the disclosure. Pre-disclosure data are
# coloured; later observations are grey and must not justify an entry.
market["residual_load_error_mw"] = (
    market["residual_load_actual_mw"] - market["residual_load_da_mw"]
)
balance_15min = (
    balance.set_index("time")
    .resample("15min")["power_net_total_mw"]
    .mean()
    .reset_index()
)
pre_market = market[market["time"] < publication_time]
post_market = market[
    (market["time"] >= publication_time) & (market["time"] < chart_end)
]
pre_balance = balance_15min[balance_15min["time"] < publication_time]
post_balance = balance_15min[
    (balance_15min["time"] >= publication_time)
    & (balance_15min["time"] < chart_end)
]
shown_capacity = capacity[
    (capacity["time"] >= day_start) & (capacity["time"] <= chart_end)
]

fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
axes[0].axhline(0, color="black", linewidth=1)
axes[0].plot(
    pre_market["time"],
    pre_market["residual_load_error_mw"],
    color="tab:red",
    marker="o",
    label="Residual-load error known before disclosure",
)
axes[0].plot(
    post_market["time"],
    post_market["residual_load_error_mw"],
    color="tab:gray",
    marker="o",
    alpha=0.65,
    label="Later observations (ex post)",
)
axes[0].set_title("Residual-load error")
axes[0].set_ylabel("Error, MW")

axes[1].axhline(0, color="black", linewidth=1)
axes[1].plot(
    pre_balance["time"],
    pre_balance["power_net_total_mw"],
    color="tab:purple",
    marker="o",
    label="Indicative Balance Delta known before disclosure",
)
axes[1].plot(
    post_balance["time"],
    post_balance["power_net_total_mw"],
    color="tab:gray",
    marker="o",
    alpha=0.65,
    label="Later 15-minute means (ex post)",
)
axes[1].set_title("Indicative net balancing contribution")
axes[1].set_ylabel("Power, MW")

axes[2].step(
    shown_capacity["time"],
    shown_capacity["capacity_to_nl_total"],
    where="post",
    color="tab:blue",
    label="Available transfer capacity into NL",
)
axes[2].axhline(0, color="black", linewidth=1)
axes[2].axvspan(
    pd.to_datetime("20:00:00", format="%H:%M:%S"),
    pd.to_datetime("22:00:00", format="%H:%M:%S"),
    color="tab:orange",
    alpha=0.12,
    label="Affected delivery products",
)
axes[2].set_title("Reported inbound ATC assumed known forward")
axes[2].set_ylabel("ATC, MW")
axes[2].set_xlabel("Observation / delivery time, UTC")

for ax in axes:
    ax.axvline(
        publication_time,
        color="tab:red",
        linestyle="--",
        linewidth=1.4,
        label="NESO disclosure, 17:28 UTC",
    )
    ax.set_xlim(day_start, chart_end)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
fig.suptitle(
    "System context around the 17:28 NESO disclosure\n"
    "grey observations after disclosure are ex post",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
context_output = output_dir / "system_context_1728_20_22.png"
fig.savefig(context_output, dpi=150, bbox_inches="tight")
plt.close(fig)

print(comparison[[
    "time_utc",
    "da_britned_import_into_nl_mw",
    "neso_britned_buy_mw",
    "buy_pct_da_import",
]].round(1).to_string(index=False))
print(f"Saved to: {supply_output}")
print(f"Saved to: {price_output}")
print(f"Saved to: {context_output}")
