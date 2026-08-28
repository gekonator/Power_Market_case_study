from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
balance_path = project_root / "data/processed/balance_delta_total.csv"
output_path = project_root / "outputs/figures/residual_prices_and_balancing.png"

market = pd.read_csv(market_path)
balance = pd.read_csv(balance_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
market["residual_load_error_mw"] = (
    market["residual_load_actual_mw"] - market["residual_load_da_mw"]
)

# The source labels balance time as CET. Assume CET = UTC + 1 hour.
balance["time"] = (
    pd.to_datetime(balance["time_cet"], format="%H:%M:%S")
    - pd.Timedelta(hours=1)
)
balance_15m = (
    balance.set_index("time")["power_net_total_mw"]
    .resample("15min")
    .mean()
    .reset_index()
)

fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

axes[0].axhline(0, color="black", linewidth=1)
axes[0].plot(
    market["time"],
    market["residual_load_error_mw"],
    label="Residual load error",
    color="tab:red",
)
axes[0].set_title("Residual load error")
axes[0].set_ylabel("Actual minus DA, MW")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(
    market["time"],
    market["price_da_eur_mwh"],
    label="Day-ahead price",
    color="black",
)
axes[1].plot(
    market["time"],
    market["price_imbalance_long_eur_mwh"],
    label="Long imbalance price",
)
axes[1].plot(
    market["time"],
    market["price_imbalance_short_eur_mwh"],
    label="Short imbalance price",
    linestyle="--",
)
axes[1].set_title("NL day-ahead and imbalance prices")
axes[1].set_ylabel("Price, EUR/MWh")
axes[1].legend()
axes[1].grid(alpha=0.3)

axes[2].axhline(0, color="black", linewidth=1)
axes[2].plot(
    balance_15m["time"],
    balance_15m["power_net_total_mw"],
    label="Net total balancing response",
    color="tab:purple",
)
axes[2].set_title("Net total balancing response, 15-minute average")
axes[2].set_xlabel("Time, UTC (balance data converted assuming CET = UTC + 1)")
axes[2].set_ylabel("Net balancing power, MW")
axes[2].legend()
axes[2].grid(alpha=0.3)
axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
