import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import pydeck as pdk
# import plotly.express as px
import altair as alt
from io import StringIO
# import geopandas

# create dateparser to be safe
from datetime import datetime
dateparse = lambda x: datetime.strptime(x, '%Y-%m-%d')

# get absolute path and use it to create absolute path for csv data
import os
dirname = os.path.dirname(__file__)

# In progress warning
components.html(
    """
    <div>
        <h1 style="color: white; text-align: center">--------------- WORK IN PROGRESS ---------------</h1>
    </div>
    """,
)

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

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')

# Load data
data = load_data()
# st.write(data)
edited_data = data.copy()

# Notify the reader that the data was successfully loaded.
data_load_state.text("Loading data ... Done!") # (using st.cache)

# drop duplicates for the map of unqiue Oyatoi
edited_data.drop_duplicates(subset=['id'], inplace=True)

# drop observations with NAs in coordinate information
edited_data.dropna(subset=['latitude', 'longitude'], inplace = True)
# edited_data.dropna(subset=['employment_start_date_converted','time_employed_converted'], inplace = True)
# edited_data.dropna(subset=['wage_converted_into_yen'], inplace = True)
edited_data['employment_start_date_converted'] = edited_data['employment_start_date_converted'].astype("datetime64")

# calculate midpoint of all available data points for the map view
midpoint = (np.average(edited_data['latitude']), np.average(edited_data['longitude']))

# create dataframe with logged frequency of entries for each city
frequency = (edited_data[['latitude', 'longitude', 'region_eng']].groupby(edited_data[['latitude', 'longitude', 'region_eng']].columns.tolist()).size().reset_index().rename(columns={0:'records'})) # compute frequency of each location in the data

logged_data = frequency
logged_data['log_frequency'] = 0
for index, row in frequency.iterrows():
    logged_data.loc[index,'log_frequency'] = np.log(row.records + 1)**2

max_records = np.max(logged_data.log_frequency)
logged_data['log_frequency_max_percentage'] = logged_data['log_frequency']/max_records

logged_data = logged_data.reset_index(drop=True)
# gdf = geopandas.GeoDataFrame(logged_data, geometry=geopandas.points_from_xy(logged_data.longitude, logged_data.latitude))
# gdf.to_file("output.geo.json", driver='GeoJSON')

# implement drop down menu to filter for specific nationalities
# st.map(logged_data)

# viewstate range - yet to implement
LONGITUDE_RANGE = [midpoint[1]-10, midpoint[1]+10]
LATITUDE_RANGE = [midpoint[0]-10, midpoint[0]+10]

column_layer = pdk.Layer(
    "ColumnLayer",
    data = logged_data,
    get_position=["longitude", "latitude"],
    get_elevation="log_frequency+1",
    elevation_scale=5000,
    elevation_range=[2000,3000],
    radius=2000,
    get_fill_color=["log_frequency_max_percentage * 250 + 120", 100, 100, 220],
    pickable=True,
    auto_highlight=True,
)

# define view state
view_state = pdk.ViewState(
    latitude= midpoint[0],
    longitude= midpoint[1],
    zoom= 5,
    pitch= 45,
    min_zoom=4.5,
    max_zoom=7,
)

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=view_state,
    layers=[
        column_layer,
    ],
    tooltip={
        "text": "{records} Hired Foreigners in {region_eng}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
   }, # setting pickable but not tooltip leads to freezing apparently with the current version
))


# reset data (include duplicates by 'id' again)
edited_data = data.copy()
# rename columns in edited_data
edited_data = edited_data.rename(columns = {'time_employed_converted':'Employment Duration (Days)', 'wage_converted_into_yen':'Wage (Yen)'})

# Create histogram showing the number of oyatoi over time
st.subheader("Number of Oyatoi Hired in a Given Period")
# create start year variable
edited_data['Employment Start (Year)'] = (edited_data['employment_start_date_converted'].dt.year)
# edited_data['employment_start_year'] = edited_data['employment_start_year'].astype('int32')
chart_wages = alt.Chart(edited_data[edited_data['Employment Start (Year)'] <= 1912]).mark_bar().encode(
    alt.X("Employment Start (Year)", bin=alt.Bin(maxbins=30), axis = alt.Axis(title='Employment Start (Year)')),
    y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
    tooltip=['count()'],
).interactive()
st.altair_chart(chart_wages.properties(width=700, height=410))


# Distribution of nationalities among oyatoi
# drop duplicates for the map of unqiue Oyatoi
edited_data.drop_duplicates(subset=['id'], inplace=True)

nationalities = edited_data[['england','usa','france','germany','norway','finland','italy','china','austria','netherlands','russia','sweden','denmark']].sum().reset_index()
nationalities = nationalities.rename(columns={0:'count'}).sort_values('count')
chart_nationalities = alt.Chart(nationalities).mark_bar().encode(
    alt.X("count", axis = alt.Axis(title='Nationality')),
    y=alt.Y("index", axis=alt.Axis(title='# Employment Spells'), sort='-x'),
    tooltip=["count"],
)
st.altair_chart(chart_nationalities.properties(width=700, height=410))


# reset data (include duplicates by 'id' again)
edited_data = data.copy()
# rename columns in edited_data
edited_data = edited_data.rename(columns = {'time_employed_converted':'Employment Duration (Days)', 'wage_converted_into_yen':'Wage (Yen)'})


# Create histogram showing the distribution of employment duration among hired foreigners
st.subheader("Distribution of Employment Duration (in Days) among Hired Foreigners")
upper_limit = st.slider(label="Select upper limit (in days)",min_value=100, max_value=5000, value=3000)
chart_wages = alt.Chart(edited_data[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < upper_limit)]).mark_bar().encode(
    alt.X("Employment Duration (Days)", bin=alt.Bin(maxbins=30), axis = alt.Axis(title='Employment Duration (Days)')),
    y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
    tooltip=['count()'],
).interactive()
st.altair_chart(chart_wages.properties(width=700, height=410))

# compute corresponding average and variance of wages
average_employment_duration = np.average(edited_data.loc[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < 5000),'Employment Duration (Days)'])
variance_employment_duration = np.var(edited_data.loc[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < 5000),'Employment Duration (Days)'])
st.markdown("Average employment duration: {:.0f} days".format(average_employment_duration))
st.markdown("Standard error: {:.2f}".format(np.sqrt(variance_employment_duration)))


# Create histogram showing the distribution of wages among hired foreigners
st.subheader("Distribution of Wages among Hired Foreigners")
edited_data['Log Wage (Yen)'] = np.log(edited_data['Wage (Yen)'])
# Altair chart looks better than st.bar_chart
chart_wages = alt.Chart(edited_data[(edited_data['Wage (Yen)'] > 0) & (edited_data['Wage (Yen)'] < 2500)]).mark_bar().encode(
    alt.X("Wage (Yen)", bin=alt.Bin(maxbins=25), axis = alt.Axis(title='Wage (Yen)')),
    y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
    tooltip=['count()'],
).interactive()
st.altair_chart(chart_wages.properties(width=700, height=410))

# compute corresponding average and variance of wages
average_wage = np.average(edited_data.loc[edited_data['Wage (Yen)'] > 0,'Wage (Yen)'])
variance_wage = np.var(edited_data.loc[edited_data['Wage (Yen)'] > 0,'Wage (Yen)'])
st.markdown("Average Wage: {:.2f} Yen".format(average_wage))
st.markdown("Standard error: {:.2f}".format(np.sqrt(variance_wage)))


# add a checkbox in order to not always show the raw data
if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(data)

# Footer
components.html(
    """
    <div style="position: fixed; bottom: 0px;">
        <p style="color:white; font-size:1em">Created by <a href="https://github.com/floriancaro/" target="_blank">Florian Caro</a>.</p>
    </div>
    """,
)
