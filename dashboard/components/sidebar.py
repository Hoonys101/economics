import streamlit as st
from dashboard.services.registry_service import RegistryService
from dashboard.services.socket_manager import SocketManager
from simulation.dtos.commands import GodCommandDTO

def render_sidebar():
    st.sidebar.title("🎮 Global Controls")

    # Connection Status
    socket_mgr = SocketManager()
    status = socket_mgr.connection_status

    color = "green" if status == "Connected" else "red"
    st.sidebar.markdown(f"**Engine Status:** :{color}[{status}]")

    # Intervention Toggle
    god_mode = st.sidebar.toggle("God Mode (Intervention)", value=False)

    st.sidebar.divider()

    if not god_mode:
        st.sidebar.info("Enable God Mode to adjust parameters.")
        return

    # Registry Service
    registry_service = RegistryService()
    metadata_list = registry_service.get_all_metadata()

    # Group by domain
    domains = sorted(list(set(m.domain for m in metadata_list)))

    if "pending_commands" not in st.session_state:
        st.session_state.pending_commands = []

    for domain in domains:
        st.sidebar.subheader(f"🏛️ {domain}")
        domain_meta = [m for m in metadata_list if m.domain == domain]

        for meta in domain_meta:
            key = f"param_{meta.key}"

            # Helper to create DTO on change
            def on_change(m=meta, k=key):
                new_val = st.session_state[k]
                cmd = GodCommandDTO(
                    target_domain=m.domain,
                    parameter_key=m.key,
                    new_value=new_val,
                    command_type="SET_PARAM"
                )
                st.session_state.pending_commands.append(cmd)
                st.toast(f"Queued: {m.key} -> {new_val}")

            # Determine initial value
            if key not in st.session_state:
                st.session_state[key] = meta.min_value

            if meta.data_type == "int":
                st.sidebar.number_input(
                    label=meta.description,
                    min_value=int(meta.min_value),
                    max_value=int(meta.max_value),
                    step=int(meta.step),
                    key=key,
                    on_change=on_change
                )
            else:
                st.sidebar.slider(
                    label=meta.description,
                    min_value=float(meta.min_value),
                    max_value=float(meta.max_value),
                    step=float(meta.step),
                    key=key,
                    on_change=on_change
                )
