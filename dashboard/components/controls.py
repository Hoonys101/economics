import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from dashboard.services.registry_service import RegistryService
from dashboard.dtos import ParameterSchemaDTO
from simulation.dtos.commands import GodCommandDTO

logger = logging.getLogger(__name__)

def render_dynamic_controls(container=None, use_tabs=True):
    """
    Renders dynamic UI controls based on registry schema.
    Handles user interaction and queues GodCommandDTOs.
    """
    parent = container if container else st

    # 1. Load Schema
    registry_service = RegistryService()
    schemas: List[ParameterSchemaDTO] = registry_service.get_all_metadata()

    if not schemas:
        parent.info("No registry schema loaded.")
        return

    # 2. Get Telemetry (Current State)
    telemetry = st.session_state.get("telemetry_buffer", {})
    registry_data = telemetry.get("registry", {})

    # 3. Group by Category
    categories = sorted(list(set(s.category for s in schemas)))

    if use_tabs:
        tabs = parent.tabs([f"🏛️ {c}" for c in categories])
        for i, category in enumerate(categories):
            with tabs[i]:
                _render_category_content(category, schemas, registry_data)
    else:
        for category in categories:
            with parent.expander(f"🏛️ {category}", expanded=True):
                _render_category_content(category, schemas, registry_data)

def _render_category_content(category: str, schemas: List[ParameterSchemaDTO], registry_data: Dict[str, Any]):
    cat_schemas = [s for s in schemas if s.category == category]
    for schema in cat_schemas:
        _render_widget(schema, registry_data)

def _render_widget(schema: ParameterSchemaDTO, registry_data: Dict[str, Any]):
    """
    Renders a single widget for a parameter.
    """
    key = schema.key
    label = schema.label
    desc = schema.description
    unit = getattr(schema, 'unit', '')

    ui_key = f"ui_{key}"

    # Resolve current value from registry (Telemetry)
    current_val = registry_data.get(key)

    # Fallback logic for flat keys not in registry data (simulated)
    if current_val is None:
         parts = key.split('.')
         if len(parts) > 1 and parts[0] in registry_data:
             root = registry_data[parts[0]]
             if isinstance(root, dict) and parts[1] in root:
                 current_val = root[parts[1]]

    # Mismatch Handling: If value not found, mark as missing
    is_missing = (current_val is None)
    if is_missing:
         current_val = schema.min_value # Fallback default
         label = f"{label} (⚠️ N/A)"

    # Append unit to label
    if unit:
        label = f"{label} [{unit}]"

    # Initial value logic (Sync with session state)
    if ui_key not in st.session_state:
        st.session_state[ui_key] = current_val
    else:
        # Sync logic: If not pending (user interaction), update from telemetry
        pending_keys = {cmd.parameter_key for cmd in st.session_state.get("pending_commands", [])}
        if key not in pending_keys and not is_missing:
             if current_val != st.session_state[ui_key]:
                 st.session_state[ui_key] = current_val

    # Lock logic
    is_god_mode = st.session_state.get("god_mode_active", False)
    # If missing, force disable
    is_locked = (not is_god_mode) or is_missing

    # Widget Generation
    widget_type = schema.widget_type

    def on_change():
        new_val = st.session_state[ui_key]

        cmd = GodCommandDTO(
            target_domain=schema.category,
            parameter_key=key,
            new_value=new_val,
            command_type="SET_PARAM"
        )

        if "pending_commands" not in st.session_state:
            st.session_state["pending_commands"] = []

        # Deduplicate
        st.session_state["pending_commands"] = [
            c for c in st.session_state["pending_commands"]
            if c.parameter_key != key
        ]
        st.session_state["pending_commands"].append(cmd)

        st.toast(f"Queued: {label} -> {new_val}")

    col1, col2 = st.columns([0.9, 0.1])

    with col1:
        if widget_type == "slider":
            st.slider(
                label=label,
                min_value=float(schema.min_value),
                max_value=float(schema.max_value),
                step=float(schema.step) if schema.step else 0.1,
                key=ui_key,
                on_change=on_change,
                help=desc,
                disabled=is_locked
            )
        elif widget_type == "number_input":
            st.number_input(
                label=label,
                min_value=float(schema.min_value),
                max_value=float(schema.max_value),
                step=float(schema.step) if schema.step else 1.0,
                key=ui_key,
                on_change=on_change,
                help=desc,
                disabled=is_locked
            )
        elif widget_type == "toggle":
            st.toggle(
                label=label,
                key=ui_key,
                on_change=on_change,
                help=desc,
                disabled=is_locked
            )

    with col2:
        if is_locked:
            st.markdown("🔒")
