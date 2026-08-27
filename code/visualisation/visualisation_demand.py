from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_market_15m.csv"
output_path = project_root / "outputs/figures/demand_da_vs_actual.png"

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    data["time"],
    data["demand_da_mw"],
    label="Day-ahead forecast",
)
ax.plot(
    data["time"],
    data["demand_actual_mw"],
    label="Actual",
)

ax.set_title("NL demand: day-ahead forecast vs actual")
ax.set_xlabel("Time, UTC")
ax.set_ylabel("Power, MW")
ax.legend()
ax.grid(alpha=0.3)

ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
