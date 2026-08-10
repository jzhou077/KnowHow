"""
knowledge_graph.py


"""

from streamlit_agraph import agraph, Node, Edge, Config

# Tuned to be legible on streamlit-agraph's dark canvas. "document" is
# intentionally NOT near-black here (it would vanish against the dark
# background) even though it uses INK elsewhere in the app.
NODE_COLORS = {
    "project": "#4C9AFF",
    "document": "#B8BCC4",
    "person": "#36D399",
    "topic": "#C084FC",
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
            # color=NODE_COLORS.get(node["type"], "#B8BCC4"),
            color="#FF7171",
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
