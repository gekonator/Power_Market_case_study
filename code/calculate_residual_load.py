import pandas as pd

nl_market_15m = pd.read_csv('data/processed/nl_market_15m.csv')

nl_market_15m['residual_load_da_mw'] =  nl_market_15m['demand_da_mw'] - nl_market_15m['solar_da_mw'] - nl_market_15m['wind_da_mw']
nl_market_15m['residual_load_actual_mw'] =  nl_market_15m['demand_actual_mw'] - nl_market_15m['solar_actual_mw'] - nl_market_15m['wind_actual_total_mw']


nl_market_15m.to_csv('data/processed/nl_market_15m.csv', index=False)