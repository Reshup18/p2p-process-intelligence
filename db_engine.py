import os
import pandas as pd

def fetch_transition_matrix(min_volume: int = 500) -> pd.DataFrame:
    csv_path = 'transition_matrix.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df[df['volume'] >= min_volume].reset_index(drop=True)
    else:
        raise FileNotFoundError('transition_matrix.csv not found!')
