import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
from io import StringIO

# create dateparser to be safe
from datetime import datetime
dateparse = lambda x: datetime.strptime(x, '%Y-%m-%d')

# get absolute path and use it to create absolute path for csv data
import os
dirname = os.path.dirname(__file__)

# DATA_URL = (
#     os.path.join(dirname, 'Motor_Vehicle_Collisions_-_Crashes_shortened.csv')
# )

# Create some title and text
st.title("Hired Foreigners in Meiji Japan")
st.markdown("This application is a Streamlit dashboard that can be used to analyze the presence of hired foreigners in Japan during the Meiji era (1868-1912).")

# import prepared raw data from aws_client.py
from aws_client import csv_string

# tell Streamlit to keep the data in a cache so that it does not have to rerun the whole code when something changes
@st.cache(persist=True)
def load_data(nrows = 50000):
    # read/parse the file retrieved from the S3 bucket
    # data = pd.read_csv(StringIO(csv_string), parse_dates=[['employment_start_date_converted']], date_parser=dateparse)
    data = pd.read_csv(StringIO(csv_string))
    data['employment_start_date_converted'] = pd.to_datetime(data['employment_start_date_converted'], errors='coerce')

    # we must not have NAs in lon, lat info when working with maps
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)

    return data

data = load_data()
original_data = data

# drop NAs
data.dropna(subset=['latitude', 'latitude'], inplace = True)
data.dropna(subset=['employment_start_date_converted','time_employed_converted'], inplace = True)

# calculate midpoint of all available data points for the map view
midpoint = (np.average(data['latitude']), np.average(data['longitude']))

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 7,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data = data,
            get_position=['longitude','latitude'],
            auto_highlight=True,
            radius=750,
            extruded=True,
            pickable=True,
            elevation_scale=250,
            elevation_range=[0,500],
        ),
    ],
    tooltip={
        "text": "{elevationValue}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
   }, # setting pickable but not tooltip leads to freezing apparently with the current version
))


# add a checkbox in order to not always show the raw data
if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(data)
