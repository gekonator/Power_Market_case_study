from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
auctions_path = project_root / "data/raw/neso_auctions.csv"
flows_path = project_root / "data/processed/nl_flows_gb.csv"
output_path = (
    project_root
    / "outputs/figures/neso_vs_da_britned_import_0946_12_15.png"
)

publication_time = "09:46:42"
delivery_hours = ["12:00:00", "13:00:00", "14:00:00"]

auctions = pd.read_csv(auctions_path)
flows = pd.read_csv(flows_path)

neso_buy = (
    auctions[
        (auctions["published_time_utc"] == publication_time)
        & (auctions["delivery_start_time_utc"].isin(delivery_hours))
    ]
    .groupby("delivery_start_time_utc", as_index=False)["bn_volume_mw"]
    .sum()
    .rename(columns={"bn_volume_mw": "neso_britned_buy_mw"})
)

comparison = flows[
    flows["time_utc"].isin(delivery_hours)
][["time_utc", "da_net_nl_exports_mw"]].merge(
    neso_buy,
    left_on="time_utc",
    right_on="delivery_start_time_utc",
    how="left",
    validate="one_to_one",
)
comparison = comparison.sort_values("time_utc")

if len(comparison) != len(delivery_hours):
    raise ValueError("Not all selected delivery hours were found")
if comparison["neso_britned_buy_mw"].isna().any():
    raise ValueError("Missing NESO BritNed Buy volume")

# The source flow convention is positive for NL export and negative for NL import.
comparison["da_britned_import_into_nl_mw"] = (
    -comparison["da_net_nl_exports_mw"]
).clip(lower=0)
comparison["buy_pct_da_import"] = (
    100
    * comparison["neso_britned_buy_mw"]
    / comparison["da_britned_import_into_nl_mw"]
)

start_times = pd.to_datetime(comparison["time_utc"], format="%H:%M:%S")
labels = [
    f"{start:%H:%M}–{start + pd.Timedelta(hours=1):%H:%M}"
    for start in start_times
]
x = np.arange(len(comparison))
width = 0.36

fig, ax = plt.subplots(figsize=(10, 6))
da_bars = ax.bar(
    x - width / 2,
    comparison["da_britned_import_into_nl_mw"],
    width,
    color="tab:blue",
    alpha=0.8,
    label="DA scheduled BritNed import into NL",
)
neso_bars = ax.bar(
    x + width / 2,
    comparison["neso_britned_buy_mw"],
    width,
    color="tab:red",
    alpha=0.8,
    label="NESO BritNed Buy for GB, published 09:46",
)

for bars in (da_bars, neso_bars):
    ax.bar_label(bars, fmt="%.0f MW", padding=3, fontsize=9)

for index, percent in enumerate(comparison["buy_pct_da_import"]):
    height = max(
        comparison.iloc[index]["da_britned_import_into_nl_mw"],
        comparison.iloc[index]["neso_britned_buy_mw"],
    )
    ax.text(
        index,
        height + 75,
        f"NESO Buy = {percent:.0f}% of DA import",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

ax.set_title(
    "Known BritNed supply shock for selected hourly products\n"
    "NESO disclosure at 09:46:42 UTC"
)
ax.set_xlabel("Hourly delivery product, UTC")
ax.set_ylabel("Power, MW")
ax.set_xticks(x, labels)
ax.set_ylim(0, comparison[[
    "da_britned_import_into_nl_mw",
    "neso_britned_buy_mw",
]].to_numpy().max() * 1.28)
ax.grid(axis="y", alpha=0.3)
ax.legend(loc="upper right")

fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(comparison[[
    "time_utc",
    "da_britned_import_into_nl_mw",
    "neso_britned_buy_mw",
    "buy_pct_da_import",
]].round(1).to_string(index=False))
print(f"Saved to: {output_path}")
