import streamlit as st
import json
import os
from uuid import uuid4

# File paths
CLOUD_FILE = "requirements_cloud.json"
WORKFLOW_DIR = "workflows"
os.makedirs(WORKFLOW_DIR, exist_ok=True)

# Session state to track if cloud data is submitted
if 'cloud_submitted' not in st.session_state:
    st.session_state.cloud_submitted = False
if 'workflow_functions' not in st.session_state:
    st.session_state.workflow_functions = {}
if 'workflow_dependencies' not in st.session_state:
    st.session_state.workflow_dependencies = {}
if 'workflow_parallel_paths' not in st.session_state:
    st.session_state.workflow_parallel_paths = 1

st.title("Cloud and Workflow Configuration")

# ---------------- CLOUD NODES INPUT ----------------
if not st.session_state.cloud_submitted:
    st.header("1. Define Cloud Nodes")

    st.subheader("TinyFaaS Nodes")
    with st.form("tinyfaas_form"):
        num_tinyfaas = st.number_input("Number of TinyFaaS Nodes", min_value=0, value=0)
        tinyfaas_nodes = []
        for i in range(num_tinyfaas):
            st.markdown(f"**TinyFaaS Node {i + 1}**")
            latency = st.number_input(f"Estimated Latency (ms) - Node {i + 1}", key=f"lat_{i}")
            ram = st.number_input(f"Max Current RAM (MB) - Node {i + 1}", key=f"ram_{i}")
            tinyfaas_nodes.append({"latency": latency, "max_ram": ram})

        submitted = st.form_submit_button("Submit TinyFaaS Nodes")

    st.subheader("Other Cloud Nodes")
    if 'other_nodes' not in st.session_state:
        st.session_state.other_nodes = []

    with st.form("other_node_form"):
        name = st.text_input("Node Name")
        pricing = st.number_input("Pricing (USD/hour)")
        if st.form_submit_button("Add Node"):
            st.session_state.other_nodes.append({"name": name, "pricing": pricing})

    if submitted:
        cloud_data = {
            "tinyfaas_nodes": tinyfaas_nodes,
            "other_nodes": st.session_state.other_nodes
        }
        with open(CLOUD_FILE, 'w') as f:
            json.dump(cloud_data, f, indent=2)
        st.session_state.cloud_submitted = True
        st.success("Cloud data submitted successfully!")

# ---------------- WORKFLOW INPUT ----------------
if st.session_state.cloud_submitted:
    st.header("2. Define Workflows")

    with st.form("workflow_form"):
        func_name = st.text_input("Function Name (unique key)")
        time = st.number_input("Execution Time (ms)", min_value=0)
        ram = st.number_input("RAM Requirement (MB)", min_value=0)
        prob_request = st.number_input("Probability of Request", min_value=0.0, max_value=1.0)
        data_send = st.number_input("Data to Send (MB)", min_value=0.0)
        data_dependencies = st.text_input("Data Dependencies (comma-separated)")

        dependencies = st.text_input("Successor Functions (comma-separated)")
        parallel_paths = st.number_input("Number of Parallel Paths", min_value=1, value=st.session_state.workflow_parallel_paths)

        if st.form_submit_button("Add Function"):
            st.session_state.workflow_functions[func_name] = {
                "time": time,
                "ram": ram,
                "prob_request": prob_request,
                "data_send": data_send,
                "data_dependencies": [x.strip() for x in data_dependencies.split(',') if x.strip()]
            }
            st.session_state.workflow_dependencies[func_name] = [x.strip() for x in dependencies.split(',') if x.strip()]
            st.session_state.workflow_parallel_paths = parallel_paths
            st.success(f"Function '{func_name}' added.")

    if st.session_state.workflow_functions:
        if st.button("Submit Workflow"):
            workflow_data = {
                "functions": st.session_state.workflow_functions,
                "dependencies": st.session_state.workflow_dependencies,
                "parallel_paths": st.session_state.workflow_parallel_paths
            }
            workflow_id = str(uuid4())[:8]
            workflow_file = os.path.join(WORKFLOW_DIR, f"workflow_{workflow_id}.json")
            with open(workflow_file, 'w') as f:
                json.dump(workflow_data, f, indent=2)
            st.success(f"Workflow submitted and saved as {workflow_file}.")

            # Reset workflow state for a new workflow
            st.session_state.workflow_functions = {}
            st.session_state.workflow_dependencies = {}
            st.session_state.workflow_parallel_paths = 1