from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_flows_gb.csv"
output_path = project_root / "outputs/figures/britned_da_vs_final_imports.png"

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")
data["da_net_nl_imports_mw"] = -data["da_net_nl_exports_mw"]
data["final_net_nl_imports_mw"] = -data["fin_net_nl_exports_mw"]

fig, ax = plt.subplots(figsize=(12, 5))

ax.axhline(0, color="black", linewidth=1)
ax.step(
    data["time"],
    data["da_net_nl_imports_mw"],
    where="post",
    label="DA scheduled NL imports from GB",
)
ax.step(
    data["time"],
    data["final_net_nl_imports_mw"],
    where="post",
    label="Final scheduled NL imports from GB",
)
ax.set_title("BritNed: day-ahead vs final NL import schedule")
ax.set_xlabel("Time, UTC")
ax.set_ylabel("Net imports into NL, MW")
ax.legend()
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
