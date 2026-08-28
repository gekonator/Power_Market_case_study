from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
capacity_path = project_root / "data/processed/capacities_total.csv"
output_path = project_root / "outputs/figures/residual_prices_and_import_capacity.png"

market = pd.read_csv(market_path)
capacity = pd.read_csv(capacity_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
capacity["time"] = pd.to_datetime(capacity["time_utc"], format="%H:%M:%S")
market["residual_load_error_mw"] = (
    market["residual_load_actual_mw"] - market["residual_load_da_mw"]
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

axes[2].step(
    capacity["time"],
    capacity["capacity_to_nl_total"],
    where="post",
    label="Available transfer capacity into NL",
    color="tab:green",
)
axes[2].step(
    capacity["time"],
    capacity["capacity_from_nl_total"],
    where="post",
    label="Available transfer capacity out of NL",
    color="tab:purple",
)
axes[2].axhline(0, color="black", linewidth=1)
axes[2].set_title("Total available transfer capacity into and out of NL")
axes[2].set_xlabel("Time, UTC")
axes[2].set_ylabel("Capacity, MW (exports negative)")
axes[2].legend()
axes[2].grid(alpha=0.3)
axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
