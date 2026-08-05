"""
UserInterface.py

Main entry point for the KnowHow app.

Two states for the main content area:
  - Nothing connected yet: the home screen (hero + connectable source cards).
  - A source is selected: an interactive AI Knowledge Graph for that source
    (nodes = documents/projects/people/topics, edges = relationships),
    with a side panel showing details for whichever node is picked.

>>> BACKEND INTEGRATION <<<
This file never reads or builds fake data itself. Everywhere it needs
data, it asks one of these two places for it:
  - mock_data.py              -> which sources CAN be connected (the catalog)
  - integrations/registry.py  -> which sources ARE available + their module
  - <source>_module.get_graph() / get_node_detail()  -> the actual graph data
Your backend developer only ever needs to touch those files/functions.
Nothing below this docstring should need to change.

Run with:  streamlit run UserInterface.py
"""

import time

import requests
import streamlit as st
from config import settings
from integrations import registry
from knowledge_graph import render_graph
from mock_data import get_source_catalog
from style import (
    ICON_BINDER,
    ICON_CLOCK,
    ICON_EMAIL,
    ICON_GITHUB,
    ICON_GOOGLE_DRIVE,
    ICON_LOGO,
    ICON_NOTION,
    ICON_OTHER,
    ICON_SEARCH,
    ICON_UPLOAD,
    icon,
    inject_css,
    render_html,
)

# Node-type -> color, kept in one place so the legend and the graph itself

NODE_TYPE_COLORS = {
    "project": "#1E7CF2",
    "document": "#6B7280",
    "person": "#17B26A",
    "topic": "#7C3AED",
}
NODE_TYPE_ICONS = {
    "project": "📁",
    "document": "📄",
    "person": "👤",
    "topic": "🏷️",
}

# =============================================
# API CALLS
# =============================================

API_URL="http://localhost:8000/api/graph/all"

def get_graph_info():
    res = requests.get(API_URL, headers={"Authorization": f"Bearer {settings.dev_token}"}, timeout=(5,60))      # 5 seconds to establish connection, 60 for response
    return res.json()

# =============================================
# END OF API CALLS
# =============================================

st.set_page_config(
    page_title="KnowHow / Knowledge Base",
    page_icon="🗂️",
    layout="wide",
)

inject_css()


# This section initializes the shared session values that keep the selected source and node state stable across reruns.
st.session_state.setdefault("connected_sources", {})
st.session_state.setdefault("selected_source", None)
st.session_state.setdefault("selected_node", None)


# The top bar adds the app branding, search box, and connection button in one compact header.

top_left, top_mid, top_right = st.columns([1.4, 3, 1.3], vertical_alignment="center")

with top_left:
    render_html(f'<div class="brand">{icon(ICON_LOGO, 26)} KnowHow</div>')

with top_mid:
    search_col1, search_col2 = st.columns([0.06, 0.94])
    with search_col1:
        render_html(f'<div style="padding-top:9px;color:#9CA3AF;">{icon(ICON_SEARCH, 18)}</div>')
    with search_col2:
        st.text_input(
            "Search Knowledge",
            placeholder="Search Knowledge",
            label_visibility="collapsed",
            key="search_knowledge",
        )

with top_right:
    st.button("＋ Connect Source", type="primary", use_container_width=True, key="connect_source_top")

render_html("<div style='border-bottom:1px solid #E4E4E7; margin: 8px 0 6px 0;'></div>")


# The sidebar lists the connected sources and lets the user switch between them without leaving the main view.

SOURCE_ICON_MAP = {
    "notion": ICON_NOTION,
    "email": ICON_EMAIL,
    "gmail": ICON_EMAIL,
    "github": ICON_GITHUB,
    "upload": ICON_UPLOAD,
    "other": ICON_OTHER,
    "google_drive": ICON_GOOGLE_DRIVE,
}

with st.sidebar:
    render_html('<div class="folders-label">Sources</div>')

    connected_ids = [sid for sid, on in st.session_state["connected_sources"].items() if on]

    if not connected_ids:
        render_html(
            f"""
            <div class="empty-illustration">
                {ICON_BINDER}
                <div class="headline">Nothing connected yet</div>
                <div class="subline">Connect a source to create your knowledge graph.</div>
            </div>
            """
        )
    else:
        for sid in connected_ids:
            src = registry.get_source(sid)
            if not src:
                continue
            is_selected = st.session_state["selected_source"] == sid
            clicked = st.button(
                src["name"],
                key=f"select_source_{sid}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            )
            if clicked:
                st.session_state.selected_source = sid
                st.session_state.selected_node = None
                st.rerun()


# This section handles the connection workflow for each source and shows a friendly loading state while the backend finishes its setup work.
# It also keeps the UI consistent for sources that are not fully connected yet.

def render_idle_card_html(source, svg_icon):
    return f"""
        <div class="source-card" style="text-align:center;">
            <div style="display:flex;justify-content:center;color:inherit;margin-bottom:8px;">
                {icon(svg_icon, 24)}
            </div>
            <div class="name">{source['name']}</div>
            <div class="dots">· · · · · · ·</div>
        </div>
    """


def run_connect_animation(placeholder, module):
    """Runs a source module's connect() flow, updating `placeholder` live
    as each stage completes. Every source module is expected to accept the
    same progress_callback(label, percent) signature — see
    integrations/base.py for the contract."""

    def show_step(label, percent):
        render_html(
            f"""
            <div class="connecting-wrap">
                <div class="db-spinner"></div>
                <div class="connecting-label">{label}</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width:{percent}%;"></div>
                </div>
            </div>
            """,
            target=placeholder,
        )

    return module.connect(progress_callback=show_step)


def render_source_card(source):
    """One card on the home screen. If the source has a working module
    (registry "available": True), clicking Connect runs its real connect
    flow. Otherwise it's a friendly placeholder — this is intentional so
    the UI never pretends a source works before the backend exists."""
    src_meta = registry.get_source(source["id"])
    svg_icon = SOURCE_ICON_MAP.get(source["icon"], ICON_CLOCK)

    with st.container(border=True):
        placeholder = st.empty()
        render_html(render_idle_card_html(source, svg_icon), target=placeholder)

        already_connected = st.session_state["connected_sources"].get(source["id"], False)

        if already_connected:
            st.button("Connected ✓", key=f"card_{source['id']}", use_container_width=True, disabled=True)
        elif src_meta and src_meta["available"]:
            if st.button("Connect", key=f"card_{source['id']}", use_container_width=True):
                result = run_connect_animation(placeholder, src_meta["module"])
                st.session_state["connected_sources"][source["id"]] = True
                st.session_state.selected_source = source["id"]
                st.session_state.selected_node = None
                st.rerun()
        else:
            if st.button("Connect", key=f"card_{source['id']}", use_container_width=True):
                st.toast(f"{source['name']} isn't wired up to a backend yet — coming soon.")


# The home screen presents the welcome hero and the source cards that users can connect from a single place.

def render_home_screen():
    render_html(
        """
        <div class="hero">
            <h1>Give your AI the context it needs</h1>
            <p>KnowHow connects your scattered company knowledge into a single,
            AI-ready structure. Start by linking your first data source.</p>
        </div>
        """
    )

    sources = get_source_catalog()
    st.write("")

    # Renders in rows of 3 automatically — add a 9th, 10th, etc. source to
    # mock_data.SOURCE_CATALOG and it just flows into a new row, no layout
    # changes needed.
    for row_start in range(0, len(sources), 3):
        row = sources[row_start:row_start + 3]
        cols = st.columns(3, gap="medium")
        for col, src in zip(cols, row):
            with col:
                render_source_card(src)
        st.write("")

    render_html('<div class="connect-all-wrap">')
    btn_col1, btn_col2, btn_col3 = st.columns([1.3, 1, 1.3])
    with btn_col2:
        st.button("＋ Connect All Sources", type="primary", use_container_width=True, key="connect_all")
    render_html("</div>")


# This section renders the graph view for a selected source and displays the node details panel when the user clicks a node.

def render_graph_legend():
    items = "".join(
        f"""
        <div class="legend-item">
            <span class="legend-dot" style="background:{color};"></span>
            {NODE_TYPE_ICONS.get(t, '')} {t.title()}
        </div>
        """
        for t, color in NODE_TYPE_COLORS.items()
    )
    render_html(f'<div class="legend-row">{items}</div>')


def render_node_detail_panel(node_detail):
    color = NODE_TYPE_COLORS.get(node_detail["type"], "#111111")
    meta = node_detail.get("meta", {})

    render_html(
        f"""
        <div class="detail-title">{node_detail['label']}</div>
        <div class="detail-type-pill" style="background:{color}22; color:{color};">
            {node_detail['type'].title()}
        </div>
        """
    )

    if meta.get("excerpt"):
        render_html(f'<div class="detail-desc">{meta["excerpt"]}</div>')

    field_rows = "".join(
        f"""
        <div class="detail-field">
            <div class="detail-field-label">{label}</div>
            <div class="detail-field-value">{value}</div>
        </div>
        """
        for label, value in [
            ("Author", meta.get("author")),
            ("Last Updated", meta.get("last_edited_at")),
            ("Collection", meta.get("collection")),
            ("Role", meta.get("role")),
        ]
        if value
    )
    if field_rows:
        render_html(f'<div class="section-block"><div class="section-heading">Details</div>{field_rows}</div>')

    related = node_detail.get("related", [])
    if related:
        rel_rows = "".join(
            f"""
            <div class="related-item">
                <span class="rel-label">{r['label']}</span>
                <span class="rel-relation"> — {r['relation']}</span>
            </div>
            """
            for r in related
        )
        render_html(
            f'<div class="section-block"><div class="section-heading">Connections</div>{rel_rows}</div>'
        )


def render_graph_view(source_id):
    src_meta = registry.get_source(source_id)
    if not src_meta or not src_meta["module"]:
        st.warning("This source has no data module connected.")
        return

    module = src_meta["module"]

    render_html(
        f"""
        <div class="source-header">
            <div class="source-header-title">{src_meta['name']} Knowledge Graph</div>
        </div>
        <div class="source-header-meta">AI-organized view of everything pulled from {src_meta['name']}.</div>
        """
    )

    # This small loading state makes the graph feel more responsive while the selected source is being prepared.
    loading_key = f"graph_loaded_{source_id}"
    if not st.session_state.get(loading_key):
        loading_ph = st.empty()
        render_html(
            """
            <div class="graph-loading-wrap">
                <div class="connecting-wrap">
                    <div class="db-spinner"></div>
                    <div class="connecting-label">Laying out the knowledge graph...</div>
                </div>
            </div>
            """,
            target=loading_ph,
        )
        time.sleep(0.5)
        loading_ph.empty()
        st.session_state[loading_key] = True

    graph = get_graph_info()  # <-- BACKEND SWAP POINT: real API call goes here eventually

    render_graph_legend()

    graph_col, detail_col = st.columns([2.3, 1], gap="large")

    with graph_col:
        clicked_node_id = render_graph(graph, height=520)
        if clicked_node_id:
            st.session_state.selected_node = clicked_node_id

        st.caption("Drag to explore, scroll to zoom. Click a node to see its details and connections →")

        if st.button("Disconnect " + src_meta["name"], key=f"disconnect_{source_id}"):
            module.disconnect()  # <-- BACKEND SWAP POINT: real token revocation goes here eventually
            st.session_state["connected_sources"][source_id] = False
            st.session_state.selected_source = None
            st.session_state.selected_node = None
            st.session_state.pop(loading_key, None)
            st.rerun()

    with detail_col:
        node_id = st.session_state.get("selected_node")
        if node_id:
            detail = module.get_node_detail(node_id)  # <-- BACKEND SWAP POINT
            if detail:
                render_node_detail_panel(detail)
        else:
            render_html(
                '<div class="detail-field-value">Pick a node above to see its details and connections.</div>'
            )


# The main content switches between the welcome screen and the graph experience based on whether a source is currently selected.

selected = st.session_state.get("selected_source")
if selected and st.session_state["connected_sources"].get(selected):
    render_graph_view(selected)
else:
    render_home_screen()
