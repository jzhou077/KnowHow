"""
style.py

Shared CSS + small SVG icon helpers so every page in the app looks
consistent. Import `inject_css()` at the top of each page.
"""

import re
import streamlit as st


ACCENT = "#1E7CF2"
ACCENT_DARK = "#0F62D6"
INK = "#111111"
SUBTLE = "#6B7280"
BORDER = "#E4E4E7"
BG = "#FFFFFF"
CARD_BG = "#FFFFFF"


def render_html(html: str, target=None):
    """
    Renders an HTML string safely.

    Why this exists: Markdown's spec treats any line starting with 4+
    spaces of indentation as a preformatted code block, which would
    otherwise cause st.markdown() to print raw tags instead of rendering
    them. This collapses all whitespace before handing the string off, so
    it always renders correctly regardless of how it's formatted in the
    source code.

    Usage:
        render_html("<div>...</div>")                       # writes to the page
        render_html("<div>...</div>", target=placeholder)   # writes into a placeholder
    """
    compact = re.sub(r"\s+", " ", html.strip())
    compact = re.sub(r">\s+<", "><", compact)
    sink = target if target is not None else st
    sink.markdown(compact, unsafe_allow_html=True)


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        html, body, main, section, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stSidebar"], .block-container {{
            background-color: {BG} !important;
            background-image: none !important;
            color-scheme: light !important;
        }}

        #MainMenu, footer, header {{visibility: hidden;}}
        div[data-testid="stToolbar"] {{visibility: hidden;}}
        div[data-testid="stDecoration"] {{display: none;}}
        div[data-testid="stStatusWidget"] {{display: none;}}

        iframe[title="streamlit_agraph.agraph"] {{
            background-color: #FFFFFF;
        }}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {BG};
            border-right: 1px solid {BORDER};
        }}

        /* ---------- Top bar ---------- */
        .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.5rem;
            font-weight: 700;
            color: {INK};
            letter-spacing: -0.02em;
        }}
        .brand svg {{
            width: 28px;
            height: 28px;
            flex-shrink: 0;
        }}

        /* ---------- Sidebar: empty state ---------- */
        .folders-label {{
            font-weight: 600;
            font-size: 0.95rem;
            color: {INK};
            margin: 4px 0 20px 0;
        }}
        .empty-illustration {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            margin-top: 24px;
            padding: 12px 8px 0;
            gap: 8px;
        }}
        .empty-illustration svg {{
            width: 140px;
            height: auto;
            opacity: 0.95;
        }}
        .empty-illustration .headline {{
            font-weight: 700;
            font-size: 0.95rem;
            color: {INK};
            line-height: 1.3;
        }}
        .empty-illustration .subline {{
            font-size: 0.86rem;
            color: {SUBTLE};
            line-height: 1.5;
            max-width: 180px;
        }}

        /* ---------- Sidebar: connected sources list ---------- */
        section[data-testid="stSidebar"] .stButton > button {{
            all: unset;
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            box-sizing: border-box;
            padding: 9px 10px;
            font-size: 0.88rem;
            font-weight: 500;
            color: {INK};
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 2px;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: #F4F6FA;
        }}
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: #EAF2FF;
            color: {ACCENT};
            font-weight: 700;
        }}
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] p {{
            color: {ACCENT};
        }}

        /* ---------- Hero ---------- */
        .hero {{
            text-align: center;
            padding: 38px 0 8px 0;
        }}
        .hero h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            color: {INK};
            letter-spacing: -0.03em;
            margin-bottom: 14px;
        }}
        .hero p {{
            font-size: 1.02rem;
            color: {SUBTLE};
            max-width: 560px;
            margin: 0 auto;
            line-height: 1.55;
        }}

        /* ---------- Source cards (home screen) ---------- */
        .source-card {{
            border: 1px solid {BORDER};
            border-radius: 14px;
            background: {CARD_BG};
            padding: 22px 16px 18px 16px;
            text-align: center;
            transition: all 0.15s ease;
            height: 100%;
        }}
        .source-card svg {{
            width: 26px;
            height: 26px;
            margin-bottom: 10px;
        }}
        .source-card .name {{
            font-weight: 700;
            font-size: 1rem;
            color: {INK};
            margin-bottom: 8px;
        }}
        .source-card .dots {{
            color: {BORDER};
            letter-spacing: 2px;
            font-size: 0.9rem;
        }}

        /* ---------- Buttons ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"] button {{
            width: 100%;
        }}
        .stButton > button {{
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid {BORDER};
            transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }}
        .stButton > button:not([kind="primary"]) {{
            color: {INK};
            background-color: #FFFFFF;
        }}
        .stButton > button:not([kind="primary"]):hover {{
            background-color: {ACCENT};
            border-color: {ACCENT};
            color: #FFFFFF;
        }}
        .stButton > button[kind="primary"] {{
            background-color: {ACCENT};
            border: none;
            color: #FFFFFF;
        }}
        .stButton > button[kind="primary"] p {{
            color: #FFFFFF;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {ACCENT_DARK};
            border-color: {ACCENT_DARK};
        }}

        /* Search input */
        div[data-testid="stTextInput"] input {{
            border-radius: 999px !important;
            border: 1px solid {BORDER} !important;
            padding: 10px 18px !important;
        }}
        div[data-testid="stTextInput"] input:focus {{
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 3px rgba(30, 124, 242, 0.15) !important;
        }}

        .connect-all-wrap {{
            display: flex;
            justify-content: center;
            margin-top: 30px;
        }}

        /* ---------- Connecting animation (Notion connect + graph loading) ---------- */
        .connecting-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 14px 6px 4px;
            text-align: center;
        }}
        .db-spinner {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 3px solid {BORDER};
            border-top-color: {ACCENT};
            animation: db-spin 0.8s linear infinite;
            margin-bottom: 12px;
        }}
        @keyframes db-spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .connecting-label {{
            font-size: 0.82rem;
            font-weight: 600;
            color: {INK};
            margin-bottom: 10px;
            min-height: 18px;
        }}
        .progress-track {{
            width: 100%;
            height: 6px;
            border-radius: 999px;
            background: {BORDER};
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: {ACCENT};
            transition: width 0.4s ease;
        }}
        .graph-loading-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 300px;
            border: 1px solid {BORDER};
            border-radius: 14px;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        /* ---------- Source header (above the graph) ---------- */
        .source-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        }}
        .source-header-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: {INK};
        }}
        .source-header-meta {{
            font-size: 0.82rem;
            color: {SUBTLE};
            margin-bottom: 16px;
        }}

        /* ---------- Node legend ---------- */
        .legend-row {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin: 10px 0 16px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78rem;
            color: {SUBTLE};
        }}
        .legend-dot {{
            width: 9px;
            height: 9px;
            border-radius: 3px;
            flex-shrink: 0;
        }}

        /* ---------- Node detail panel (right side, shown when a node is picked) ---------- */
        .detail-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {ACCENT};
            margin-bottom: 4px;
            line-height: 1.3;
        }}
        .detail-type-pill {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 2px 9px;
            border-radius: 999px;
            margin-bottom: 10px;
        }}
        .detail-desc {{
            font-size: 0.88rem;
            color: {INK};
            line-height: 1.6;
            margin-bottom: 4px;
        }}
        .section-block {{
            margin-top: 22px;
        }}
        .section-heading {{
            font-size: 0.95rem;
            font-weight: 700;
            color: {INK};
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid {BORDER};
        }}
        .detail-field {{
            margin-bottom: 12px;
        }}
        .detail-field-label {{
            font-size: 0.82rem;
            font-weight: 700;
            color: {INK};
            margin-bottom: 2px;
        }}
        .detail-field-value {{
            font-size: 0.8rem;
            color: {SUBTLE};
        }}
        .related-item {{
            padding: 7px 0;
            border-top: 1px solid #F1F1F3;
            font-size: 0.8rem;
        }}
        .related-item:first-of-type {{
            border-top: none;
        }}
        .related-item .rel-label {{
            font-weight: 600;
            color: {INK};
        }}
        .related-item .rel-relation {{
            color: {SUBTLE};
            font-size: 0.74rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# These inline SVG icons provide the app's visual symbols without relying on any external image files.

ICON_LOGO = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
  <rect x="9" y="9" width="6" height="6" rx="1"/>
  <rect x="4" y="4" width="16" height="16" rx="2"/>
  <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>
</svg>
"""

ICON_SEARCH = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <circle cx="11" cy="11" r="7"/>
  <path d="M21 21l-4.3-4.3"/>
</svg>
"""

ICON_CLOCK = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
  <circle cx="12" cy="12" r="9"/>
  <path d="M12 7v5l3 2"/>
</svg>
"""

ICON_EMAIL = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="5" width="18" height="14" rx="2.5" fill="#EA4335"/>
  <path d="M4 7.2 12 12.8 20 7.2" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M4 7.2 12 12.8 20 7.2" stroke="#F2C94C" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
</svg>
"""

ICON_NOTION = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="4" y="4" width="16" height="16" rx="3" fill="#000000"/>
  <path d="M8 7.5h4.2l3.3 3.2v6.8a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V8.5a1 1 0 0 1 1-1Z" fill="#FFFFFF"/>
  <path d="M8 9h3.2" stroke="#000000" stroke-width="1.1" stroke-linecap="round"/>
  <path d="M8 12.2h3" stroke="#000000" stroke-width="1.1" stroke-linecap="round"/>
  <path d="M8 15.5h3.2" stroke="#000000" stroke-width="1.1" stroke-linecap="round"/>
</svg>
"""

ICON_GITHUB = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.5.5.09.66-.22.66-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.15-1.11-1.46-1.11-1.46-.91-.62.07-.61.07-.61 1.01.07 1.54 1.04 1.54 1.04.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.8c.85 0 1.71.12 2.51.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.69-4.57 4.94.36.31.68.93.68 1.87v2.77c0 .27.16.58.67.48A10.01 10.01 0 0 0 22 12c0-5.52-4.48-10-10-10Z" fill="#24292F"/>
</svg>
"""

ICON_UPLOAD = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 3v13" stroke="#2563EB" stroke-width="2" stroke-linecap="round"/>
  <path d="m7 8 5-5 5 5" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="#111827" stroke-width="2" stroke-linecap="round"/>
</svg>
"""

ICON_OTHER = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="m12 3 1.6 4.7L18 9.4l-4.4 1.7L12 15.8l-1.6-4.7L6 9.4l4.4-1.7L12 3Z" fill="#7C3AED"/>
</svg>
"""

ICON_GOOGLE_DRIVE = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M8.1 3.5h7.8l6.1 10.6-3.9 6.9H12l-3.9-6.9L8.1 3.5Z" fill="#FBBC05" opacity="0.001"/>
  <path d="M8.1 3.5 2 14.1l3.9 6.9L12 10.4 8.1 3.5Z" fill="#0066DA"/>
  <path d="M12 10.4 18.1 21h3.9l-3.9-6.9-6.1-10.6L8.9 8.4 12 10.4Z" fill="#00AC47"/>
  <path d="M5.9 21h12.2l3.9-6.9H2L5.9 21Z" fill="#FFBA00"/>
</svg>
"""

ICON_PLUS = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
  <path d="M12 5v14M5 12h14"/>
</svg>
"""

ICON_BINDER = """
<svg viewBox="0 0 160 130" fill="none" xmlns="http://www.w3.org/2000/svg">
  <g transform="rotate(-8 80 65)">
    <rect x="30" y="10" width="90" height="110" rx="4" fill="#F4F4F5" stroke="#D4D4D8" stroke-width="2"/>
    <rect x="30" y="10" width="18" height="110" rx="4" fill="#E4E4E7" stroke="#D4D4D8" stroke-width="2"/>
    <circle cx="39" cy="32" r="3" fill="#A1A1AA"/>
    <circle cx="39" cy="65" r="3" fill="#A1A1AA"/>
    <circle cx="39" cy="98" r="3" fill="#A1A1AA"/>
    <rect x="56" y="24" width="56" height="4" rx="2" fill="#E4E4E7"/>
    <rect x="56" y="36" width="40" height="4" rx="2" fill="#E4E4E7"/>
  </g>
</svg>
"""


def icon(svg: str, size: int = 22) -> str:
    """Returns an inline-styleable <span> wrapper around an svg string."""
    return f'<span style="display:inline-flex;width:{size}px;height:{size}px;">{svg}</span>'
