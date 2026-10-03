import sys
import pandas as pd
import psycopg2

# Database Connection Parameters
# Replace 'YOUR_ACTUAL_PASSWORD' with your real PostgreSQL password
DB_PARAMS = {
    "dbname": "process_mining_db",
    "user": "postgres",
    "password": "Reshuadmin",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """
    Establishes and returns a native psycopg2 DBAPI connection to PostgreSQL.
    """
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        print(f"[-] Database connection failure: {e}")
        sys.exit(1)

def fetch_transition_matrix(min_volume: int = 500) -> pd.DataFrame:
    """
    Executes vectorized window function query on p2p_event_logs
    and returns activity-to-activity transition metrics as a DataFrame.
    """
    conn = get_db_connection()
    
    query = f"""
    WITH SequencedEvents AS (
        SELECT 
            case_id,
            activity_name AS source_node,
            event_timestamp AS t1,
            LEAD(activity_name) OVER (
                PARTITION BY case_id 
                ORDER BY event_timestamp ASC
            ) AS target_node,
            LEAD(event_timestamp) OVER (
                PARTITION BY case_id 
                ORDER BY event_timestamp ASC
            ) AS t2
        FROM p2p_event_logs
        WHERE event_timestamp >= '2018-01-01 00:00:00'
          AND event_timestamp <= '2019-06-30 23:59:59'
    ),
    Transitions AS (
        SELECT 
            source_node,
            target_node,
            EXTRACT(EPOCH FROM (t2 - t1)) / 3600.0 AS delay_hours
        FROM SequencedEvents
        WHERE target_node IS NOT NULL
    )
    SELECT 
        source_node,
        target_node,
        COUNT(*) AS volume,
        ROUND(AVG(delay_hours)::numeric, 2) AS avg_delay_hours,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_hours)::numeric, 2) AS median_delay_hours
    FROM Transitions
    GROUP BY source_node, target_node
    HAVING COUNT(*) >= {min_volume}
    ORDER BY volume DESC;
    """
    
    try:
        # Native psycopg2 connection + raw string query execution
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
        
    return df

if __name__ == "__main__":
    df_result = fetch_transition_matrix(min_volume=500)
    print(f"[+] Successfully extracted {len(df_result)} aggregated transition pairs.")
    print(df_result.head(10))
