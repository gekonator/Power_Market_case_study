from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_market_15m.csv"
output_path = project_root / "outputs/figures/demand_vs_wind_solar.png"

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")
data["renewables_da_mw"] = data["solar_da_mw"] + data["wind_da_mw"]
data["renewables_actual_mw"] = (
    data["solar_actual_mw"] + data["wind_actual_total_mw"]
)

fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

axes[0].plot(data["time"], data["demand_actual_mw"], label="Actual demand")
axes[0].plot(
    data["time"],
    data["renewables_actual_mw"],
    label="Actual wind + solar",
)
axes[0].set_title("Actual demand vs observed wind and solar generation")
axes[0].set_ylabel("Power, MW")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(data["time"], data["demand_da_mw"], label="DA demand forecast")
axes[1].plot(
    data["time"],
    data["renewables_da_mw"],
    label="DA wind + solar forecast",
)
axes[1].set_title("Day-ahead demand vs wind and solar forecast")
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
