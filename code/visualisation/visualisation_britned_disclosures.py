from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


project_root = Path(__file__).resolve().parents[2]
auctions_path = project_root / "data/raw/neso_auctions.csv"
flows_path = project_root / "data/processed/nl_flows_gb.csv"
output_dir = project_root / "outputs/figures"

auctions = pd.read_csv(auctions_path)
flows = pd.read_csv(flows_path)

# One disclosure can contain several lots for the same delivery hour.
disclosure_hourly = (
    auctions.groupby(
        ["published_time_utc", "delivery_start_time_utc"],
        as_index=False,
    )["bn_volume_mw"]
    .sum()
    .rename(columns={"bn_volume_mw": "disclosure_bn_buy_mw"})
)

output_dir.mkdir(parents=True, exist_ok=True)

for publication_time, disclosure in disclosure_hourly.groupby(
    "published_time_utc", sort=True
):
    disclosure = disclosure.merge(
        flows[
            [
                "time_utc",
                "id_adjustment_mw",
            ]
        ],
        left_on="delivery_start_time_utc",
        right_on="time_utc",
        how="left",
        validate="one_to_one",
    )

    if disclosure["id_adjustment_mw"].isna().any():
        raise ValueError(
            f"Missing BritNed schedule adjustment for disclosure {publication_time}"
        )

    disclosure = disclosure.sort_values("delivery_start_time_utc")
    labels = disclosure["delivery_start_time_utc"].str.slice(0, 5)
    x = range(len(disclosure))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(0, color="black", linewidth=1)
    ax.bar(
        x,
        disclosure["id_adjustment_mw"],
        label="Final minus DA net NL exports to GB",
        color="tab:blue",
        alpha=0.7,
    )
    ax.plot(
        x,
        disclosure["disclosure_bn_buy_mw"],
        label="BritNed Buy volume in this disclosure",
        color="tab:red",
        marker="o",
        linewidth=2,
    )

    ax.set_title(
        "BritNed schedule adjustment vs NESO Buy volume\n"
        f"NESO disclosure at {publication_time} UTC"
    )
    ax.set_xlabel("Delivery start time, UTC")
    ax.set_ylabel("Adjustment towards Great Britain, MW")
    ax.set_xticks(list(x), labels)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    filename_time = publication_time.replace(":", "")
    output_path = output_dir / f"britned_disclosure_{filename_time}.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(
        f"Saved to: {output_path} "
        f"({len(disclosure)} delivery hours)"
    )
