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
col11, col12, col13, col14, col15, col16, col17 = st.columns(7)
with col11:
    st.title("birdRISK")
with col12:
    st.subheader(" ")
with col13:
    st.image("data/img/visavis_logo.jpg")
    
st.subheader("Goal")

st.markdown(
    """
    The tool ssupports the planning and concession process for onshore and offshore wind farms by quantifying the risk for migratory birds.
    """
)



st.subheader("Different dimensions")
st.markdown(
    """
    In the visAvis project, different aspects of bird migration, such as migration intensity (exposure), flight behavior (vulnerability) and probability of landing birds (risk) will be computed and visualized. Finally a bird migration risk map is produced informing infrastructure planning and other activities.
"""
)
st.info("Click on the left sidebar menu to navigate to the different sub topics.")

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.image("data/img/migration.jpg", caption='Migration intensity')
    st.image("data/img/stopover.jpg",caption='Stopover sites')

with row1_col2:
    st.image("data/img/behaviour.jpg", caption='Local flight behaviour')
    st.image("data/img/vulnerability.jpg", caption='Vulnerability')

# Insert institutional logos at the bottom
st.markdown("---")  # Horizontal line for separation
st.subheader("Institutions involved")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.image("data/img/nina_logo.png", caption="Norwegian Institute for Nature Research", use_column_width=True)  # Replace with actual logo path

with col2:
    st.image("data/img/uoA_logo.png", caption="University of Amsterdam", use_column_width=True)  # Replace with actual logo path
