"""Shared page chrome: CSS + scroll-reveal/progress-bar JS injection.

Every page (main.py, pages/*) calls these so the glassmorphism theme and
scroll behaviour stay identical across the app.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ASSETS = Path(__file__).parent.parent / "assets"


def load_css():
    css = (ASSETS / "css" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def load_scroll_reveal():
    js = (ASSETS / "js" / "scroll_reveal.js").read_text(encoding="utf-8")
    components.html(f"<script>{js}</script>", height=0, width=0)


def inject_top_markers():
    st.markdown('<div id="top"></div><div id="scroll-progress"></div>', unsafe_allow_html=True)
