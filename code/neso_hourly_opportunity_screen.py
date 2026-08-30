from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[1]
trades_path = project_root / "data/raw/trades.csv"
auctions_path = project_root / "data/raw/neso_auctions.csv"
flows_path = project_root / "data/processed/nl_flows_gb.csv"
capacities_path = project_root / "data/processed/capacities_total.csv"
market_path = project_root / "data/processed/nl_market_15m.csv"
output_csv = project_root / "data/processed/hourly_neso_event_screen.csv"
output_figure = project_root / "outputs/figures/hourly_neso_opportunity_screen.png"

trades = pd.read_csv(trades_path)
trades = trades[
    (trades["product"] == "XBID_Hour_Power")
    & (trades["trade_phase"] == "CONT")
].drop_duplicates("trade_id").copy()
trades["execution_time"] = pd.to_datetime(
    trades["execution_time_utc"],
    format="%H:%M:%S.%f",
)

auctions = pd.read_csv(auctions_path)
auctions = auctions.groupby(
    ["published_time_utc", "delivery_start_time_utc"],
    as_index=False,
)["bn_volume_mw"].sum()

flows = pd.read_csv(flows_path).set_index("time_utc")
capacities = pd.read_csv(capacities_path).set_index("time_utc")
market = pd.read_csv(market_path)
market["time"] = pd.to_datetime(market["time_utc"], format="%H:%M:%S")

rows = []
for auction in auctions.itertuples(index=False):
    delivery_start = auction.delivery_start_time_utc
    product_trades = trades[
        trades["delivery_start_time_utc"] == delivery_start
    ].sort_values("execution_time").copy()
    if product_trades.empty:
        continue

    publication_time = pd.to_datetime(
        auction.published_time_utc,
        format="%H:%M:%S",
    )
    delivery_time = pd.to_datetime(delivery_start, format="%H:%M:%S")
    delivery_end = delivery_time + pd.Timedelta(hours=1)

    pre_15min = product_trades[
        (product_trades["execution_time"] >= publication_time - pd.Timedelta(minutes=15))
        & (product_trades["execution_time"] < publication_time)
    ]
    post_15min = product_trades[
        (product_trades["execution_time"] >= publication_time)
        & (product_trades["execution_time"] < publication_time + pd.Timedelta(minutes=15))
    ]
    after_publication = product_trades[
        (product_trades["execution_time"] >= publication_time)
        & (product_trades["execution_time"] < delivery_time)
    ].copy()
    after_publication["execution_5min"] = after_publication[
        "execution_time"
    ].dt.floor("5min")
    price_5min = after_publication.groupby("execution_5min")[
        "price_eur_mwh"
    ].median()

    delivery_market = market[
        (market["time"] >= delivery_time)
        & (market["time"] < delivery_end)
    ]
    da_price = delivery_market["price_da_eur_mwh"].mean()
    flow = flows.loc[delivery_start]
    da_britned_import = max(-flow["da_net_nl_exports_mw"], 0)

    pre_price = pre_15min["price_eur_mwh"].median()
    post_price = post_15min["price_eur_mwh"].median()
    rows.append(
        {
            "publication_time_utc": auction.published_time_utc,
            "delivery_start_time_utc": delivery_start,
            "product": (
                f"{delivery_start[:5]}–{delivery_end:%H:%M}"
            ),
            "hours_to_delivery": (
                delivery_time - publication_time
            ).total_seconds() / 3600,
            "da_price_eur_mwh": da_price,
            "neso_britned_buy_mw": auction.bn_volume_mw,
            "da_britned_import_mw": da_britned_import,
            "neso_buy_pct_da_import": (
                100 * auction.bn_volume_mw / da_britned_import
                if da_britned_import
                else pd.NA
            ),
            "inbound_atc_mw": capacities.loc[
                delivery_start, "capacity_to_nl_total"
            ],
            "pre_15min_price_eur_mwh": pre_price,
            "post_15min_price_eur_mwh": post_price,
            "immediate_change_eur_mwh": post_price - pre_price,
            "max_after_price_eur_mwh": price_5min.max(),
            "post15_to_max_move_eur_mwh": price_5min.max() - post_price,
            "trades_after_publication": after_publication["trade_id"].nunique(),
            "volume_after_publication_mwh": after_publication["volume_mwh"].sum(),
        }
    )

screen = pd.DataFrame(rows)
screen.to_csv(output_csv, index=False)

publication_colors = {
    "03:18:41": "tab:blue",
    "09:46:42": "tab:orange",
    "12:04:00": "tab:red",
    "17:28:08": "tab:purple",
}
colors = screen["publication_time_utc"].map(publication_colors)
labels = [
    f"{publication[:5]}\n{product}"
    for publication, product in zip(
        screen["publication_time_utc"],
        screen["product"],
    )
]
x = list(range(len(screen)))

fig, axes = plt.subplots(4, 1, figsize=(17, 15), sharex=True)

axes[0].bar(x, screen["immediate_change_eur_mwh"], color=colors, alpha=0.8)
axes[0].axhline(0, color="black", linewidth=1)
axes[0].set_title("Immediate ID repricing: 15 minutes after minus 15 minutes before")
axes[0].set_ylabel("Price change, EUR/MWh")

axes[1].bar(x, screen["post15_to_max_move_eur_mwh"], color=colors, alpha=0.8)
axes[1].set_title("Maximum later intraday uplift from the post-publication price")
axes[1].set_ylabel("Uplift, EUR/MWh")

axes[2].bar(x, screen["neso_buy_pct_da_import"], color=colors, alpha=0.8)
axes[2].axhline(100, color="black", linestyle="--", linewidth=1.2, label="100% of DA BritNed import")
axes[2].set_title("NESO BritNed Buy relative to DA scheduled BritNed import")
axes[2].set_ylabel("Percent")
axes[2].legend(loc="upper left")

axes[3].bar(x, screen["inbound_atc_mw"], color=colors, alpha=0.8)
axes[3].set_title("Reported inbound ATC for the delivery hour")
axes[3].set_ylabel("ATC, MW")
axes[3].set_xlabel("NESO publication time and hourly delivery product, UTC")
axes[3].set_xticks(x, labels, rotation=55, ha="right")

for ax in axes:
    ax.grid(axis="y", alpha=0.3)

fig.suptitle(
    "NESO hourly-product opportunity screen (ex-post selection only)",
    fontsize=15,
    y=1.0,
)
fig.tight_layout()
output_figure.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_figure, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved to: {output_csv}")
print(f"Saved to: {output_figure}")
