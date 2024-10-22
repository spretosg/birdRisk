# streamlit_app.py

import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

## the developer branch

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.


sql = """SELECT * FROM `visavis-312202.wp4_dev.radar_sites` """
df = client.query_and_wait(sql).to_dataframe()


def create_geodataframe(df):
    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude, crs="EPSG:4326"))
    return gdf

def create_map(gdf):
    # Initialize a map centered at the mean location
    m = folium.Map()

    # Add points to the map
    for _, row in gdf.iterrows():
        folium.Marker(location=[row.geometry.y, row.geometry.x],icon=folium.Icon(icon='cloud', color='blue')).add_to(m)
        
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])


    return m


# Print results.
st.title("Radar stations")
st.write("Test to connect from google cloud BigQuery")
st.dataframe(df)
gdf = create_geodataframe(df)


folium_map = create_map(gdf)
st_folium(folium_map, width=700, height=500)

    