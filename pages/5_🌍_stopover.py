import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, Point
import h3
import pydeck as pdk
import json

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
        "institutionCode": "nof",   # Filter by institution code (example: nof)
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
st.title("Bird Observations with Hexagonal Grid")
st.subheader("Based on Norwegian Species Observation Service")

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
            st.write(f"Showing occurrences of *{species_input}* for the year {year_input}")
            
            # Create a hexagonal grid and aggregate occurrences using H3
            hex_grid = create_h3_grid(df, resolution=5)  # H3 resolution

            # Convert hex grid to GeoJSON for pydeck
            hex_geojson = hexagons_to_pydeck_geojson(hex_grid)
            geojson_string = json.dumps(hex_geojson)

            # Create a pydeck Layer for hexagons
            hex_layer = pdk.Layer(
                "GeoJsonLayer",
                hex_geojson,
                opacity=0.6,
                stroked=True,
                filled=True,
                extruded=False,
                get_fill_color=[34, 33, 33],
                get_line_color=[255, 255, 255],
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
                zoom=6,
                pitch=0
            )

            # Render the map with both hexagons and points
            #st.pydeck_chart(pdk.Deck(layers=[hex_layer, point_layer], initial_view_state=view_state, tooltip={"text": "Density: {counts}"}))
            deck = pdk.Deck(
                layers=[hex_layer],
                initial_view_state=view_state,
                map_style=pdk.map_styles.LIGHT,
                tooltip={"text": "Count: {counts}"},
            )

            # Render the deck in Streamlit
            st.pydeck_chart(deck)

            # Display data table
            st.write("Occurrences Data:", df)

        else:
            st.error("No valid data to display on the map.")