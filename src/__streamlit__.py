import streamlit as st
import requests
import subprocess
import time

st.markdown(
    """
    <style>
    .stAppDeployButton {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Page configuration
st.set_page_config(
    page_title="Resilience & Chaos Engineering Dashboard",
    page_icon="🛡️",
    layout="centered"
)

st.title("🛡️ Resilience Control Panel (Chaos Engineering)")
st.markdown("Interact with **Toxiproxy** to simulate network failures and test your system's resilience in real-time.")

st.subheader("1. Infrastructure Control")

if st.button("🚀 Start Infrastructure & App (Step by Step)", type="primary"):
    with st.spinner("Starting base services (ministack, redis, rabbitmq, toxiproxy)..."):
        # 1. Start everything except the app
        res_base = subprocess.run(
            ["docker", "compose", "up", "-d", "ministack", "redis", "rabbitmq", "toxiproxy"],
            capture_output=True, text=True
        )
        if res_base.returncode != 0:
            st.error(f"❌ Error starting base services: {res_base.stderr}")
        else:
            st.success("✅ Base services started successfully.")

    with st.spinner("Waiting for Toxiproxy to be ready and configuring the proxy to RabbitMQ..."):
        # Wait a few seconds for Toxiproxy API to launch on port 8474
        time.sleep(3)

        # 2. Configure Toxiproxy to redirect traffic from toxiproxy:5672 to rabbitmq:5672
        proxy_config = {
            "name": "rabbitmq",
            "listen": "0.0.0.0:5672",
            "upstream": "rabbitmq:5672",
            "enabled": True
        }
        try:
            # Try to create the proxy in Toxiproxy (if it already exists, the API might return a conflict)
            resp = requests.post("http://localhost:8474/proxies", json=proxy_config)
            if resp.status_code in [201, 200]:
                st.success("✅ Toxiproxy configured to forward traffic to RabbitMQ.")
            elif resp.status_code == 409:
                st.info("ℹ️ Toxiproxy proxy was already configured.")
            else:
                st.warning(f"⚠️ Unexpected response configuring Toxiproxy: {resp.text}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Toxiproxy API at http://localhost:8474. Is it running?")

    with st.spinner("Starting the application (app)..."):
        # 3. Start the application container
        res_app = subprocess.run(
            ["docker", "compose", "up", "-d", "app"],
            capture_output=True, text=True
        )
        if res_app.returncode != 0:
            st.error(f"❌ Error starting the app: {res_app.stderr}")
        else:
            st.success("🎉 All systems are up and connected through Toxiproxy!")

st.markdown("---")
st.subheader("2. Chaos Engineering: Network Failure Simulation")

# Use session_state to persist the network failure toggle state
if "network_failure" not in st.session_state:
    st.session_state.network_failure = False

# Toggle button to enable or disable the RabbitMQ network drop
failure_toggle = st.checkbox("💥 Enable RabbitMQ Network Failure (via Toxiproxy)",
                             value=st.session_state.network_failure)

if failure_toggle != st.session_state.network_failure:
    st.session_state.network_failure = failure_toggle
    enable_status = not failure_toggle  # If failure is active, proxy is disabled (enabled: False)

    try:
        response = requests.post(
            "http://localhost:8474/proxies/rabbitmq/enabled",
            json={"enabled": enable_status}
        )
        if response.status_code == 200:
            if failure_toggle:
                st.error("💥 RabbitMQ network is down! Traffic is blocked by Toxiproxy.")
            else:
                st.success("✅ RabbitMQ network restored successfully!")
        else:
            st.warning(f"⚠️ Error communicating with Toxiproxy API: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to Toxiproxy API. Make sure you started the infrastructure first.")

st.markdown("---")
st.info(
    "💡 **Tip:** Open your Docker logs or monitoring tool to observe how the application reacts to the loss of connection with RabbitMQ.")