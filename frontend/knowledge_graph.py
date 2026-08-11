"""
knowledge_graph.py


"""

from streamlit_agraph import agraph, Node, Edge, Config

NODE_COLORS = {
    # People — green
    "person":        "#34D399",
    "team":          "#059669",

    # Work in flight — blue
    "project":       "#4C9AFF",
    "initiative":    "#1D4ED8",
    "actionitem":    "#93C5FD",

    # Technical things — cyan
    "system":        "#0E7490",
    "tool":          "#22D3EE",

    # Rules and how-we-do-it — purple
    "policy":        "#6D28D9",
    "process":       "#A78BFA",
    "requirement":   "#C4B5FD",

    # Points in time — pink
    "decision":      "#DB2777",
    "meeting":       "#F9A8D4",

    # Needs attention — warm
    "risk":          "#EF4444",
    "openquestion":  "#F59E0B",

    # Supporting reference — neutral
    "metric":        "#57534E",
    "term":          "#8A837C",
}

LABEL_FONT_COLOR = "#1F1E1E"   # light text, readable on the dark canvas
EDGE_LABEL_COLOR = "#8B8F98"

def shorten_text(text, limit=14):
    return text if len(text) <= 14 else text[:limit-1] + "..."

def render_graph(graph: dict, height: int = 560):
    """
    Renders the graph and returns the clicked node's id (str), or None if
    nothing has been clicked yet this run.
    """
    nodes = [
        Node(
            id=node["uuid"],
            label=shorten_text(node["name"]),
            # size=24 if node["type"] in ("project", "document") else 17,
            color=NODE_COLORS.get(node["labels"][0].lower() if len(node["labels"]) > 0 else None, "#B8BCC4"),
            # color="#FF7171",
            widthConstraint={"minimum": 45, "maximum": 45},
            heightConstraint={"minimum": 45, "valign": "middle"},
            shape="circle",
            font={"color": LABEL_FONT_COLOR, "size": 10, "face": "Inter, sans-serif"},
        )
        for node in graph["entities"]
    ]

    edges = [
        Edge(
            source=edge["source_uuid"], 
            target=edge["target_uuid"], 
            color="#4B4F58", 
            label=edge["relation"], 
            font={
                "align": "top", 
                "size": 8,
                "strokeWidth": 0,
                "color": "#B3B3B3"
            }
        )
        for edge in graph["facts"]
    ]

    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#1E7CF2",
        collapsible=False,
        node={"labelProperty": "label", "renderLabel": True},
        # Edge relation labels ("authored", "about", etc.) are shown in the
        # detail panel when a node is clicked instead of inline on the
        # graph — with 20+ edges, inline labels overlapped badly and made
        # the whole graph unreadable.
        link={"renderLabel": False},
    )

    return agraph(nodes=nodes, edges=edges, config=config)
