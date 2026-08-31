from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
balance_path = project_root / "data/processed/balance_delta_total.csv"
capacity_path = project_root / "data/processed/capacities_total.csv"
output_path = project_root / "outputs/figures/long_confirmation_at_1205.png"

market = pd.read_csv(market_path)
balance = pd.read_csv(balance_path)
capacity = pd.read_csv(capacity_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
balance["time"] = pd.to_datetime(balance["time_utc"], format="%H:%M:%S")
capacity["time"] = pd.to_datetime(capacity["time_utc"], format="%H:%M:%S")

publication_time = pd.to_datetime("12:04:00", format="%H:%M:%S")
decision_time = pd.to_datetime("12:05:00", format="%H:%M:%S")
observed_plot_end = pd.to_datetime("19:00:00", format="%H:%M:%S")
day_start = pd.to_datetime("00:00:00", format="%H:%M:%S")
forward_end = pd.to_datetime("19:00:00", format="%H:%M:%S")

# A row stamped at interval start is usable only after its 15-minute
# observation interval is complete.
known_market = market[
    (market["time"] >= day_start)
    & (market["time"] + pd.Timedelta(minutes=15) <= decision_time)
].copy()
known_market["residual_load_error_mw"] = (
    known_market["residual_load_actual_mw"]
    - known_market["residual_load_da_mw"]
)
later_market = market[
    (market["time"] + pd.Timedelta(minutes=15) > decision_time)
    & (market["time"] + pd.Timedelta(minutes=15) <= observed_plot_end)
].copy()
later_market["residual_load_error_mw"] = (
    later_market["residual_load_actual_mw"]
    - later_market["residual_load_da_mw"]
)

known_balance = balance[
    (balance["time"] >= day_start)
    & (balance["time"] < decision_time)
].copy()
# Use only complete 15-minute bins for the mean series.
complete_balance = known_balance[
    known_balance["time"] < pd.to_datetime("12:00:00", format="%H:%M:%S")
]
balance_15min = (
    complete_balance.set_index("time")
    .resample("15min")["power_net_total_mw"]
    .mean()
    .reset_index()
)
latest_balance = known_balance.iloc[-1]
later_balance = balance[
    (balance["time"] >= decision_time)
    & (balance["time"] < observed_plot_end)
].copy()
later_balance_15min = (
    later_balance.set_index("time")
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
    label="Completed 15-minute residual-load error",
)
axes[0].scatter(
    known_market.iloc[-1]["time"],
    known_market.iloc[-1]["residual_load_error_mw"],
    color="tab:red",
    s=65,
    zorder=5,
    label=(
        "Latest completed interval: "
        f"{known_market.iloc[-1]['residual_load_error_mw']:.0f} MW"
    ),
)
axes[0].plot(
    later_market["time"],
    later_market["residual_load_error_mw"],
    color="tab:gray",
    marker="o",
    alpha=0.65,
    label="Later observations (ex post; not used for entry)",
)
axes[0].axvline(
    publication_time,
    color="tab:red",
    linestyle=":",
    linewidth=1.3,
    label="NESO disclosure, 12:04 UTC",
)
axes[0].axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    label="Decision time, 12:05 UTC",
)
axes[0].set_title("Large positive residual-load error already observed")
axes[0].set_ylabel("Error, MW")
axes[0].set_xlim(day_start, observed_plot_end)
axes[0].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

axes[1].axhline(0, color="black", linewidth=1)
axes[1].plot(
    balance_15min["time"],
    balance_15min["power_net_total_mw"],
    color="tab:purple",
    marker="o",
    label="Complete 15-minute mean net balancing contribution",
)
axes[1].scatter(
    latest_balance["time"],
    latest_balance["power_net_total_mw"],
    color="tab:purple",
    s=65,
    zorder=5,
    label=(
        f"Latest minute ({latest_balance['time']:%H:%M}): "
        f"{latest_balance['power_net_total_mw']:.0f} MW"
    ),
)
axes[1].plot(
    later_balance_15min["time"],
    later_balance_15min["power_net_total_mw"],
    color="tab:gray",
    marker="o",
    alpha=0.65,
    label="Later 15-minute means (ex post; not used for entry)",
)
axes[1].axvline(
    publication_time,
    color="tab:red",
    linestyle=":",
    linewidth=1.3,
    label="NESO disclosure, 12:04 UTC",
)
axes[1].axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    label="Decision time, 12:05 UTC",
)
axes[1].set_title("Indicative Balance Delta was already upward")
axes[1].set_ylabel("Power, MW")
axes[1].set_xlim(day_start, observed_plot_end)
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
    label="Decision time, 12:05 UTC",
)
axes[2].axvspan(
    pd.to_datetime("16:00:00", format="%H:%M:%S"),
    pd.to_datetime("19:00:00", format="%H:%M:%S"),
    color="tab:orange",
    alpha=0.12,
    label="Candidate delivery products",
)
axes[2].set_title(
    "Reported inbound ATC assumed known at 12:05: import headroom is a risk"
)
axes[2].set_ylabel("ATC, MW")
axes[2].set_xlabel("Observation / delivery time, UTC")
axes[2].set_xlim(day_start, forward_end)
axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

for ax in axes:
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

fig.suptitle(
    "Development of long-position factors and identifiable point at 12:05 UTC\n"
    "colour before cutoff; grey observations after cutoff are ex post",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(
    "Latest completed residual-load error:",
    f"{known_market.iloc[-1]['residual_load_error_mw']:.0f} MW",
    f"(interval starting {known_market.iloc[-1]['time']:%H:%M})",
)
print(
    "Latest one-minute indicative Balance Delta:",
    f"{latest_balance['power_net_total_mw']:.1f} MW",
    f"at {latest_balance['time']:%H:%M} UTC",
)
print(f"Saved to: {output_path}")
