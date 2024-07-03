import streamlit as st
import leafmap.foliumap as leafmap
import geemap.foliumap as geemap

#def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
#geemap.ee_initialize(token_name=EARTHENGINE_TOKEN)
#geemap.ee_initialize()

st.set_page_config(layout="wide")

st.sidebar.info(
    """
    - Web App URL: <https://streamlit.geemap.org>
    - GitHub repository: <https://github.com/NINAnor/birdRisk>
    """
)

st.sidebar.title("Contact")
st.sidebar.info(
    """
    Reto Spielhofer: <https://www.nina.no>
    Frank Hanssen
    #VisAviS2024
    based on a repository of:
    Qiusheng Wu: [GitHub](https://github.com/giswqs) 
    """
)

st.title("birdRISK")

st.markdown(
    """
    The tool should be designed to support the planning and concession process for onshore and offshore wind farms. In particular, migration intensity (exposure), flight behavior (vulnerability) and probability of landing birds (risk) will be computed and visualized.

    """
)

st.info("Click on the left sidebar menu to navigate to the different apps.")

st.subheader("Timelapse of Satellite Imagery")
st.markdown(
    """
    Some placeholder stuff
"""
)

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.image("https://github.com/giswqs/data/raw/main/timelapse/spain.gif")
    st.image("https://github.com/giswqs/data/raw/main/timelapse/las_vegas.gif")

with row1_col2:
    st.image("https://github.com/giswqs/data/raw/main/timelapse/goes.gif")
    st.image("https://github.com/giswqs/data/raw/main/timelapse/fire.gif")