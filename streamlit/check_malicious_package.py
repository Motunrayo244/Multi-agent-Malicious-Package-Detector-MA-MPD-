import streamlit as st
import requests
import pandas as pd
import json
import os

st.set_page_config(
    page_title="MA-MPD: Multi-Agent Malicious Package Detection", page_icon="🛡️", layout="centered"
)

st.title("MA-MPD: Multi-Agent Malicious Package Detection")




classification_results = st.session_state.get("classification_results", pd.DataFrame(columns=["package_name", "package_version", "classification", "justification", "suspicious_files", "package_metadata"]))

# Get API URL from environment variable or default to localhost
API_URL = os.getenv("API_URL", "http://localhost:8000")

# model_choice = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-4-1", "gemini-2.0-flash"])

package_name = st.text_input("Enter Package Name")
version = st.text_input("Enter Version")

upload_file = st.file_uploader("Upload Package", type=["tar.gz", "zip", "py"])


if st.button("Check Package", type="primary", use_container_width=True):
    response = requests.post(
        f"{API_URL}/classify", 
        files={"upload_file": upload_file} if upload_file else None,
        data={"package_name": package_name, "version": version, "model_choice": model_choice}
    )
    result_data = response.json()
    if response.status_code == 200:
        package_name = package_name if package_name else result_data["package_name"]
        package_version = version if version else result_data["package_metadata"]["package_version"]
        result_data["package_name"] = package_name
        result_data["package_version"] = package_version
        classification_results = pd.concat([classification_results, pd.DataFrame(result_data)], ignore_index=True)
        st.session_state["classification_results"] = classification_results
    else:
        st.error(f"Failed to classify package: {response.status_code} {response.text}")
        
st.dataframe(classification_results)
    