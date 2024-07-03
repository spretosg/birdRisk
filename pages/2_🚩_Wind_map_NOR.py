import streamlit as st
import geemap.foliumap as geemap
import ee
from datetime import datetime

#geemap.ee_initialize(token_name="EARTHENGINE_TOKEN")

#def ee_authenticate(token_name="EARTHENGINE_TOKEN"):
#    geemap.ee_initialize(token_name=token_name)
Map = geemap.Map()

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
     #VisAviS2024
    based on a repository of:
    Qiusheng Wu: [GitHub](https://github.com/giswqs) 
    """
)

#ADM0 geom for Norway
def get_norway_geometry():
    # Load the international boundaries dataset
    countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
    
    # Filter the dataset to get Norway's geometry
    norway = countries.filter(ee.Filter.eq('country_na', 'Norway')).geometry()
    
    return norway

# Function to get mean wind speed for a given date
def get_mean_wind_speed(date):
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR') \
                .filterDate(date, date.advance(1, 'day')) \
                .select('u_component_of_wind_10m', 'v_component_of_wind_10m')

    def compute_speed(image):
        speed = image.expression('sqrt(u_component_of_wind_10m**2 + v_component_of_wind_10m**2)', {
            'u_component_of_wind_10m': image.select('u_component_of_wind_10m'),
            'v_component_of_wind_10m': image.select('v_component_of_wind_10m')
        })
        return speed.rename('wind_speed').copyProperties(image, image.propertyNames())

    wind_speed = dataset.map(compute_speed).mean()

    norway_geometry = get_norway_geometry()

    wind_speed_clip = wind_speed.clip(norway_geometry)
    return wind_speed_clip




# Streamlit app
def main():
    st.title("Mean Wind Speed Map for Norway")

    # Date selector
    selected_date = st.date_input("Select a date", datetime.now().date())
    selected_date_str = selected_date.strftime('%Y-%m-%d')

    # Get the wind speed image
    wind_speed_image = get_mean_wind_speed(ee.Date(selected_date_str))

    # Create a map
    Map = geemap.Map(center=[65, 15], zoom=4)
    Map.addLayer(wind_speed_image, {'min': 0, 'max': 20, 'palette': ['blue', 'green', 'yellow', 'red']}, 'Mean Wind Speed')

    # Display the map in Streamlit
    st.write("Based on ERA5 daily aggregated mean")
    Map.to_streamlit(height=600)

if __name__ == "__main__":
    main()
