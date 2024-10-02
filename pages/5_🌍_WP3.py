import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# Bounding box coordinates for a region in Norway (replace with actual subregion coordinates)
species_options = [
    "Anser fabalis",         # Lion
    "Numenius phaeopus",      # Asian Elephant
    "Lymnocryptes minimus",         # Brown Bear
    "Tachybaptus ruficollis",  # Giant Panda
    "Gavia adamsii",           # Eurasian Lynx
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

# Streamlit app layout
st.title("GBIF Species Occurrence Viewer")
st.subheader("Selected for Agder, Rogaland, Vestland, Møre & Romsdal and Trøndelag")

# Sidebar input for species name
species_input = st.sidebar.selectbox("Select Species", species_options)

# Year selection slider
year_input = st.sidebar.slider("Select Year", min_value=2010, max_value=2024, value=2023)

# Fetch and display GBIF data when button is clicked
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        gbif_data = get_gbif_data(species_input, year=year_input)

    if gbif_data:
        df = parse_gbif_data(gbif_data)
        if not df.empty:
            st.write(f"Showing occurrences of *{species_input}* for the year {year_input}")

            # Display data on a map
            st.map(df[["LAT", "LON"]])

            # Count occurrences per month
            df['month'] = pd.to_datetime(df['date']).dt.month  # Extract month from eventDate
            occurrences_per_month = df['month'].value_counts().sort_index()

            # Plotting occurrences per month
            plt.figure(figsize=(10, 6))
            occurrences_per_month.plot(kind='bar', color='skyblue')
            plt.title(f"Occurrences of {species_input} per Month in {year_input}")
            plt.xlabel("Month")
            plt.ylabel("Number of Occurrences")
            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(plt)  # Display the plot

            # Display data table
            st.write("Occurrences Data:", df)

        else:
            st.error("No valid data to display on the map.")
