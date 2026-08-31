from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
balance_path = project_root / "data/raw/balance_delta.csv"
figure_path = project_root / "outputs/figures/trade_simulation_13_14.png"
summary_path = project_root / "data/processed/trade_simulation_13_14.csv"

product_start = "13:00:00"
decision_seconds = 10.5 * 60 * 60
delivery_seconds = 13 * 60 * 60
entry_window_end = decision_seconds + 5 * 60
time_exit_seconds = 12 * 60 * 60 + 50 * 60
stop_price = 230.00
hypothetical_trading_capital_eur = 10_000
risk_fraction_of_capital = 0.01

trades = pd.read_csv(trades_path)
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
    & (trades["delivery_start_time_utc"] == product_start)
].drop_duplicates("trade_id").copy()
trades["execution_seconds"] = pd.to_timedelta(
    trades["execution_time_utc"]
).dt.total_seconds()
trades = trades[
    (trades["execution_seconds"] >= decision_seconds)
    & (trades["execution_seconds"] < delivery_seconds)
].sort_values("execution_seconds")
trades["execution_5min_seconds"] = (
    trades["execution_seconds"] // 300 * 300
).astype(int)

price_path = trades.groupby("execution_5min_seconds", as_index=False).agg(
    median_price_eur_mwh=("price_eur_mwh", "median"),
    traded_volume_mwh=("volume_mwh", "sum"),
    unique_trades=("trade_id", "nunique"),
    low_price_eur_mwh=("price_eur_mwh", "min"),
    high_price_eur_mwh=("price_eur_mwh", "max"),
)
price_path["time"] = pd.Timestamp("1900-01-01") + pd.to_timedelta(
    price_path["execution_5min_seconds"], unit="s"
)

entry_trades = trades[
    trades["execution_seconds"] < entry_window_end
]
entry_price = entry_trades["price_eur_mwh"].median()
risk_per_mwh = entry_price - stop_price
risk_budget_eur = (
    hypothetical_trading_capital_eur
    * risk_fraction_of_capital
)
position_mwh = round(risk_budget_eur / risk_per_mwh, 3)
take_profit = entry_price + 5 * risk_budget_eur / position_mwh

trades_through_target = trades[
    trades["price_eur_mwh"] >= take_profit
].copy()
if trades_through_target.empty:
    raise ValueError("The simulated take-profit was not reached")
first_target_trade = trades_through_target.iloc[0]
trades_through_target["cumulative_volume_mwh"] = (
    trades_through_target["volume_mwh"].cumsum()
)
full_target_fill = trades_through_target[
    trades_through_target["cumulative_volume_mwh"] >= position_mwh
].iloc[0]

balance = pd.read_csv(balance_path)
balance["source_seconds"] = pd.to_timedelta(
    balance["time_start_cet"]
).dt.total_seconds()
balance["time_utc_seconds"] = (balance["source_seconds"] - 3600) % 86400
balance["net_mfrrda_mw"] = (
    balance["power_in_mfrrda_mw"]
    - balance["power_out_mfrrda_mw"]
)
first_upward_mfrrda = balance[
    (balance["time_utc_seconds"] >= decision_seconds)
    & (balance["time_utc_seconds"] < delivery_seconds)
    & (balance["net_mfrrda_mw"] > 0)
].sort_values("time_utc_seconds").iloc[0]
mfrrda_seconds = float(first_upward_mfrrda["time_utc_seconds"])
mfrrda_time = pd.Timestamp("1900-01-01") + pd.to_timedelta(
    mfrrda_seconds, unit="s"
)

trigger_times = {
    "5R target": first_target_trade["execution_seconds"],
    "upward mFRRda": mfrrda_seconds,
    "time exit": time_exit_seconds,
}
selected_exit_trigger = min(
    trigger_times,
    key=lambda trigger: float(trigger_times[trigger]),
)
if selected_exit_trigger != "5R target":
    raise ValueError("The 5R target was expected to trigger first")

exit_seconds = full_target_fill["execution_seconds"]
exit_time = pd.Timestamp("1900-01-01") + pd.to_timedelta(
    exit_seconds, unit="s"
)

trades_before_exit = trades[trades["execution_seconds"] <= exit_seconds]
stop_touched_before_exit = (
    trades_before_exit["price_eur_mwh"] <= stop_price
).any()
if stop_touched_before_exit:
    raise ValueError("The stop was touched before the take-profit")

profit_per_mwh = take_profit - entry_price
position_profit_eur = position_mwh * profit_per_mwh
reward_to_risk = position_profit_eur / risk_budget_eur
return_as_fraction_of_capital = (
    position_profit_eur / hypothetical_trading_capital_eur
)

summary = pd.DataFrame(
    [
        {
            "product_utc": "13:00-14:00",
            "decision_time_utc": "10:30:00",
            "entry_window_utc": "10:30-10:35",
            "representative_entry_eur_mwh": entry_price,
            "stop_eur_mwh": stop_price,
            "risk_eur_per_mwh": risk_per_mwh,
            "take_profit_eur_mwh": take_profit,
            "first_trade_through_target_utc": first_target_trade[
                "execution_time_utc"
            ],
            "first_trade_through_target_eur_mwh": first_target_trade[
                "price_eur_mwh"
            ],
            "assumed_full_fill_complete_utc": full_target_fill[
                "execution_time_utc"
            ],
            "recorded_target_volume_at_full_fill_mwh": full_target_fill[
                "cumulative_volume_mwh"
            ],
            "first_upward_mfrrda_utc": mfrrda_time.strftime("%H:%M:%S"),
            "time_exit_utc": "12:50:00",
            "selected_exit_trigger": selected_exit_trigger,
            "stop_touched_before_target": stop_touched_before_exit,
            "profit_eur_per_mwh_at_target": profit_per_mwh,
            "reward_to_risk": reward_to_risk,
            "assumed_risk_fraction_of_capital": risk_fraction_of_capital,
            "hypothetical_trading_capital_eur": (
                hypothetical_trading_capital_eur
            ),
            "position_mwh": position_mwh,
            "position_mw_for_one_hour": position_mwh,
            "position_profit_eur_at_target": position_profit_eur,
            "return_fraction_of_capital_at_target": (
                return_as_fraction_of_capital
            ),
        }
    ]
)
summary.to_csv(summary_path, index=False)

before_exit = price_path["time"] <= exit_time.floor("5min")
after_exit = ~before_exit

fig, ax = plt.subplots(figsize=(13, 6.5))
ax.plot(
    price_path.loc[before_exit, "time"],
    price_path.loc[before_exit, "median_price_eur_mwh"],
    color="tab:blue",
    marker="o",
    linewidth=2,
    label="Position open: 5-minute median ID price",
)
ax.plot(
    price_path.loc[after_exit, "time"],
    price_path.loc[after_exit, "median_price_eur_mwh"],
    color="tab:gray",
    linewidth=1.5,
    alpha=0.65,
    label="Later price path after exit (ex post)",
)
ax.axhline(
    entry_price,
    color="tab:blue",
    linestyle="--",
    label=f"Representative entry: {entry_price:.2f} EUR/MWh",
)
ax.axhline(
    stop_price,
    color="tab:red",
    linestyle="--",
    label=f"Stop: {stop_price:.2f} EUR/MWh",
)
ax.axhline(
    take_profit,
    color="tab:green",
    linestyle="--",
    label=f"5R take-profit: {take_profit:.2f} EUR/MWh",
)
ax.axvline(
    exit_time,
    color="tab:green",
    linestyle=":",
    linewidth=1.5,
    label=(
        "Assumed full target fill: "
        f"{full_target_fill['execution_time_utc'][:8]} UTC"
    ),
)
ax.axvline(
    mfrrda_time,
    color="tab:purple",
    linestyle=":",
    linewidth=1.2,
    label=(
        "Fallback event exit: upward mFRRda, "
        f"{mfrrda_time:%H:%M} UTC"
    ),
)
ax.axvline(
    pd.Timestamp("1900-01-01 12:50:00"),
    color="black",
    linestyle=":",
    linewidth=1.2,
    label="Fallback time exit: 12:50 UTC",
)
ax.scatter(
    exit_time,
    take_profit,
    color="tab:green",
    s=70,
    zorder=5,
)

ax.set_title(
    "Simulated long position: hourly product 13:00–14:00 UTC\n"
    "Target and stop fixed at entry; later path shown only as ex-post context"
)
ax.set_xlabel("Trade execution time, UTC")
ax.set_ylabel("Price, EUR/MWh")
ax.set_xlim(
    pd.Timestamp("1900-01-01 10:30:00"),
    pd.Timestamp("1900-01-01 13:00:00"),
)
ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(alpha=0.3)
ax.legend(loc="upper left", fontsize=8)

fig.tight_layout()
figure_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(summary.round(4).to_string(index=False))
print(f"Saved to: {summary_path}")
print(f"Saved to: {figure_path}")
