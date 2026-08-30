from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
flows_total_path = project_root / "data/processed/nl_flows_total.csv"
capacities_path = project_root / "data/processed/capacities_total.csv"
balance_path = project_root / "data/processed/balance_delta_total.csv"
flows_gb_path = project_root / "data/processed/nl_flows_gb.csv"
output_dir = project_root / "outputs/figures"

market = pd.read_csv(market_path)
flows = pd.read_csv(flows_total_path)
capacities = pd.read_csv(capacities_path)
balance = pd.read_csv(balance_path)
flows_gb = pd.read_csv(flows_gb_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
flows["time"] = pd.to_datetime(flows["time_utc"], format="%H:%M:%S")
capacities["time"] = pd.to_datetime(capacities["time_utc"], format="%H:%M:%S")
balance["time"] = pd.to_datetime(balance["time_utc"], format="%H:%M:%S")
flows_gb["time"] = pd.to_datetime(flows_gb["time_utc"], format="%H:%M:%S")

decision_time = pd.to_datetime("08:00:00", format="%H:%M:%S")
forward_end = pd.to_datetime("12:00:00", format="%H:%M:%S")

# At 08:00, the 07:45–08:00 quarter is the latest completed interval.
historical_market = market[market["time"] < decision_time].copy()
historical_flows = flows[flows["time"] < decision_time].copy()
historical_capacities = capacities[capacities["time"] <= decision_time].copy()
historical_balance = balance[balance["time"] < decision_time].copy()

historical_market["residual_load_error_mw"] = (
    historical_market["residual_load_actual_mw"]
    - historical_market["residual_load_da_mw"]
)

output_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: realised fundamentals available by the decision cutoff.
fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

axes[0].plot(
    historical_market["time"],
    historical_market["solar_da_mw"],
    linestyle="--",
    label="Solar DA forecast",
)
axes[0].plot(
    historical_market["time"],
    historical_market["solar_actual_mw"],
    label="Solar actual",
)
axes[0].set_title("Solar generation")
axes[0].set_ylabel("Power, MW")

axes[1].plot(
    historical_market["time"],
    historical_market["wind_da_mw"],
    linestyle="--",
    label="Wind DA forecast",
)
axes[1].plot(
    historical_market["time"],
    historical_market["wind_actual_total_mw"],
    label="Wind actual",
)
axes[1].set_title("Wind generation")
axes[1].set_ylabel("Power, MW")

axes[2].plot(
    historical_market["time"],
    historical_market["demand_da_mw"],
    linestyle="--",
    label="Demand DA forecast",
)
axes[2].plot(
    historical_market["time"],
    historical_market["demand_actual_mw"],
    label="Demand actual",
)
axes[2].set_title("Demand")
axes[2].set_ylabel("Power, MW")

axes[3].axhline(0, color="black", linewidth=1)
axes[3].plot(
    historical_market["time"],
    historical_market["residual_load_error_mw"],
    color="tab:red",
    label="Residual-load error",
)
axes[3].set_title("Residual-load error available by 08:00")
axes[3].set_ylabel("Error, MW")
axes[3].set_xlabel("Observation time, UTC")

for ax in axes:
    ax.axvline(
        decision_time,
        color="tab:green",
        linestyle="--",
        linewidth=1.5,
        label="Decision time, 08:00 UTC",
    )
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(pd.to_datetime("00:00:00", format="%H:%M:%S"), decision_time)

axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Fundamentals available at 08:00 under the zero-lag assumption",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
fundamentals_output = output_dir / "decision_fundamentals_asof_0800.png"
fig.savefig(fundamentals_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 2: realised market and system context up to the decision cutoff.
balance_15min = (
    historical_balance.set_index("time")
    .resample("15min")["power_net_total_mw"]
    .mean()
    .reset_index()
)

fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

axes[0].plot(
    historical_market["time"],
    historical_market["price_da_eur_mwh"],
    color="black",
    linestyle=":",
    label="DA price",
)
axes[0].plot(
    historical_market["time"],
    historical_market["price_imbalance_long_eur_mwh"],
    label="Long imbalance price",
)
axes[0].plot(
    historical_market["time"],
    historical_market["price_imbalance_short_eur_mwh"],
    label="Short imbalance price",
)
axes[0].set_title("Prices for completed delivery intervals")
axes[0].set_ylabel("EUR/MWh")

axes[1].step(
    historical_flows["time"],
    historical_flows["da_net_nl_exports_mw"],
    where="post",
    linestyle="--",
    label="DA net NL exports",
)
axes[1].step(
    historical_flows["time"],
    historical_flows["fin_net_nl_exports_mw"],
    where="post",
    label="Finalised net NL exports",
)
axes[1].axhline(0, color="black", linewidth=1)
axes[1].set_title("Schedules for completed delivery hours")
axes[1].set_ylabel("Net exports, MW")

axes[2].step(
    historical_capacities["time"],
    historical_capacities["capacity_to_nl_total"],
    where="post",
    label="Available capacity into NL",
)
axes[2].step(
    historical_capacities["time"],
    historical_capacities["capacity_from_nl_total"],
    where="post",
    label="Available capacity out of NL",
)
axes[2].axhline(0, color="black", linewidth=1)
axes[2].set_title("Available transfer capacity observed by 08:00")
axes[2].set_ylabel("ATC, MW")

axes[3].axhline(0, color="black", linewidth=1)
axes[3].plot(
    balance_15min["time"],
    balance_15min["power_net_total_mw"],
    color="tab:purple",
    label="Indicative net balancing contribution",
)
axes[3].set_title("Balance Delta context")
axes[3].set_ylabel("Power, MW")
axes[3].set_xlabel("Observation time, UTC")

for ax in axes:
    ax.axvline(
        decision_time,
        color="tab:green",
        linestyle="--",
        linewidth=1.5,
        label="Decision time, 08:00 UTC",
    )
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(pd.to_datetime("00:00:00", format="%H:%M:%S"), decision_time)

axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Historical system context at 08:00 under the zero-lag assumption",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
system_output = output_dir / "decision_system_context_asof_0800.png"
fig.savefig(system_output, dpi=150, bbox_inches="tight")
plt.close(fig)

# Figure 3: future information assumed available at 08:00 for 09:00–12:00.
forward_market = market[
    (market["time"] >= pd.to_datetime("09:00:00", format="%H:%M:%S"))
    & (market["time"] < forward_end)
].copy()
forward_capacities = capacities[
    (capacities["time"] >= pd.to_datetime("09:00:00", format="%H:%M:%S"))
    & (capacities["time"] < forward_end)
].copy()
forward_gb = flows_gb[
    flows_gb["time_utc"].isin(["09:00:00", "10:00:00", "11:00:00"])
].copy()
forward_gb["da_britned_import_mw"] = (
    -forward_gb["da_net_nl_exports_mw"]
).clip(lower=0)

fig, axes = plt.subplots(3, 1, figsize=(12, 11))

axes[0].plot(
    forward_market["time"],
    forward_market["residual_load_da_mw"],
    color="tab:blue",
    marker="o",
    label="DA residual load",
)
axes[0].set_title("DA residual-load expectation")
axes[0].set_ylabel("Power, MW")
axes[0].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

axes[1].step(
    forward_capacities["time"],
    forward_capacities["capacity_to_nl_total"],
    where="post",
    label="Available capacity into NL",
)
axes[1].step(
    forward_capacities["time"],
    forward_capacities["capacity_from_nl_total"],
    where="post",
    label="Available capacity out of NL",
)
axes[1].axhline(0, color="black", linewidth=1)
axes[1].set_title("Future ATC assumed known at 08:00")
axes[1].set_ylabel("ATC, MW")
axes[1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

x = list(range(len(forward_gb)))
bar_width = 0.36
axes[2].bar(
    [position - bar_width / 2 for position in x],
    forward_gb["da_britned_import_mw"],
    width=bar_width,
    label="DA scheduled BritNed import into NL",
    color="tab:blue",
    alpha=0.8,
)
axes[2].bar(
    [position + bar_width / 2 for position in x],
    forward_gb["neso_buy_mw"],
    width=bar_width,
    label="NESO BritNed Buy published at 03:18",
    color="tab:red",
    alpha=0.8,
)
axes[2].set_title("Known loss of expected BritNed supply")
axes[2].set_ylabel("Power, MW")
axes[2].set_xlabel("Hourly delivery product, UTC")
axes[2].set_xticks(
    x,
    ["09:00–10:00", "10:00–11:00", "11:00–12:00"],
)

for ax in axes:
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

fig.suptitle(
    "Forward constraints for 09:00–12:00 available at the 08:00 decision time",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
forward_output = output_dir / "decision_forward_constraints_0800_09_12.png"
fig.savefig(forward_output, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {fundamentals_output}")
print(f"Saved to: {system_output}")
print(f"Saved to: {forward_output}")
