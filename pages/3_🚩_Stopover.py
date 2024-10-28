import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, Point
import h3
import pydeck as pdk
import json
import plotly.express as px


st.set_page_config(layout="wide")

# Bounding box coordinates for a region in Norway (replace with actual subregion coordinates)
species_options = [
    "Anser fabalis",        
    "Numenius phaeopus",      
    "Lymnocryptes minimus",         
    "Tachybaptus ruficollis",  
    "Gavia adamsii",           
]

# GBIF API base URL for occurrence data
GBIF_API_URL = "https://api.gbif.org/v1/occurrence/search"

# Function to get GBIF data for a specific species and year, with pagination
def get_gbif_data(species, year=None):
    limit = 300  # Maximum limit for each request
    offset = 0   # Starting point for pagination
    all_records = []  # List to store all retrieved records

    params = {
        "scientificName": species,
        "hasCoordinate": "true",  # Only include records with coordinates
        "publishingCountry": "NO",  # Filter by publishing country (example: NO for Norway)
        "limit": limit,             # Number of records to retrieve per request
        "offset": offset            # Offset for pagination
    }

    # Add year filter if specified
    if year:
        params["year"] = year

    while True:
        response = requests.get(GBIF_API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                all_records.extend(data['results'])  # Add the current page of results
                if len(data['results']) < limit:
                    break  # No more records to fetch, exit loop
                offset += limit  # Move to the next page of results
                params["offset"] = offset
            else:
                break  # No results, exit loop
        else:
            st.error(f"Error fetching data from GBIF: {response.status_code}")
            break

    # Look for media (images) in the occurrence records
    for rec in all_records:
        media = rec.get("media")
        if media:
            for item in media:
                if item.get("type") == "StillImage":
                    rec['image_url'] = item.get("identifier")  # Store the image URL

    return all_records

# Function to parse GBIF data and convert to DataFrame
def parse_gbif_data(data):
    if not data:
        st.error("No data found for the specified species.")
        return pd.DataFrame()

    # Extract relevant fields: lat, lon, and any others of interest
    parsed_data = [{
        "scientificName": rec.get("scientificName"),
        "LAT": rec.get("decimalLatitude"),  # Rename decimalLatitude to LAT
        "LON": rec.get("decimalLongitude"), # Rename decimalLongitude to LON
        "country": rec.get("country"),
        "year": rec.get("year"),
        "date": rec.get("eventDate")  # Include the event date
    } for rec in data if rec.get("decimalLatitude") and rec.get("decimalLongitude")]

    return pd.DataFrame(parsed_data)

# Function to create H3 hexagonal grid and aggregate occurrences
def create_h3_grid(df, resolution=5):
    # Generate H3 hex index for each point
    df['h3_index'] = df.apply(lambda row: h3.latlng_to_cell(row['LAT'], row['LON'], resolution), axis=1)

    # Get unique hexagons from the H3 indices
    unique_hexagons = df['h3_index'].unique()

    # Convert the H3 hexagons back to polygons
    hexagons = []
    for hex_index in unique_hexagons:
        hex_boundary = h3.cell_to_boundary(hex_index)  # Returns list of lat/lon tuples
        hexagon = Polygon([(lat, lon) for lon, lat in hex_boundary])  # Convert to Polygon
        hexagons.append((hex_index, hexagon))

    # Create a GeoDataFrame for hexagons
    hex_gdf = gpd.GeoDataFrame(hexagons, columns=['h3_index', 'geometry'])

    # Create a GeoDataFrame for the points
    geometry = [Point(xy) for xy in zip(df['LON'], df['LAT'])]
    point_gdf = gpd.GeoDataFrame(df, geometry=geometry)
    hex_gdf = hex_gdf.rename(columns={'h3_index': 'hex_index'})
    # Spatial join: find points that fall within each hexagon
    joined = gpd.sjoin(point_gdf, hex_gdf, how='left', op='within')
    #print(joined)

    # Count occurrences in each hexagon
    hex_counts = joined.groupby('hex_index').size().reset_index(name='counts')

    # Merge the counts back into the hex_gdf
    hex_gdf = hex_gdf.merge(hex_counts, on='hex_index', how='left')
    hex_gdf['counts'] = hex_gdf['counts'].fillna(0).astype(int)  # Fill missing counts with 0
    #print(hex_gdf)

    return hex_gdf

# Function to convert GeoDataFrame hexagons to pydeck-friendly format
def hexagons_to_pydeck_geojson(hex_gdf):
    features = []
    for _, row in hex_gdf.iterrows():
        feature = {
            "type": "Feature",
            "geometry": row['geometry'].__geo_interface__,
            "properties": {"counts": row['counts']}
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    print(geojson)
    
    return geojson

# Streamlit app layout
st.title("Observation data")


# Sidebar input for species name
species_options = [
    "Anser fabalis",        
    "Numenius phaeopus",      
    "Lymnocryptes minimus",         
    "Tachybaptus ruficollis",  
    "Gavia adamsii",           
]
species_input = st.sidebar.selectbox("Select Species", species_options)
year_input = st.sidebar.slider("Select Year", min_value=2010, max_value=2024, value=2023)



# Fetch and display GBIF data when button is clicked
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        gbif_data = get_gbif_data(species_input, year=year_input)

    if gbif_data:
        df = parse_gbif_data(gbif_data)
        if not df.empty:
            

            # Check for images in the GBIF data
            image_urls = [rec.get('image_url') for rec in gbif_data if rec.get('image_url')]


            
            # Create a hexagonal grid and aggregate occurrences using H3
            hex_grid = create_h3_grid(df, resolution=5)  # H3 resolution

            # Convert hex grid to GeoJSON for pydeck
            hex_geojson = hexagons_to_pydeck_geojson(hex_grid)
            geojson_string = json.dumps(hex_geojson)
            

            # Create a pydeck Layer for hexagons
            hex_layer = pdk.Layer(
                "GeoJsonLayer",
                hex_geojson,
                opacity=0.8,
                stroked=True,
                filled=True,
                extruded=True,  # Enable extrusion for 3D hexagons
                wireframe=True,  # Adds a wireframe outline to each hexagon
                get_fill_color="[255 - properties.counts * 10, 100 + properties.counts * 5, 150]",  # Dynamic color based on counts
                get_line_color=[255, 255, 255],
                get_elevation="properties.counts * 100",  # Set height based on counts
                elevation_scale=10,
                pickable=True
            )

            # Create a pydeck Layer for occurrence points
            point_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["LON", "LAT"],
                get_radius=1000,
                get_fill_color=[255, 0, 0],
                opacity=0.6
            )

            # Set the map view
            view_state = pdk.ViewState(
                latitude=df['LAT'].mean(),
                longitude=df['LON'].mean(),
                zoom=5,
                pitch=45
            )

            # Render the map with both hexagons and points
            #st.pydeck_chart(pdk.Deck(layers=[hex_layer, point_layer], initial_view_state=view_state, tooltip={"text": "Density: {counts}"}))
            deck = pdk.Deck(
                layers=[hex_layer],
                initial_view_state=view_state,
                map_style=pdk.map_styles.LIGHT,
                tooltip={"text": "Count: {counts}"},
            )
            col1, col2 = st.columns([0.2,0.8])
            if image_urls:
                # Display the first available image
                with col1:
                    st.image(image_urls[0], caption=f"Showing occurrences of {species_input} for the year {year_input}, based on Norwegian Species Observation Service. (Image from GBIF)", width=200,use_column_width =True)
                with col2:
                    st.pydeck_chart(deck)
            else:
                with col1:
                    st.write(f"No image available for {species_input}.")
                with col2:
                    st.pydeck_chart(deck)

            # Render the deck in Streamlit
            
            # Count occurrences per month
            df['month'] = pd.to_datetime(df['date']).dt.month  # Extract month from eventDate
            occurrences_per_month = df['month'].value_counts().sort_index()

            # Create an interactive bar plot using plotly
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            fig = px.bar(
                occurrences_per_month,
                x=occurrences_per_month.index,
                y=occurrences_per_month.values,
                labels={'x': 'Month', 'y': 'Number of occurrences'},
                title=f"Occurrences of {species_input} per month in {year_input}",
                text=occurrences_per_month.values  # Display the counts on the bars
            )

            # Update the x-axis to show month names
            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=month_labels
                ),
                yaxis_title="Number of Occurrences",
                xaxis_title="Month",
                title_x=0.5,  # Center the title
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )

            # Show the interactive plot in Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No valid data to display on the map.")