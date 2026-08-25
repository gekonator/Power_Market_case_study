import pandas as pd
import numpy as np

def load_aox_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep=';',
        decimal=',',
        thousands='\u00A0',
    )

balance_delta_df = load_aox_csv('data/csv/balance_delta.csv')
print(balance_delta_df.head(10))