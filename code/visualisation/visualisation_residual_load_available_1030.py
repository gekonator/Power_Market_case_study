from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_market_15m.csv"
output_path = (
    project_root
    / "outputs/figures/residual_load_available_at_1030.png"
)

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")
decision_time = pd.to_datetime("10:30:00", format="%H:%M:%S")

# The 10:15–10:30 interval is the latest completed interval at 10:30.
available_actual = data[data["time"] < decision_time].copy()

fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(
    data["time"],
    data["residual_load_da_mw"],
    color="tab:blue",
    linestyle="--",
    linewidth=1.8,
    label="DA forecast residual load — full delivery day",
)
ax.plot(
    available_actual["time"],
    available_actual["residual_load_actual_mw"],
    color="tab:orange",
    linewidth=2,
    label="Actual residual load available by 10:30",
)
ax.axvline(
    decision_time,
    color="tab:green",
    linestyle="--",
    linewidth=1.5,
    label="Decision time, 10:30 UTC",
)

ax.set_title(
    "Residual-load information available at 10:30 UTC\n"
    "under the zero-lag reporting assumption"
)
ax.set_xlabel("Delivery / observation time, UTC")
ax.set_ylabel("Residual load, MW")
ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(alpha=0.3)
ax.legend()

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
