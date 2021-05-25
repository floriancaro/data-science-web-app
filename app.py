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
edited_data = data.copy()

# drop NAs
edited_data.dropna(subset=['latitude', 'latitude'], inplace = True)
edited_data.dropna(subset=['employment_start_date_converted','time_employed_converted'], inplace = True)
edited_data['employment_start_date_converted'] = edited_data['employment_start_date_converted'].astype("datetime64")

# calculate midpoint of all available data points for the map view
midpoint = (np.average(edited_data['latitude']), np.average(edited_data['longitude']))

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
            data = edited_data,
            get_position=['longitude','latitude'],
            auto_highlight=True,
            radius=1000,
            extruded=True,
            pickable=True,
            elevation_scale=350,
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


# Create histogram showing the number of oyatoi over time
st.subheader("Number of Oyatoi Hired in a Given Period")
hist_values = np.histogram(edited_data['employment_start_date_converted'].dt.year, bins = 20, range = (1867,1912))
hist_values = pd.DataFrame(hist_values).T
hist_values = hist_values.rename(columns={0:'hired_foreigners', 1:'index'}).set_index('index')
st.bar_chart(hist_values)



# Create histogram showing the distribution of employment duration among hired foreigners
st.subheader("Distribution of Employment Duration among Hired Foreigners")
hist_values = np.histogram(edited_data['time_employed_converted'], bins = 12, range = (0,9000))
hist_values = pd.DataFrame(hist_values).T
hist_values = hist_values.rename(columns={0:'employment_duration', 1:'index'}).set_index('index')
st.bar_chart(hist_values)

# compute corresponding average and variance of wages
average_employment_duration = np.average(data['time_employed_converted'])
variance_employment_duration = np.variance(data['time_employed_converted'])
st.markdown("Average employment duration: %" % (average_employment_duration))
st.markdown("Variance: %" % (variance_employment_duration))



# Create histogram showing the distribution of wages among hired foreigners
st.subheader("Distribution of Wages among Hired Foreigners")
hist_values = np.histogram(edited_data['wage_converted_into_yen'], bins = 20, range = (0,4500))
hist_values = pd.DataFrame(hist_values).T
hist_values = hist_values.rename(columns={0:'wage', 1:'index'}).set_index('index')
st.bar_chart(hist_values)

# compute corresponding average and variance of wages
average_wage = np.average(data['wage_converted_into_yen'])
variance_wage = np.variance(data['wage_converted_into_yen'])
st.markdown("Average Wage: %" % (average_wage))
st.markdown("Variance: %" % (variance_wage))


# add a checkbox in order to not always show the raw data
if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(data)
