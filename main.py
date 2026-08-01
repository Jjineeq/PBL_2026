import streamlit as st

from components import landing
from components.theme import inject_top_markers, load_css, load_scroll_reveal

st.set_page_config(
    page_title="AI Hospital · 자율주행 안전 관제 시스템",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
inject_top_markers()
landing.render()
load_scroll_reveal()
