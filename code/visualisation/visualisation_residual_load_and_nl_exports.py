from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
market_path = project_root / "data/processed/nl_market_15m.csv"
flows_path = project_root / "data/processed/nl_flows_total.csv"
output_path = project_root / "outputs/figures/residual_load_error_and_nl_exports.png"

market = pd.read_csv(market_path)
flows = pd.read_csv(flows_path)

market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")
flows["time"] = pd.to_datetime(flows["time_utc"], format="%H:%M:%S")
market["residual_load_error_mw"] = (
    market["residual_load_actual_mw"] - market["residual_load_da_mw"]
)

fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

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

axes[1].step(
    flows["time"],
    flows["da_net_nl_exports_mw"],
    where="post",
    label="DA total net exports",
    color="tab:blue",
)
axes[1].step(
    flows["time"],
    flows["fin_net_nl_exports_mw"],
    where="post",
    label="Final total net exports",
    color="tab:orange",
)
axes[1].fill_between(
    flows["time"],
    flows["da_net_nl_exports_mw"],
    flows["fin_net_nl_exports_mw"],
    step="post",
    alpha=0.2,
    color="grey",
    label="Flow adjustment",
)
axes[1].axhline(0, color="black", linewidth=1)
axes[1].set_title("NL total net exports: day-ahead vs final")
axes[1].set_xlabel("Time, UTC")
axes[1].set_ylabel("Net exports, MW")
axes[1].legend()
axes[1].grid(alpha=0.3)
axes[1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
