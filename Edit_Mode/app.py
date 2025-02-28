import streamlit as st

st.set_page_config(layout="wide")

page_nav_bar = st.Page(
    "./nav_bar.py",
    url_path="nav-bar",
)

page_setup = st.Page(
    "./set_up_chart.py",
    url_path="set-up-chart",
)


nav = st.navigation(
    [
        page_nav_bar,
        page_setup,
    ],
    position="hidden",
)

nav.run()
