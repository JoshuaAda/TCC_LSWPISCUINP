import streamlit as st
import json

def cloud_page():
    st.header("Cloud Configuration")

    num_nodes = st.number_input("Number of Nodes (tinyFaaS)", min_value=1, value=1, step=1)

    nodes = []
    for i in range(num_nodes):
        st.subheader(f"Node {i}")
        node = {
            "name": st.text_input(f"Node {i} Name", value=f"tf-node-{i}"),
            "max_RAM_curr": st.number_input(f"Node {i} Max RAM (MB)", min_value=1, value=1024, step=1),
            "url": st.text_input(f"Node {i} URL", value=f"http://localhost:{8080+i}")
        }
        nodes.append(node)

    st.subheader("Providers - tinyFaaS")
    tinyfaas_latency = st.number_input("tinyFaaS Estimated Latency (s)", value=0.1)

    st.subheader("Other Providers")
    num_providers = st.number_input("Number of Other Providers", min_value=0, value=1, step=1)

    other_providers = {}
    for i in range(num_providers):
        st.subheader(f"Provider {i}")
        provider_name = st.text_input(f"Provider {i} Name", key=f"provider_name_{i}")
        if provider_name:
            other_providers[provider_name] = {
                "pricing_RAM": st.number_input(f"{provider_name} Pricing RAM", value=0.0, key=f"pricing_RAM_{i}"),
                "pricing_StartRequest": st.number_input(f"{provider_name} Pricing Start Request", value=0.0, key=f"pricing_StartRequest_{i}"),
                "pricing_Storage_Transfer": st.number_input(f"{provider_name} Pricing Storage Transfer", value=0.0, key=f"pricing_Storage_Transfer_{i}"),
                "pricing_data_sent": st.number_input(f"{provider_name} Pricing Data Sent", value=0.0, key=f"pricing_data_sent_{i}"),
                "estimated_latency": st.number_input(f"{provider_name} Estimated Latency (s)", value=0.0, key=f"estimated_latency_{i}")
            }

    st.subheader("Serverless Settings")
    org = st.text_input("Organization Name")
    app_name = st.text_input("App Name")
    framework_version = st.text_input("Framework Version", value="3")
    project_name = st.text_input("Project Name")

    st.subheader("AWS Credentials")
    aws_key_id = st.text_input("AWS Access Key ID")
    aws_secret = st.text_input("AWS Secret Access Key")

    st.subheader("Google Credentials")
    google_client_email = st.text_input("Google Client Email")
    google_private_key = st.text_area("Google Private Key")

    if st.button("Save Cloud Configuration"):
        providers = {
            "tinyFaaS": {
                "estimated_latency": tinyfaas_latency,
                "pricing_Storage_Transfer": 0,
                "nodes": nodes
            }
        }
        providers.update(other_providers)

        cloud_config = {
            "num_leaves": num_nodes,
            "providers": providers,
            "serverless": {
                "org": org,
                "app": app_name,
                "frameworkVersion": framework_version,
                "project": project_name
            },
            "credentials": {
                "aws": {
                    "aws_access_key_id": aws_key_id,
                    "aws_secret_access_key": aws_secret
                },
                "google": {
                    "type": "service_account",
                    "project_id": project_name,
                    "private_key_id": "",
                    "private_key": google_private_key,
                    "client_email": google_client_email,
                    "client_id": "",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "",
                    "universe_domain": "googleapis.com"
                }
            }
        }

        with open("requirements_cloud.json", "w") as f:
            json.dump(cloud_config, f, indent=4)
        st.success("Cloud configuration saved to requirements_cloud.json!")

def workflow_page():
    st.header("Workflow Configuration")

    workflow_bucket = st.text_input("Workflow Bucket Name")
    deployment_number = st.number_input("Deployment Number", min_value=1, value=1, step=1)
    input_data = st.number_input("Input Data Size", min_value=0, value=10)

    input_functions = st.text_area("Input Functions (comma separated)").split(",")
    output_functions = st.text_area("Output Functions (comma separated)").split(",")

    st.subheader("Workflow Dependencies")
    workflow_dependencies = {}
    all_functions = set(input_functions + output_functions)
    all_functions = {fn.strip() for fn in all_functions if fn.strip()}
    for fn in all_functions:
        deps = st.text_area(f"Dependencies for {fn} (comma separated)").split(",")
        workflow_dependencies[fn] = [d.strip() for d in deps if d.strip()]

    st.subheader("Paths")
    num_paths = st.number_input("Number of Paths", min_value=1, value=1, step=1)
    paths = {"num_paths": num_paths}
    for i in range(num_paths):
        path = st.text_area(f"Path {i} Functions (comma separated)").split(",")
        paths[str(i)] = [p.strip() for p in path if p.strip()]

    st.subheader("Functions Definitions")
    functions = {}
    for fn in all_functions:
        st.subheader(f"Function: {fn}")
        time = st.number_input(f"{fn} - Execution Time", min_value=0, value=10)
        ram = st.number_input(f"{fn} - RAM Usage", min_value=1, value=100)
        prob_request = st.number_input(f"{fn} - Probability of Request", min_value=0.0, max_value=1.0, value=0.5)
        data_send = st.number_input(f"{fn} - Data Sent", min_value=0, value=10)

        provider = st.text_input(f"{fn} - Provider Name", key=f"provider_{fn}")
        functions[fn] = {
            "time": time,
            "ram": ram,
            "prob_request": prob_request,
            "data_send": data_send,
            "data_dependencies": {
                provider: 0
            }
        }

    if st.button("Send Workflow Configuration"):
        workflow_config = {
            "workflowBucketName": workflow_bucket,
            "deployment_number": deployment_number,
            "input_data": input_data,
            "input_functions": input_functions,
            "output_functions": output_functions,
            "workflow_dependencies": workflow_dependencies,
            "paths": paths,
            "functions": functions
        }

        with open("requirements_workflow.json", "w") as f:
            json.dump(workflow_config, f, indent=4)
        st.success("Workflow configuration saved to requirements_workflow.json!")

def main():
    st.title("☁️ Cloud & Workflow Configuration App")

    page = st.sidebar.selectbox("Choose a Page", ["Cloud Configuration", "Workflow Configuration"])

    if page == "Cloud Configuration":
        cloud_page()
    else:
        workflow_page()

if __name__ == "__main__":
    main()
