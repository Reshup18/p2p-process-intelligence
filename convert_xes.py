import pm4py
import pandas as pd
import time

def parse_xes_to_csv(xes_path="BPI_Challenge_2019.xes", output_csv="bpi_2019_raw.csv"):
    print(f"[+] Parsing XES log: {xes_path}")
    start_time = time.time()
    
    log = pm4py.read_xes(xes_path)
    df = pm4py.convert_to_dataframe(log)
    
    column_mapping = {
        'case:concept:name': 'case_id',
        'concept:name': 'activity_name',
        'time:timestamp': 'event_timestamp',
        'org:resource': 'resource_id'
    }
    df = df.rename(columns=column_mapping)
    
    keep_cols = ['case_id', 'activity_name', 'event_timestamp', 'resource_id']
    df_clean = df[keep_cols].copy()
    
    df_clean['event_timestamp'] = pd.to_datetime(df_clean['event_timestamp']).dt.strftime('%%Y-%%m-%%d %%H:%%M:%%S')
    df_clean['resource_id'] = df_clean['resource_id'].fillna('SYSTEM_AUTOMATED')
    df_clean = df_clean.sort_values(by=['case_id', 'event_timestamp']).reset_index(drop=True)
    
    df_clean.to_csv(output_csv, index=False)
    print(f"[+] Exported {len(df_clean):,} rows to '{output_csv}' in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    parse_xes_to_csv()
