import streamlit as st
import json
from dashboard.services.socket_manager import SocketManager

def render_command_center():
    st.divider()
    st.subheader("🚀 Command Center")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Pending Commands")

        # Ensure session state for pending commands exists
        if "pending_commands" not in st.session_state:
            st.session_state.pending_commands = []

        pending = st.session_state.pending_commands

        if not pending:
            st.info("No pending commands.")
        else:
            for idx, cmd in enumerate(pending):
                # Display command summary
                st.text(f"{idx+1}. {cmd.target_domain} / {cmd.parameter_key} -> {cmd.new_value}")

            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("Commit Batch", type="primary"):
                    socket_mgr = SocketManager()
                    for cmd in pending:
                        socket_mgr.send_command(cmd)
                    st.session_state.pending_commands = []
                    st.success(f"Batch of {len(pending)} commands sent!")
                    st.rerun()

            with col_act2:
                if st.button("Clear Queue"):
                    st.session_state.pending_commands = []
                    st.rerun()

    with col2:
        st.markdown("### Audit Log")

        # Accumulate logs in session state
        if "audit_logs" not in st.session_state:
            st.session_state.audit_logs = []

        socket_mgr = SocketManager()
        # Fetch new logs from the manager's queue
        new_logs = socket_mgr.get_audit_logs()
        st.session_state.audit_logs.extend(new_logs)

        # Keep only last 20 logs
        if len(st.session_state.audit_logs) > 20:
            st.session_state.audit_logs = st.session_state.audit_logs[-20:]

        # Display logs (newest first)
        logs = reversed(st.session_state.audit_logs)

        for log in logs:
            success = log.get("success", False)
            tick = log.get("execution_tick", "?")
            cid = str(log.get("command_id", "unknown"))[:8]
            reason = log.get("failure_reason", "Success")

            icon = "✅" if success else "❌"
            color = "green" if success else "red"

            with st.expander(f"{icon} [Tick {tick}] Command {cid}"):
                st.markdown(f"**Result**: :{color}[{reason}]")
                if "audit_report" in log and log["audit_report"]:
                    st.json(log["audit_report"])
