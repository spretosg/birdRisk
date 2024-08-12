import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO
from datetime import datetime, timedelta
import plotly.graph_objs as go


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




st.title("Vertical profiles")
st.markdown(
    """
Visualizing vertical profiles from ENRAM radar. Test the connection to AWS.
"""
)


# Function to load data from a URL and return a DataFrame
def load_data(url):
    response = requests.get(url)
    data = StringIO(response.text)
    df = pd.read_csv(data)
    return df

rad_stationID = 'nohur'
# Base URL of the dataset
#base_url = 'https://aloftdata.s3-eu-west-1.amazonaws.com/baltrad/daily/bejab/2018/bejab_vpts_'
base_url = 'https://aloftdata.s3-eu-west-1.amazonaws.com/baltrad/daily/'


# Streamlit app
st.title('Interactive Heatmap Visualization')

# Date selection
    # Date selector
d = datetime.today() - timedelta(days=3)
selected_date = st.date_input("Select a date", d)
year_sel = selected_date.year
selected_date_str = selected_date.strftime('%Y%m%d')

data_url = f'{base_url}{rad_stationID}/{year_sel}/{rad_stationID}_vpts_{selected_date_str}.csv'

# Load data
st.write(f"Loading data from: {data_url}")
try:
    df = load_data(data_url)
    st.write("Data loaded successfully!")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Display the first few rows of the dataframe
st.write("Data preview:")
st.write(df.head())

#df['DateStr'] = df['datetime'].strftime("%Y-%m-%dT%H:%M:%SZ")
#new_df = df.pivot(index='height', columns='datetime')['dens'].fillna(0)
df1 = df[['datetime', 'height','dens']]

df1 = pd.DataFrame(df1)

fig = go.Figure(data=go.Heatmap(
        z=df1['dens'],
        x=df1['datetime'],
        y=df1['height'],
        colorscale='Viridis'
))

    
st.plotly_chart(fig)

