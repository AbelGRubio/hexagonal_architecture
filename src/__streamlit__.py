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

# Helper to fetch proxies from Toxiproxy and map to table rows
def fetch_proxies():
    try:
        resp = requests.get("http://localhost:8474/proxies")
        if resp.status_code == 200:
            proxies_json = resp.json()
            rows = []
            if isinstance(proxies_json, dict):
                for name, obj in proxies_json.items():
                    rows.append({
                        "Name": name,
                        "Listen": obj.get("listen"),
                        "Upstream": obj.get("upstream"),
                        "Enabled": obj.get("enabled")
                    })
            elif isinstance(proxies_json, list):
                for obj in proxies_json:
                    rows.append({
                        "Name": obj.get("name"),
                        "Listen": obj.get("listen"),
                        "Upstream": obj.get("upstream"),
                        "Enabled": obj.get("enabled")
                    })
            return rows, None
        else:
            return None, f"HTTP {resp.status_code}: {resp.text}"
    except requests.exceptions.ConnectionError:
        return None, "ConnectionError"

# Initial fetch (no side-effects)
rows, err = fetch_proxies()
if err:
    if err == "ConnectionError":
        st.error("❌ No se pudo conectar a la API de Toxiproxy en http://localhost:8474. Asegúrate de haber iniciado la infraestructura.")
    else:
        st.warning(f"⚠️ Error consultando Toxiproxy: {err}")
else:
    if rows:
        st.table(rows)
    else:
        st.info("No hay proxies configurados en Toxiproxy.")

# Initialize network_failure state from current proxy (only set once, no side-effects)
if "network_failure" not in st.session_state:
    initial_failure = False
    if rows:
        for r in rows:
            if r.get("Name") == "rabbitmq":
                initial_failure = not bool(r.get("Enabled", True))
                break
    st.session_state.network_failure = initial_failure

# Callback that runs only on user interaction with the checkbox
def _on_toggle_network_failure():
    failure = st.session_state.network_failure
    action = "disable" if failure else "enable"
    endpoint = f"http://localhost:8474/proxies/rabbitmq"
    try:
        resp = requests.post(endpoint, json={"enabled": failure})
        if resp.status_code == 200:
            st.session_state.toxiproxy_msg = ("success", f"RabbitMQ network {'down' if failure else 'restored'}")
        else:
            st.session_state.toxiproxy_msg = ("warning", f"{resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        st.session_state.toxiproxy_msg = ("error", "Could not connect to Toxiproxy API.")

    # Refresh cached rows after the action so the UI reflects the new status
    new_rows, new_err = fetch_proxies()
    st.session_state._proxies_rows = new_rows
    st.session_state._proxies_err = new_err

# Render checkbox with on_change callback; this avoids sending requests on page load
st.checkbox("💥 Enable RabbitMQ Network Failure (via Toxiproxy)", key="network_failure", on_change=_on_toggle_network_failure)

# Show any result message from the last toggle action
if "toxiproxy_msg" in st.session_state:
    level, msg = st.session_state.toxiproxy_msg
    if level == "success":
        st.success(msg)
    elif level == "warning":
        st.warning(msg)
    else:
        st.error(msg)

# Display refreshed proxies if we have them from a toggle, otherwise the initial fetch
rows = st.session_state.get("_proxies_rows", rows)
err = st.session_state.get("_proxies_err", err)
if err:
    if err == "ConnectionError":
        st.error("❌ No se pudo conectar a la API de Toxiproxy en http://localhost:8474. Asegúrate de haber iniciado la infraestructura.")
    else:
        st.warning(f"⚠️ Error consultando Toxiproxy: {err}")
else:
    if rows:
        st.table(rows)
    else:
        st.info("No hay proxies configurados en Toxiproxy.")

st.markdown("---")
st.info(
    "💡 **Tip:** Open your Docker logs or monitoring tool to observe how the application reacts to the loss of connection with RabbitMQ.")