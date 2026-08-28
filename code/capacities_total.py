import pandas as pd

capacities_db = pd.read_csv("data/raw/capacities.csv")

capacities_db["capacity_to_nl_total"] = capacities_db[
    ["be_to_nl", "de_to_nl", "dk_to_nl", "no_to_nl"]
].sum(axis=1)

capacities_db["capacity_from_nl_total"] = capacities_db[
    ["nl_to_be", "nl_to_de", "nl_to_dk", "nl_to_no"]
].sum(axis=1)

capacities_total = capacities_db[
    [
        "time_utc",
        "capacity_to_nl_total",
        "capacity_from_nl_total",
    ]
]

capacities_total.to_csv('data/processed/capacities_total.csv', index=False)