from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data/processed/nl_flows_gb.csv"
output_path = project_root / "outputs/figures/britned_imports_and_neso_buy.png"

data = pd.read_csv(data_path)
data["time"] = pd.to_datetime(data["time_utc"], format="%H:%M:%S")
data["da_net_nl_imports_mw"] = -data["da_net_nl_exports_mw"]
data["final_net_nl_imports_mw"] = -data["fin_net_nl_exports_mw"]

fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

axes[0].axhline(0, color="black", linewidth=1)
axes[0].step(
    data["time"],
    data["da_net_nl_imports_mw"],
    where="post",
    label="DA scheduled NL imports from GB",
)
axes[0].step(
    data["time"],
    data["final_net_nl_imports_mw"],
    where="post",
    label="Final scheduled NL imports from GB",
)
axes[0].set_title("BritNed: day-ahead vs final NL import schedule")
axes[0].set_ylabel("Net imports into NL, MW")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].axhline(0, color="black", linewidth=1)
axes[1].bar(
    data["time"],
    data["id_adjustment_mw"],
    width=pd.Timedelta(minutes=45),
    label="Final minus DA net NL exports",
    color="tab:blue",
    alpha=0.7,
)
axes[1].plot(
    data["time"],
    data["neso_buy_mw"],
    label="NESO Buy volume on BritNed",
    color="tab:red",
    marker="o",
)
axes[1].set_title("BritNed schedule adjustment vs NESO Buy volume")
axes[1].set_xlabel("Time, UTC")
axes[1].set_ylabel("Adjustment toward GB, MW")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
