import streamlit as st
import leafmap.foliumap as leafmap
import geemap.foliumap as geemap

#def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
#geemap.ee_initialize(token_name=st.secrets["EARTHENGINE_TOKEN"])
#geemap.ee_initialize()

st.set_page_config(layout="wide")



st.sidebar.title("Contact")
st.sidebar.info(
    """
    Reto Spielhofer: <https://www.nina.no>
    Frank Hanssen
    #VisAviS2024
    """
)

st.title("birdRISK")

st.markdown(
    """
    The tool should be designed to support the planning and concession process for onshore and offshore wind farms.
    """
)

st.info("Click on the left sidebar menu to navigate to the different sub topics.")

st.subheader("Different dimensions")
st.markdown(
    """
    In the visAvis project, different aspects of bird migration, such as migration intensity (exposure), flight behavior (vulnerability) and probability of landing birds (risk) will be computed and visualized. Finally a bird migration risk map is produced informing infrastructure planning and other activities.
"""
)

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.image("data/img/migration.jpg", caption='Migration intensity')
    st.image("data/img/stopover.jpg",caption='Stopover sites')

with row1_col2:
    st.image("data/img/behaviour.jpg", caption='Local flight behaviour')
    st.image("data/img/vulnerability.jpg", caption='Vulnerability')
