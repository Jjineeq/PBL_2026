"""Shared st.markdown(unsafe_allow_html=True) wrapper.

See components/landing.py's module docstring for the full rationale:
each line must be stripped of leading whitespace, and a whole section's
HTML (wrapper + children) must go through ONE call, or Streamlit's
per-call DOM isolation silently breaks CSS grid/flex layouts and
CommonMark can misparse indented nested lines as code blocks.
"""

import streamlit as st


def md(html: str):
    lines = [line.lstrip() for line in html.strip("\n").splitlines()]
    st.markdown("\n".join(lines), unsafe_allow_html=True)
