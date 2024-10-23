import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
from io import StringIO
from datetime import datetime, timedelta
from google.oauth2 import service_account
from google.cloud import bigquery
from astral.sun import sun
from astral import Observer
import numpy as np
import geopy
from geopy.distance import geodesic

# Set up Streamlit page
st.set_page_config(layout="wide")

st.sidebar.info(
    """
    - Web App URL: <https://birdrisk.streamlit.app>
    - GitHub repository: <https://github.com/spretosg/birdRisk>
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

np.random.seed(42)  # For consistent randomization




st.title("Bird density distribution")
st.markdown(
    """
Visualizing vertical profiles from ENRAM radar. Test the connection to AWS.
"""
)

# Date selection
    # Date selector
d = datetime.today() - timedelta(days=3)
crit_height = 200


selected_date = st.date_input("Select a date (72h from current date)", d)


# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.


# Fetch radar station data from BigQuery
sql = """SELECT radar, latitude, longitude, elevation FROM `visavis-312202.wp4_dev.radar_sites` LIMIT 20"""
df = client.query(sql).to_dataframe()

df['wind_speed'] = np.random.uniform(5, 25, size=len(df))  # Wind speed in m/s
df['wind_dir'] = np.random.uniform(0, 360, size=len(df))    # Wind direction in degrees
df['bird_dir'] = np.random.uniform(0, 360, size=len(df))    # Bird mean direction in degrees

# Calculate u, v components for wind and bird direction to draw arrows
df['wind_u'] = df['wind_speed'] * np.cos(np.radians(df['wind_dir']))
df['wind_v'] = df['wind_speed'] * np.sin(np.radians(df['wind_dir']))
df['bird_u'] = 10 * np.cos(np.radians(df['bird_dir']))  # Fixed scaling for bird direction
df['bird_v'] = 10 * np.sin(np.radians(df['bird_dir']))  # Fixed scaling for bird direction

# Add a map to the app to display radar locations
# Function to calculate points of a circle given center and radius
def calculate_circle_points(lat, lon, radius_km, num_points=100):
    """ Returns the latitude and longitude points of a circle around a central point. """
    angles = np.linspace(0, 360, num_points)
    circle_points = []
    
    for angle in angles:
        # Calculate destination points from center at each angle
        destination = geodesic(kilometers=radius_km).destination((lat, lon), angle)
        circle_points.append((destination.latitude, destination.longitude))
    
    return pd.DataFrame(circle_points, columns=['latitude', 'longitude'])

# Generate a random "density" value for each radar to use for the color ramp (can be replaced by real data)
df['density_value'] = np.random.uniform(0, 1, size=len(df))  # Values between 0 (green) and 1 (red)


# Create a map plot using Plotly
fig = px.scatter_mapbox(df,
                        lat='latitude',
                        lon='longitude',
                        hover_name='radar',
                        hover_data={'latitude': False, 'longitude': False, 'wind_speed': True, 'wind_dir': True, 'bird_dir': True},
                        zoom=3,
                        height=500)

# Add wind direction and bird direction as arrows on the map
for i, row in df.iterrows():

    
    # Add 50 km radius circle around each radar
    circle_points = calculate_circle_points(row['latitude'], row['longitude'], radius_km=50)
    # Use the density value to determine the color of the circle (green to red)
    color_scale = px.colors.sequential.Greens  # Greenish color scale
    color_index = int(row['density_value'] * (len(color_scale) - 1))  # Map density value to color scale index
    circle_color = color_scale[color_index]
    fig.add_trace(go.Scattermapbox(
        mode='lines',
        lon=circle_points['longitude'],
        lat=circle_points['latitude'],
        fill='toself',
        fillcolor=circle_color,
        line=dict(width=2, color=circle_color),
        showlegend=False
    ))
    # Wind direction arrow (scaled with wind speed)
    fig.add_trace(go.Scattermapbox(
        mode="markers+lines",
        lon=[row['longitude'], row['longitude'] + 0.1 * row['wind_u']],  # Scale the arrow by a factor for visibility
        lat=[row['latitude'], row['latitude'] + 0.1 * row['wind_v']],
        marker={'size': 10, 'symbol': "arrow-bar", 'angle': row['wind_dir']},
        line=dict(width=2, color='blue'),
        showlegend=False,  # Remove from legend
        name=f"Wind: {row['wind_speed']:.1f} m/s, {row['wind_dir']:.1f}°"
    ))

    # Bird mean direction arrow (fixed scaling)
    fig.add_trace(go.Scattermapbox(
        mode="markers+lines",
        lon=[row['longitude'], row['longitude'] + 0.05 * row['bird_u']],  # Scale the arrow by a smaller factor
        lat=[row['latitude'], row['latitude'] + 0.05 * row['bird_v']],
        marker={'size': 10, 'symbol': "arrow-bar", 'angle': row['bird_dir']},
        line=dict(width=2, color='red'),
        name=f"Bird: {row['bird_dir']:.1f}°",
        showlegend=False  # Remove from legend

    ))


# Plot the density grid for all radars as a scatter plot with color scale

# Configure map layout
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# Display the map in Streamlit
selected_radar = st.plotly_chart(fig, use_container_width=True)

## station selection
radar_stat = st.selectbox("Select a radar station",df.radar)
filtered_df = df[df['radar'] == radar_stat]
observer = Observer(latitude=filtered_df.latitude, longitude=filtered_df.longitude, elevation=filtered_df.elevation)


# Function to load data from a URL and return a DataFrame
def load_data(url):
    response = requests.get(url)
    data = StringIO(response.text)
    df = pd.read_csv(data)
    return df

#rad_stationID = 'nohur'
# Base URL of the dataset
#base_url = 'https://aloftdata.s3-eu-west-1.amazonaws.com/baltrad/daily/bejab/2018/bejab_vpts_'
base_url = 'https://aloftdata.s3-eu-west-1.amazonaws.com/baltrad/daily/'

monthly_url = 'https://aloftdata.s3-eu-west-1.amazonaws.com/baltrad/monthly/'




year_sel = selected_date.year
selected_date_str = selected_date.strftime('%Y%m%d')


y1 = selected_date.replace(year=selected_date.year - 1)
y1 = y1.strftime('%Y%m%d')

y2 = selected_date.replace(year=selected_date.year - 2)
y2 = y2.strftime('%Y%m%d')

y3 = selected_date.replace(year=selected_date.year - 3)
y3 = y3.strftime('%Y%m%d')

data_url = f'{base_url}{radar_stat}/{year_sel}/{radar_stat}_vpts_{selected_date_str}.csv'
url1 = f'{base_url}{radar_stat}/{year_sel-1}/{radar_stat}_vpts_{y1}.csv'
url2 = f'{base_url}{radar_stat}/{year_sel-2}/{radar_stat}_vpts_{y2}.csv'
url3 = f'{base_url}{radar_stat}/{year_sel-3}/{radar_stat}_vpts_{y3}.csv'


### sunrise and sunset time for plots
# Get the sunrise and sunset times for the specified date and observer
sun_times = sun(observer, date=selected_date)

# Extract sunrise and sunset times
sunrise = sun_times['sunrise'].strftime('%Y-%m-%d %H:%M:%S')
sunset = sun_times['sunset'].strftime('%Y-%m-%d %H:%M:%S')

# Print the results
#print(f"Sunrise: {sunrise}")
#print(f"Sunset: {sunset}")
rad_el = filtered_df['elevation'].iloc[0] 
rad_el = int(rad_el)

# Load data
st.write(f"Loading data from: {data_url}")
try:
    df = load_data(data_url)
    dfY1 = load_data(url1)
    dfY2 = load_data(url2)
    dfY3 = load_data(url3)
    st.write("Data loaded successfully!")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Display the first few rows of the dataframe
#st.write("Data preview:")
#st.write(df.head())

#df['DateStr'] = df['datetime'].strftime("%Y-%m-%dT%H:%M:%SZ")
#new_df = df.pivot(index='height', columns='datetime')['dens'].fillna(0)
df1 = df[['datetime', 'height','dens']]
df1 = pd.DataFrame(df1)
df1['datetime'] = pd.to_datetime(df1['datetime'], utc=True)
df1['datetime_str'] = df1['datetime'].dt.strftime('%H:%M:%S')


dfY1 = dfY1[['datetime', 'height','dens']]
dfY2 = dfY2[['datetime', 'height','dens']]
dfY3 = dfY3[['datetime', 'height','dens']]
df_all = pd.concat([dfY1,dfY2,dfY3])
df_all['datetime'] = pd.to_datetime(df_all['datetime'], utc=True)
df_all['datetime_str'] = df_all['datetime'].dt.strftime('%H:%M:%S')

# Group by 'datetime' and calculate the mean of 'dens'
df_mean = df_all.groupby('datetime_str')['dens'].mean().reset_index()
# mean of selected day
df_mean_cur = df1.groupby('datetime_str')['dens'].mean().reset_index()

# Subtitle
month_day = selected_date.strftime('%m-%d')
st.subheader(f' {radar_stat} / {month_day}')

fig0 = go.Figure()

# Add the first line (blue)
fig0.add_trace(go.Scatter(
    x=df_mean['datetime_str'],
    y=df_mean['dens'],
    mode='lines+markers',
    name='Mean density 2021-2023',
    line=dict(color='blue')
))

# Add the second line (red)
fig0.add_trace(go.Scatter(
    x=df_mean_cur['datetime_str'],
    y=df_mean_cur['dens'],
    mode='lines+markers',
    name= f'Density 2024',
    line=dict(color='red')
))

# Update layout
fig0.update_layout(
    title='',
    xaxis_title='Datetime',
    yaxis_title='Density',
    xaxis_tickformat='%H:%M:%S',
    legend=dict(x=0, y=1, traceorder='normal'),
    template='plotly_white',
    height=600,
    width=1200
)



# Display the Plotly figure in Streamlit
st.plotly_chart(fig0, use_container_width=True)


glob_dens = df1['dens'].sum()
glob_dens_past = df_all['dens'].sum()
print(glob_dens_past)

## critical values in rotor swept area
df_crit = df1[df1['height'].between(rad_el, rad_el+crit_height)]
df_crit_past = df_all[df_all['height'].between(rad_el, rad_el+crit_height)]
crit_dens_past = df_crit_past['dens'].sum()
#print(df_crit.dtypes)
crit_dens = df_crit['dens'].sum()
performance_value=crit_dens/glob_dens
performance_value_past=crit_dens_past/glob_dens_past

# make a datetime index
df1['datetime'] = pd.to_datetime(df1['datetime'])
#print(df_mean_cur)


# Streamlit app
st.subheader(f'Height distribution at the {selected_date}')
fig = go.Figure(data=go.Heatmap(
        z=df1['dens'],
        x=df1['datetime'],
        y=df1['height'],
        colorscale='Viridis'
))


# Identify the highest value in 'density'
max_value = df1['dens'].max()
max_index = df1['dens'].idxmax()
max_time = df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[max_index]
max_h = df1['datetime'].dt.strftime('%H:%M:%S')[max_index]
max_dens_at_max_height = df1['height'][max_index]  
#print(max_dens_at_max_height)

fig.add_annotation(
    x=df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[max_index],
    y='height',
    text=f"Max: {max_value:.2f}",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.5,
    arrowcolor="red",
    ax=-30,  # Shift the annotation text slightly away from the point
    ay=-40
)

# Draw vertical and horizontal lines from the peak value
fig.add_shape(
    type="line",
    x0=df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[max_index], x1=df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[max_index],
    y0=0, y1=4800,  # y0 and y1 define the height range for the line
    line=dict(color="red", width=2, dash="dash")
)


# Draw vertical line for the sunrise
fig.add_shape(
    type="line",
    x0=sunrise, x1=sunrise,
    y0=4800, y1=5300,  # y0 and y1 define the height range for the line
    line=dict(color="black", width=2)
)

# Draw vertical line for the sunset
fig.add_shape(
    type="line",
    x0=sunset, x1=sunset,
    y0=4800, y1=5300,  # y0 and y1 define the height range for the line
    line=dict(color="black", width=2)
)

fig.add_annotation(
    x=sunrise,  # Position at x=3 (same as the vertical line)
    y=5350,  # Position above the plot (you can adjust this)
    text="🌅",  # This can be any emoji or text
    showarrow=False,
    font=dict(size=20),
    yshift=20  # Shifts the icon/text upwards
)

fig.add_annotation(
    x=sunset,  # Position at x=3 (same as the vertical line)
    y=5350,  # Position above the plot (you can adjust this)
    text="🌙",  # This can be any emoji or text
    showarrow=False,
    font=dict(size=20),
    yshift=20  # Shifts the icon/text upwards
)

# Draw horizontal line for dens at max height
fig.add_shape(
    type="line",
    x0=df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[0],  # Start of the line on the x-axis
    x1=df1['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')[max_index],  # End of the line on the x-axis
    y0=max_dens_at_max_height,  # Horizontal line at dens value
    y1=max_dens_at_max_height,  # Same as y0 to keep it horizontal
    line=dict(color="red", width=2, dash="dash"),
)


# Update layout for better readability
fig.update_layout(
    title=f"Highest bird density value of {max_value:.2f} at {max_h} flying at {max_dens_at_max_height} m above ground",
    xaxis_title="Date",
    yaxis_title="Height",
    height=600,
    width=1200
)
    
st.plotly_chart(fig,use_container_width=True)

# Streamlit app
st.subheader('Percentage of birds within potential rotor swept area during the whole day')
# Normalize the performance value to a scale of 0-100
max_value = 1  # Define your maximum value
performance_percentage = (performance_value / max_value) * 100
performance_percentage_past = (performance_value_past / max_value) * 100

# Create a gauge chart using Plotly
fig2 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = performance_percentage,
    title = {'text': "selected day"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "darkblue"},
        'steps' : [
            {'range': [0, 50], 'color': "lightgray"},
            {'range': [50, 100], 'color': "gray"}
        ],
        'threshold' : {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': performance_percentage}
    }
))

fig3 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = performance_percentage_past,
    title = {'text': "Mean 2021-2023"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "darkblue"},
        'steps' : [
            {'range': [0, 50], 'color': "lightgray"},
            {'range': [50, 100], 'color': "gray"}
        ],
        'threshold' : {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': performance_percentage_past}
    }
))

col1, col2 = st.columns(2)
# Display the gauge chart in Streamlit
# Display the first gauge in the first column
with col1:
    st.plotly_chart(fig2, use_container_width=True)

# Display the second gauge in the second column
with col2:
    st.plotly_chart(fig3, use_container_width=True)

