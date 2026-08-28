import pandas as pd

balance_delta_db = pd.read_csv("data/raw/balance_delta.csv")

balance_delta_db["power_net_afrr_mw"] = balance_delta_db['power_in_afrr_mw'] - balance_delta_db['power_out_afrr_mw']
balance_delta_db["power_net_igcc_mw"] = balance_delta_db['power_in_igcc_mw'] - balance_delta_db['power_out_igcc_mw']
balance_delta_db["power_net_mfrrda_mw"] = balance_delta_db['power_in_mfrrda_mw'] - balance_delta_db['power_out_mfrrda_mw']
balance_delta_db["time_utc"] = (
    pd.to_datetime(
        balance_delta_db["time_start_cet"],
        format="%H:%M:%S",
    )
    .sub(pd.Timedelta(hours=1))
    .dt.strftime("%H:%M:%S")
)
balance_delta_db["power_net_picasso_mw"] = balance_delta_db["picasso_in_mw"] - balance_delta_db["picasso_out_mw"]
balance_delta_db["power_net_total_mw"] = (
    balance_delta_db["power_net_afrr_mw"]
    + balance_delta_db["power_net_igcc_mw"]
    + balance_delta_db["power_net_mfrrda_mw"]
    + balance_delta_db["power_net_picasso_mw"]
).round(2)

balance_delta_total = balance_delta_db[
    [
        "time_utc",
        "power_net_afrr_mw",
        "power_net_igcc_mw",
        "power_net_mfrrda_mw",
        "power_net_picasso_mw",
        "power_net_total_mw",
    ]
]

balance_delta_total.to_csv('data/processed/balance_delta_total.csv', index=False)