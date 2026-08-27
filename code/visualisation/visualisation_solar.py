from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

nl_market_15m = pd.read_csv(
    "data/processed/nl_market_15m.csv"
)

nl_market_15m["time"] = pd.to_datetime(
    nl_market_15m["time_utc"],
    format="%H:%M:%S",
)

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    nl_market_15m["time"],
    nl_market_15m["solar_da_mw"],
    label="Day-ahead forecast",
)

ax.plot(
    nl_market_15m["time"],
    nl_market_15m["solar_actual_mw"],
    label="Actual",
)

ax.set_title("NL solar generation: day-ahead forecast vs actual")
ax.set_xlabel("Time, UTC")
ax.set_ylabel("Power, MW")

ax.legend()
ax.grid(alpha=0.3)

ax.xaxis.set_major_locator(
    mdates.HourLocator(interval=2)
)
ax.xaxis.set_major_formatter(
    mdates.DateFormatter("%H:%M")
)

fig.tight_layout()

output_directory = Path("outputs/figures")
output_directory.mkdir(
    parents=True,
    exist_ok=True,
)

fig.savefig(
    output_directory / "solar_da_vs_actual.png",
    dpi=150,
    bbox_inches="tight",
)

plt.close(fig)