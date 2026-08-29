import pandas as pd

nl_flows_db = pd.read_csv("data/raw/nl_flows.csv")
neso_auctions_db = pd.read_csv("data/raw/neso_auctions.csv")

nl_flows_gb_db = (
    nl_flows_db[nl_flows_db["border"] == "GB"]
    .copy()
)

neso_britned_hourly = (
    neso_auctions_db
    .groupby("delivery_start_time_utc", as_index=False)["bn_volume_mw"]
    .sum()
    .rename(columns={"bn_volume_mw": "neso_buy_mw"})
)

nl_flows_gb_db = (
    nl_flows_gb_db
    .merge(
        neso_britned_hourly,
        left_on="time_utc",
        right_on="delivery_start_time_utc",
        how="left",
        validate="one_to_one",
    )
    .drop(columns="delivery_start_time_utc")
)

nl_flows_gb_db["neso_buy_mw"] = (
    nl_flows_gb_db["neso_buy_mw"]
    .fillna(0)
)

nl_flows_gb_db.to_csv(
    "data/processed/nl_flows_gb.csv",
    index=False,
)