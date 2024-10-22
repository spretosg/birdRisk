import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO
from datetime import datetime, timedelta
import plotly.graph_objs as go
import numpy as np
from google.oauth2 import service_account
from google.cloud import bigquery
from astral.sun import sun
from astral import Observer



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




st.title("Bird density distribution")
st.markdown(
    """
Visualizing vertical profiles from ENRAM radar. Test the connection to AWS.
"""
)


# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.


sql = """SELECT radar, latitude, longitude, elevation FROM `visavis-312202.wp4_dev.radar_sites` LIMIT 20"""
df = client.query_and_wait(sql).to_dataframe()

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



# Date selection
    # Date selector
d = datetime.today() - timedelta(days=3)
crit_height = 200


selected_date = st.date_input("Select a date (72h from current date)", d)
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
st.subheader('Density - time current vs. previous years')

fig = go.Figure()

# Add the first line (blue)
fig.add_trace(go.Scatter(
    x=df_mean['datetime_str'],
    y=df_mean['dens'],
    mode='lines+markers',
    name='Mean density 2021-2023',
    line=dict(color='blue')
))

# Add the second line (red)
fig.add_trace(go.Scatter(
    x=df_mean_cur['datetime_str'],
    y=df_mean_cur['dens'],
    mode='lines+markers',
    name= f'Density {selected_date_str}',
    line=dict(color='red')
))

# Update layout
fig.update_layout(
    title='',
    xaxis_title='Datetime',
    yaxis_title='Density',
    xaxis_tickformat='%H:%M:%S',
    legend=dict(x=0, y=1, traceorder='normal'),
    template='plotly_white'
)

# Display the Plotly figure in Streamlit
st.plotly_chart(fig, use_container_width=True)


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
print(df_mean_cur)


# Streamlit app
st.subheader('Time-space density distribution')
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
    title=f"Highest bird density value of {max_value:.2f} at {max_time} flying at {max_dens_at_max_height} m above ground",
    xaxis_title="Date",
    yaxis_title="Height",
    height=600,
    width=1200
)
    
st.plotly_chart(fig)

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

