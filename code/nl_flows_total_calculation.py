import pandas as pd

nl_flows_db = pd.read_csv("data/raw/nl_flows.csv")

nl_flows_total = (
    nl_flows_db[
        [
            "time_utc",
            "da_net_nl_exports_mw",
            "fin_net_nl_exports_mw",
            "id_adjustment_mw",
        ]
    ]
    .groupby("time_utc", as_index=False)
    .sum()
    .round(2)
)

nl_flows_total.to_csv('data/processed/nl_flows_total.csv', index=False)