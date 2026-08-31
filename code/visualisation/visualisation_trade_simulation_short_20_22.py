from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
figure_path = project_root / "outputs/figures/trade_simulation_short_20_22.png"
summary_path = project_root / "data/processed/trade_simulation_short_20_22.csv"

capital_eur = 10_000
risk_fraction = 0.01
total_risk_budget_eur = capital_eur * risk_fraction
risk_per_leg_eur = total_risk_budget_eur / 2
decision_seconds = 17 * 3600 + 40 * 60
entry_end_seconds = decision_seconds + 5 * 60
chart_end_seconds = 21 * 3600

settings = {
    "20:00:00": {
        "stop_eur_mwh": 200.0,
        "time_exit_seconds": 19 * 3600 + 50 * 60,
    },
    "21:00:00": {
        "stop_eur_mwh": 175.0,
        "time_exit_seconds": 20 * 3600 + 50 * 60,
    },
}

trades = pd.read_csv(trades_path)
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"].isin(settings))
].drop_duplicates("trade_id").copy()
trades["execution_seconds"] = pd.to_timedelta(
    trades["execution_time_utc"]
).dt.total_seconds()
trades = trades.sort_values(["delivery_start_time_utc", "execution_seconds"])
trades["execution_5min_seconds"] = (
    trades["execution_seconds"] // 300 * 300
).astype(int)

summaries = []
plot_data = {}
for product, params in settings.items():
    product_trades = trades[
        trades["delivery_start_time_utc"] == product
    ].copy()

    pre_stress = product_trades[
        product_trades["execution_seconds"] < 10 * 3600
    ]
    pre_stress_median = pre_stress["price_eur_mwh"].median()
    target_price = round(pre_stress_median / 5) * 5

    entry_trades = product_trades[
        (product_trades["execution_seconds"] >= decision_seconds)
        & (product_trades["execution_seconds"] < entry_end_seconds)
    ]
    entry_price = entry_trades["price_eur_mwh"].median()
    stop_price = params["stop_eur_mwh"]
    risk_per_mwh = stop_price - entry_price
    position_mwh = round(risk_per_leg_eur / risk_per_mwh, 3)

    eligible = product_trades[
        (product_trades["execution_seconds"] >= entry_end_seconds)
        & (
            product_trades["execution_seconds"]
            < params["time_exit_seconds"]
        )
    ]
    target_trades = eligible[eligible["price_eur_mwh"] <= target_price]
    stop_trades = eligible[eligible["price_eur_mwh"] >= stop_price]
    target_time = (
        float(target_trades.iloc[0]["execution_seconds"])
        if not target_trades.empty
        else float("inf")
    )
    stop_time = (
        float(stop_trades.iloc[0]["execution_seconds"])
        if not stop_trades.empty
        else float("inf")
    )

    if target_time < stop_time:
        exit_trigger = "pre-stress target"
        exit_price = float(target_price)
        first_trigger_time = target_trades.iloc[0]["execution_time_utc"]
        target_fill_trades = target_trades[
            target_trades["execution_seconds"] >= target_time
        ].copy()
        target_fill_trades["cumulative_volume_mwh"] = (
            target_fill_trades["volume_mwh"].cumsum()
        )
        completion = target_fill_trades[
            target_fill_trades["cumulative_volume_mwh"] >= position_mwh
        ].iloc[0]
        exit_time_seconds = float(completion["execution_seconds"])
        fill_volume_proxy = float(completion["cumulative_volume_mwh"])
        first_trigger_price = float(target_trades.iloc[0]["price_eur_mwh"])
    elif stop_time < float("inf"):
        exit_trigger = "stop"
        first_stop_trade = stop_trades.iloc[0]
        first_trigger_time = first_stop_trade["execution_time_utc"]
        first_trigger_price = float(first_stop_trade["price_eur_mwh"])
        # The tape shows only 0.1 MWh at the first breach and does not
        # reveal the order book. Use the first observed breach price as a
        # conservative full-position proxy rather than waiting for later,
        # more favourable prints.
        exit_price = first_trigger_price
        exit_time_seconds = float(first_stop_trade["execution_seconds"])
        fill_volume_proxy = float(first_stop_trade["volume_mwh"])
    else:
        exit_trigger = "time exit"
        time_exit_trades = product_trades[
            (product_trades["execution_seconds"] >= params["time_exit_seconds"])
            & (
                product_trades["execution_seconds"]
                < params["time_exit_seconds"] + 300
            )
        ]
        exit_price = float(time_exit_trades["price_eur_mwh"].median())
        exit_time_seconds = float(params["time_exit_seconds"])
        fill_volume_proxy = float(time_exit_trades["volume_mwh"].sum())
        first_trigger_price = exit_price
        first_trigger_time = pd.Timestamp("1900-01-01") + pd.to_timedelta(
            exit_time_seconds,
            unit="s",
        )
        first_trigger_time = first_trigger_time.strftime("%H:%M:%S")

    profit_eur = (entry_price - exit_price) * position_mwh
    risk_multiple = profit_eur / risk_per_leg_eur
    exit_time = pd.Timestamp("1900-01-01") + pd.to_timedelta(
        exit_time_seconds,
        unit="s",
    )

    price_path = product_trades[
        (product_trades["execution_seconds"] >= decision_seconds)
        & (product_trades["execution_seconds"] < chart_end_seconds)
    ].groupby("execution_5min_seconds", as_index=False).agg(
        median_price_eur_mwh=("price_eur_mwh", "median"),
        traded_volume_mwh=("volume_mwh", "sum"),
    )
    price_path["time"] = pd.Timestamp("1900-01-01") + pd.to_timedelta(
        price_path["execution_5min_seconds"],
        unit="s",
    )
    plot_data[product] = {
        "path": price_path,
        "entry": entry_price,
        "stop": stop_price,
        "target": target_price,
        "exit_time": exit_time,
        "exit_price": exit_price,
        "trigger": exit_trigger,
    }

    summaries.append(
        {
            "product_utc": (
                f"{product[:5]}-"
                f"{(pd.to_datetime(product) + pd.Timedelta(hours=1)):%H:%M}"
            ),
            "decision_time_utc": "17:40:00",
            "entry_window_utc": "17:40-17:45",
            "entry_eur_mwh": entry_price,
            "entry_window_low_eur_mwh": entry_trades["price_eur_mwh"].min(),
            "entry_window_high_eur_mwh": entry_trades["price_eur_mwh"].max(),
            "entry_window_volume_mwh": entry_trades["volume_mwh"].sum(),
            "entry_window_unique_trades": entry_trades["trade_id"].nunique(),
            "stop_eur_mwh": stop_price,
            "risk_budget_eur": risk_per_leg_eur,
            "position_mwh": position_mwh,
            "pre_stress_median_eur_mwh": pre_stress_median,
            "target_eur_mwh": target_price,
            "time_exit_utc": str(
                pd.to_timedelta(params["time_exit_seconds"], unit="s")
            )[7:15],
            "selected_exit_trigger": exit_trigger,
            "first_trigger_time_utc": first_trigger_time,
            "first_trigger_price_eur_mwh": first_trigger_price,
            "exit_time_utc": exit_time.strftime("%H:%M:%S.%f")[:-3],
            "simulated_exit_eur_mwh": exit_price,
            "recorded_fill_volume_proxy_mwh": fill_volume_proxy,
            "profit_eur": profit_eur,
            "risk_multiple": risk_multiple,
        }
    )

summary = pd.DataFrame(summaries)
summary.to_csv(summary_path, index=False)

fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
for ax, product in zip(axes, settings):
    data = plot_data[product]
    path = data["path"]
    before_exit = path["time"] <= data["exit_time"].floor("5min")
    ax.plot(
        path.loc[before_exit, "time"],
        path.loc[before_exit, "median_price_eur_mwh"],
        color="tab:blue",
        marker="o",
        markersize=3,
        linewidth=1.6,
        label="Position open: 5-minute median ID price",
    )
    ax.plot(
        path.loc[~before_exit, "time"],
        path.loc[~before_exit, "median_price_eur_mwh"],
        color="tab:gray",
        linewidth=1.4,
        alpha=0.65,
        label="Later price path after exit (ex post)",
    )
    ax.axhline(
        data["entry"],
        color="tab:blue",
        linestyle="--",
        label=f"Entry: {data['entry']:.2f} EUR/MWh",
    )
    ax.axhline(
        data["stop"],
        color="tab:red",
        linestyle="--",
        label=f"Stop: {data['stop']:.2f} EUR/MWh",
    )
    ax.axhline(
        data["target"],
        color="tab:green",
        linestyle="--",
        label=f"Pre-stress target: {data['target']:.2f} EUR/MWh",
    )
    ax.axvline(
        data["exit_time"],
        color="tab:green" if data["trigger"] != "stop" else "tab:red",
        linestyle=":",
        linewidth=1.5,
        label=(
            f"Exit ({data['trigger']}): "
            f"{data['exit_time']:%H:%M:%S} UTC"
        ),
    )
    ax.scatter(
        data["exit_time"],
        data["exit_price"],
        color="tab:green" if data["trigger"] != "stop" else "tab:red",
        s=65,
        zorder=5,
    )
    delivery_time = pd.to_datetime(product, format="%H:%M:%S")
    ax.set_title(
        f"Short hourly product: {product[:5]}–"
        f"{delivery_time + pd.Timedelta(hours=1):%H:%M} UTC"
    )
    ax.set_ylabel("Price, EUR/MWh")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

axes[-1].set_xlabel("Trade execution time, UTC")
axes[-1].set_xlim(
    pd.Timestamp("1900-01-01 17:40:00"),
    pd.Timestamp("1900-01-01 21:00:00"),
)
axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=20))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Simulated split short after the failed 17:28 bullish reaction\n"
    "later prices are grey and are not included after each leg exits",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
figure_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(summary.round(4).to_string(index=False))
print("Total simulated P&L:", round(summary["profit_eur"].sum(), 2), "EUR")
print(f"Saved to: {summary_path}")
print(f"Saved to: {figure_path}")
