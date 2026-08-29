from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_market_15m.csv"
output_path = project_root / "outputs/figures/solar_and_wind_da_vs_actual.png"

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")

fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

axes[0].plot(
    data["time"],
    data["solar_da_mw"],
    label="Solar day-ahead forecast",
    color="tab:orange",
)
axes[0].plot(
    data["time"],
    data["solar_actual_mw"],
    label="Solar actual",
    color="tab:blue",
)
axes[0].set_title("NL solar generation: day-ahead forecast vs actual")
axes[0].set_ylabel("Power, MW")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(
    data["time"],
    data["wind_da_mw"],
    label="Wind day-ahead forecast",
    color="tab:orange",
)
axes[1].plot(
    data["time"],
    data["wind_actual_total_mw"],
    label="Wind actual",
    color="tab:blue",
)
axes[1].set_title("NL wind generation: day-ahead forecast vs actual")
axes[1].set_xlabel("Time, UTC")
axes[1].set_ylabel("Power, MW")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
