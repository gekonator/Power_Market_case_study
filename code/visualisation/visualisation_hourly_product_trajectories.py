from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
trades_path = project_root / "data/raw/trades.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_dir = project_root / "outputs/figures"

trades = pd.read_csv(trades_path)
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
].drop_duplicates("trade_id").copy()
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)
trades["execution_5min"] = trades["execution_time"].dt.floor("5min")

market = pd.read_csv(market_path)
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")

product_starts = sorted(trades["delivery_start_time_utc"].unique())
chart_start = pd.to_datetime("00:00:00", format="%H:%M:%S")
stress_start = pd.to_datetime("10:00:00", format="%H:%M:%S")
stress_end = pd.to_datetime("14:00:00", format="%H:%M:%S")
disclosures = [
    pd.to_datetime("09:46:42", format="%H:%M:%S"),
    pd.to_datetime("12:04:00", format="%H:%M:%S"),
    pd.to_datetime("17:28:08", format="%H:%M:%S"),
]

summary_rows = []
legend_handles = [
    Line2D(
        [0],
        [0],
        color="tab:blue",
        linewidth=1.5,
        label="5-minute median execution price",
    ),
    Line2D(
        [0],
        [0],
        color="black",
        linestyle=":",
        linewidth=1.2,
        label="Mean day-ahead price for delivery hour",
    ),
    Line2D(
        [0],
        [0],
        color="tab:red",
        linestyle="--",
        linewidth=1.0,
        label="NESO disclosure times",
    ),
    Patch(
        facecolor="tab:orange",
        alpha=0.12,
        label="Main system-stress window in Q1",
    ),
]
product_groups = [
    product_starts[0:6],
    product_starts[6:12],
    product_starts[12:18],
    product_starts[18:22],
]
output_dir.mkdir(parents=True, exist_ok=True)
output_paths = []

for group_number, product_group in enumerate(product_groups, start=1):
    fig, axes = plt.subplots(2, 3, figsize=(17, 9), sharex=True)
    axes_flat = axes.flatten()
    group_chart_end = pd.to_datetime(
        product_group[-1], format="%H:%M:%S"
    )
    tick_interval = max(1, group_chart_end.hour // 7)

    for ax, product_start in zip(axes_flat, product_group):
        product_trades = trades[
            trades["delivery_start_time_utc"] == product_start
        ].sort_values("execution_time")
        trajectory = product_trades.groupby(
            "execution_5min", as_index=False
        ).agg(median_price_eur_mwh=("price_eur_mwh", "median"))

        delivery_start = pd.to_datetime(product_start, format="%H:%M:%S")
        delivery_end = delivery_start + pd.Timedelta(hours=1)
        delivery_market = market[
            (market["time"] >= delivery_start)
            & (market["time"] < delivery_end)
        ]
        da_price = delivery_market["price_da_eur_mwh"].mean()
        first_execution = product_trades["execution_time"].min()
        last_execution = product_trades["execution_time"].max()

        if last_execution >= stress_start and first_execution <= stress_end:
            ax.axvspan(
                max(first_execution, stress_start),
                min(last_execution, stress_end),
                color="tab:orange",
                alpha=0.08,
            )
        for disclosure in disclosures:
            if first_execution <= disclosure <= last_execution:
                ax.axvline(
                    disclosure,
                    color="tab:red",
                    linestyle="--",
                    linewidth=0.8,
                    alpha=0.55,
                )
        ax.plot(
            trajectory["execution_5min"],
            trajectory["median_price_eur_mwh"],
            color="tab:blue",
            linewidth=1.6,
        )
        ax.axhline(
            da_price,
            color="black",
            linestyle=":",
            linewidth=1.0,
            alpha=0.8,
        )

        end_label = delivery_end.strftime("%H:%M")
        ax.set_title(
            f"{delivery_start.strftime('%H:%M')}–{end_label} UTC",
            fontsize=11,
            fontweight="bold",
        )
        ax.set_ylabel("EUR/MWh", fontsize=9)
        ax.set_xlabel("Execution time, UTC", fontsize=9)
        ax.grid(alpha=0.22)
        ax.tick_params(axis="both", labelsize=8)
        ax.set_xlim(chart_start, group_chart_end)
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=tick_interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

        summary_rows.append(
            {
                "delivery_product": (
                    f"{delivery_start.strftime('%H:%M')}–{end_label}"
                ),
                "unique_trades": product_trades["trade_id"].nunique(),
                "volume_mwh": product_trades["volume_mwh"].sum(),
                "min_price_eur_mwh": product_trades["price_eur_mwh"].min(),
                "max_price_eur_mwh": product_trades["price_eur_mwh"].max(),
            }
        )

    for ax in axes_flat[len(product_group) :]:
        ax.set_visible(False)

    first_hour = product_group[0][:2]
    last_hour = product_group[-1][:2]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.955),
        ncol=3,
        fontsize=9,
    )
    fig.suptitle(
        "Intraday hourly-product trajectories: "
        f"delivery starts {first_hour}:00–{last_hour}:00 UTC",
        fontsize=15,
        y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    output_path = output_dir / (
        f"intraday_hourly_product_trajectories_{group_number}.png"
    )
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    output_paths.append(output_path)

summary = pd.DataFrame(summary_rows)
print(summary.to_string(index=False, formatters={"volume_mwh": "{:.1f}".format}))
print(f"Products plotted: {len(product_starts)}")
for output_path in output_paths:
    print(f"Saved to: {output_path}")
