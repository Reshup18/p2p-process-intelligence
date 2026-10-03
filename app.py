import streamlit as st
import pandas as pd
import graphviz
from db_engine import fetch_transition_matrix

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="P2P Enterprise Process Intelligence Engine",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Enterprise Process Intelligence & Bottleneck Analyzer")
st.markdown("Real-time process mining workflow topology extracted directly from PostgreSQL event logs.")

# 2. Sidebar Filter Controls
st.sidebar.header("Operational SLA & Filter Controls")

sla_threshold = st.sidebar.slider(
    "SLA Breach Threshold (Hours)",
    min_value=1,
    max_value=500,
    value=24,
    step=1,
    help="Transitions with average delay exceeding this value will be flagged red as SLA breaches."
)

min_volume = st.sidebar.slider(
    "Minimum Transition Volume Filter",
    min_value=100,
    max_value=10000,
    value=1000,
    step=100,
    help="Filters out rare/edge-case transitions to simplify process graph visualization."
)

# 3. Data Extraction & Metric Processing
@st.cache_data(ttl=3600)
def load_and_process_transitions(volume_filter: int, sla_limit: int) -> pd.DataFrame:
    df = fetch_transition_matrix(min_volume=volume_filter)
    if not df.empty:
        # Flag transition paths exceeding SLA threshold
        df['sla_breach'] = df['avg_delay_hours'] > sla_limit
    return df

df_transitions = load_and_process_transitions(min_volume, sla_threshold)

# 4. Top KPI Metric Summary Cards
col1, col2, col3, col4 = st.columns(4)

if not df_transitions.empty:
    total_extracted_transitions = len(df_transitions)
    total_case_flow_volume = df_transitions['volume'].sum()
    total_sla_breaches = len(df_transitions[df_transitions['sla_breach']])
    max_transition_latency = df_transitions['avg_delay_hours'].max()
    
    col1.metric("Extracted Node Paths", f"{total_extracted_transitions:,}")
    col2.metric("Total Transition Volume", f"{total_case_flow_volume:,}")
    col3.metric("SLA Breached Paths", f"{total_sla_breaches}", delta=f"{total_sla_breaches} Critical", delta_color="inverse")
    col4.metric("Max Handoff Delay", f"{max_transition_latency:.1f} hrs")
else:
    st.warning("No transition data found matching current volume filter settings.")

st.divider()

# 5. Graphviz Directed Graph Construction (DFG)
st.subheader("Process Workflow Topology (Directly-Follows Graph)")

if not df_transitions.empty:
    # Initialize Graphviz Directed Graph
    dot = graphviz.Digraph(comment='P2P Process Topology')
    dot.attr(rankdir='LR', size='12,8', bgcolor='transparent')
    
    # Extract unique process activity nodes
    unique_nodes = set(df_transitions['source_node']).union(set(df_transitions['target_node']))
    
    # Add nodes to graph
    for node in unique_nodes:
        dot.node(
            node, 
            label=node, 
            shape='rectangle', 
            style='filled,rounded', 
            fillcolor='#E2E8F0',
            fontname='Helvetica',
            fontsize='10'
        )
        
    # Add directed edges (arrows) between nodes
    max_vol = df_transitions['volume'].max()
    for _, row in df_transitions.iterrows():
        is_breach = row['sla_breach']
        # Red line for SLA breaches, Slate Gray for compliant steps
        edge_color = "#E53E3E" if is_breach else "#4A5568" 
        
        # Scale edge line thickness based on transition volume (Range: 1.0 to 8.0)
        pen_width = str(max(1.0, min(8.0, (row['volume'] / max_vol) * 8.0)))
        
        # Edge text label displaying case volume and average delay
        edge_label = f"{int(row['volume']):,} cases\n{row['avg_delay_hours']:.1f} hrs"
        
        dot.edge(
            row['source_node'], 
            row['target_node'], 
            label=edge_label, 
            color=edge_color, 
            penwidth=pen_width,
            fontsize='8',
            fontcolor=edge_color
        )
        
    # Render Graphviz DAG inside Streamlit layout
    st.graphviz_chart(dot, use_container_width=True)

st.divider()

# 6. Detailed Transition Data Table
st.subheader("Transition Analytics & SLA Performance Table")
if not df_transitions.empty:
    st.dataframe(
        df_transitions.style.highlight_between(
            subset=['avg_delay_hours'], 
            left=sla_threshold, 
            right=1000000, 
            color='#FED7D7'
        ),
        use_container_width=True
    )
