import pandas as pd


solar_db = pd.read_csv('data/raw/solar.csv')
wind_db = pd.read_csv('data/raw/wind.csv')
demand_db = pd.read_csv('data/raw/demand.csv')
da_prices_db = pd.read_csv('data/raw/da_prices_nl.csv')
imbalance_prices_db = pd.read_csv('data/raw/imbalance_prices_nl.csv')


def merge_dataframes(df1, df2):
    return df1.merge(df2, on="time_utc", how="inner", validate="one_to_one")


nl_market_15m = merge_dataframes(solar_db, wind_db)
nl_market_15m = merge_dataframes(nl_market_15m, demand_db)
nl_market_15m = merge_dataframes(nl_market_15m, da_prices_db)
nl_market_15m = merge_dataframes(nl_market_15m, imbalance_prices_db)
nl_market_15m.to_csv('data/processed/nl_market_15m.csv', index=False)