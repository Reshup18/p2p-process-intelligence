# ⚡ Enterprise Process Intelligence & Automated Bottleneck Analyzer

An end-to-end Process Mining Engine engineered to ingest, model, and visualize 1.5M+ Procure-to-Pay (P2P) event logs from the **BPI Challenge 2019** enterprise dataset.

## 🎯 Executive Impact & Performance Benchmarks
* **High-Throughput Log Ingestion**: Ingested and structured **1,595,923 timestamped event records** across **251,734 unique purchase order cases**.
* **Query Latency Acceleration**: Optimized analytical log windowing using PostgreSQL CTEs and `LEAD()`/`LAG()` window functions paired with B-Tree composite indexes, achieving sub-4-second query execution.
* **Bottleneck Isolation**: Identified that finance payment release (`Record Invoice Receipt` -> `Clear Invoice`) accounts for primary enterprise delay, with a median handoff latency of **865 hours (~36 days)**.
* **Real-Time Topology Rendering**: Aggregated 1.5M+ event rows into an adjacency matrix directly inside SQL, preventing browser memory exhaustion during dynamic Graphviz DAG rendering.

## 🛠 Tech Stack
* **Database Engine**: PostgreSQL 14+, B-Tree Indexing, CTEs, Window Functions (`LEAD`, `LAG`).
* **Python Backend**: Python 3.12, `psycopg2-binary`, `pandas`, `pm4py`.
* **Frontend Visualization**: Streamlit Web Engine, Graphviz (DOT Language).

## 🚀 Execution Guide
```bash
pip install -r requirements.txt
psql -U postgres -d process_mining_db -f schema.sql
streamlit run app.py
```
