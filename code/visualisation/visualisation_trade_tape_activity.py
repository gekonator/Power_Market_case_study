from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
output_path = project_root / "outputs/figures/trade_tape_activity_full_day.png"

trades = pd.read_csv(trades_path)
trades = trades[trades["trade_phase"] == "CONT"].drop_duplicates(
    "trade_id"
).copy()
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")

product_types = [
    ("XBID_Hour_Power", "Hourly continuous products"),
    ("XBID_Quarter_Hour_Power", "Quarter-hour continuous products"),
]
disclosures = [
    ("09:46:42", "09:46 disclosure"),
    ("12:04:00", "12:04 disclosure"),
    ("17:28:08", "17:28 disclosure"),
]

fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
for ax, (product, title) in zip(axes, product_types):
    product_trades = trades[trades["product"] == product]
    activity = product_trades.groupby(
        "execution_5min",
        as_index=False,
    ).agg(
        unique_trades=("trade_id", "nunique"),
        volume_mwh=("volume_mwh", "sum"),
    )

    volume_ax = ax.twinx()
    volume_ax.bar(
        activity["execution_5min"],
        activity["volume_mwh"],
        width=pd.Timedelta(minutes=4),
        color="tab:gray",
        alpha=0.22,
        label="5-minute volume",
    )
    volume_ax.set_ylabel("Volume, MWh", color="tab:gray")
    volume_ax.tick_params(axis="y", labelcolor="tab:gray")

    ax.plot(
        activity["execution_5min"],
        activity["unique_trades"],
        color="tab:blue",
        linewidth=1.3,
        label="Unique trades per 5 minutes",
    )
    for index, (clock, label) in enumerate(disclosures):
        ax.axvline(
            pd.to_datetime(clock, format="%H:%M:%S"),
            color="tab:red",
            linestyle=["--", ":", "-."][index],
            linewidth=1.1,
            alpha=0.8,
            label=label,
        )

    ax.axvspan(
        pd.to_datetime("10:00:00", format="%H:%M:%S"),
        pd.to_datetime("14:00:00", format="%H:%M:%S"),
        color="tab:orange",
        alpha=0.08,
        label="Main stress window",
    )
    ax.set_title(title)
    ax.set_ylabel("Unique trades")
    ax.grid(alpha=0.3)

    activity_handles, activity_labels = ax.get_legend_handles_labels()
    volume_handles, volume_labels = volume_ax.get_legend_handles_labels()
    ax.legend(
        activity_handles + volume_handles,
        activity_labels + volume_labels,
        loc="upper right",
        fontsize=8,
        ncol=2,
    )

axes[-1].set_xlim(
    pd.to_datetime("00:00:00", format="%H:%M:%S"),
    pd.to_datetime("23:59:59", format="%H:%M:%S"),
)
axes[-1].set_xlabel("Execution time, UTC")
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=1))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
fig.suptitle(
    "Full-day execution clustering in the deduplicated continuous trade tape",
    fontsize=14,
    y=1.0,
)
fig.tight_layout()
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_path}")
