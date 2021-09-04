import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import pydeck as pdk
import time
import altair as alt
from io import StringIO
import json
import geopandas as gpd

# create dateparser to be safe -----
from datetime import datetime
dateparse = lambda x: datetime.strptime(x, '%Y-%m-%d')

# get absolute path and use it to create absolute path for csv data
import os
dirname = os.path.dirname(__file__)

# # In progress warning
# components.html(
#     """
#     <div>
#         <h1 style="color: white; text-align: center">--------------- WORK IN PROGRESS ---------------</h1>
#     </div>
#     """,
# )

# Create some title and text
st.title("Hired Foreigners in Meiji Japan")
st.markdown("""This application is a Streamlit dashboard that can be used to analyze the presence of hired foreigners in Japan during the Meiji era (1868-1912).

The analysis is based on data from the 『資料御雇外国人』 by the Centre for East Asian Cultural Studies for UNESCO.""")


# import prepared raw data from aws_client.py
from aws_client import csv_string, json_content

# tell Streamlit to keep the data in a cache so that it does not have to rerun the whole code when something changes
@st.cache(persist=True)
def load_data(nrows = 50000):
    # read/parse the file retrieved from the S3 bucket
    # data = pd.read_csv(StringIO(csv_string), parse_dates=[['employment_start']], date_parser=dateparse)
    data = pd.read_csv(StringIO(csv_string))
    data['employment_start'] = pd.to_datetime(data['employment_start'], errors='coerce')

    # we must not have NAs in lon, lat info when working with maps
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)

    print("loading data")

    return data

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')


# (0) Load data -----
data = load_data()
# st.write(data)
edited_data = data.copy()

# Notify the reader that the data was successfully loaded.
data_load_state.text("Loading data ... Done!") # (using st.cache)


# enter some blank space
st.write("#")


# (1) Map showing the regional distribution of oyatoi ------
oyatoi_json = gpd.read_file(json_content)
# st.write(oyatoi_json.head())

# select industry from dropdown for which you want to see the regional distribution
industry_selection = st.selectbox('Select an Industry:',
    ("Any","Agriculture","Fishery","Forestry","Mining","Manufacturing","Service","Infrastructure","Construction"))

if industry_selection != "Any":
    oyatoi_json['selection'] = oyatoi_json[industry_selection.lower()]
    oyatoi_json['display'] = np.log(oyatoi_json[industry_selection.lower()] +1) ** 2.5
else:
    oyatoi_json['selection'] = oyatoi_json['nr_oyatoi']
    oyatoi_json['display'] = np.log(oyatoi_json['nr_oyatoi'] +1) ** 2.5

INITIAL_VIEW_STATE = pdk.ViewState(latitude=35.554, longitude=135.73, zoom=4.5, max_zoom=7, pitch=40, bearing=0)

geojson = pdk.Layer(
    "GeoJsonLayer",
    oyatoi_json,
    opacity=0.8,
    stroked=False,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation="display * 400",
    get_fill_color="[255, 255 - display/20 * 255, 255]",
    pickable = True,
)

r = pdk.Deck(map_style="mapbox://styles/mapbox/light-v9",
    layers=[geojson],
    initial_view_state=INITIAL_VIEW_STATE,
    tooltip={
        "text": "{selection} Hired Foreigners in {N03_006}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    },) # setting pickable but not tooltip leads to freezing apparently with the current version)
st.write(r)

st.markdown("""
<style>
.note-font {
font-size:13px;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<p class="note-font"><i>Notes:</i> <br> (1) The high number of foreigners recorded in Kochi is due to the Tosa samurai who hired a large number of foreigners after founding the Mitsubishi corporation in 1873. <br> (2) Some individuals worked in multiple locations over the time of their stay in Japan.</p>', unsafe_allow_html=True)

# # (2) Distribution of oyatoi across years -----
# # reset data (include duplicates by 'id' again)
# edited_data = data.copy()
# # rename columns in edited_data
# edited_data = edited_data.rename(columns = {'time_employed_converted':'Employment Duration (Days)'})
# edited_data.dropna(subset=['employment_start'], inplace = True)
#
# # Create histogram showing the number of oyatoi over time
# st.subheader("Number of Oyatoi Hired in a Given Period")
# # create start year variable
# edited_data['Employment Start (Year)'] = (edited_data['employment_start'].dt.year)
# # edited_data['employment_start_year'] = edited_data['employment_start_year'].astype('int32')
# chart_wages = alt.Chart(edited_data[edited_data['Employment Start (Year)'] <= 1912]).mark_bar().encode(
#     alt.X("Employment Start (Year)", bin=alt.Bin(maxbins=30), axis = alt.Axis(title='Employment Start (Year)')),
#     y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
#     tooltip=['count()'],
# ).interactive()
# st.altair_chart(chart_wages.properties(width=700, height=410))
#
#
# # enter some blank space
# st.write("#")


# (3) Distribution of oyatoi across industries -----
st.subheader("Number of Oyatoi Hired by Industry")
# reset data
edited_data = data.copy()

# keep only observations per unique foreign employee
edited_data.drop_duplicates(subset=['id'], inplace=True)

industries = edited_data[["agriculture","fishery","forestry","mining","manufacturing","service","infrastructure","construction"]].sum().reset_index()
industries = industries.rename(columns={0:'count'}).sort_values('count')
industries['log_count'] = np.log(industries['count']+1)

chart_industries = alt.Chart(industries).mark_bar().encode(
    alt.X("count", axis=alt.Axis(title='# Employment Spells')),
    y = alt.Y("index", axis = alt.Axis(title='Industry'), sort='-x'),
    tooltip=["count"],
)
st.altair_chart(chart_industries.properties(width=700, height=410))


# enter some blank space
st.write("#")


# (4) Distribution of nationalities among oyatoi -----
st.subheader("Number of Oyatoi Hired by Nationality")
# reset data
edited_data = data.copy()

# # keep only observations per unique foreign employee
# edited_data.drop_duplicates(subset=['id'], inplace=True)

nationalities = edited_data[['austria','belgium','benin','britain','canada','china','denmark','finland','france','germany','hawaii','hungary','india','ireland','italy','mauritius','netherlands','norway','philippines','portugal','russia','scotland','sweden','switzerland','usa']].sum().reset_index()
nationalities = nationalities.rename(columns={0:'count'}).sort_values('count')
nationalities['log_count'] = np.log(nationalities['count']+1)
chart_nationalities = alt.Chart(nationalities).mark_bar().encode(
    alt.X("log_count", axis = alt.Axis(title='Log(# Employment Spells + 1)')),
    y = alt.Y("index", axis=alt.Axis(title='Nationality'), sort='-x'),
    tooltip=["count"],
)
st.altair_chart(chart_nationalities.properties(width=700, height=500))


# enter some blank space
st.write("#")


# (5) Distribution of Employment Duration among oyatoi -----
# reset data (include duplicates by 'id' again)
edited_data = data.copy()
# rename columns in edited_data
edited_data = edited_data.rename(columns = {'time_employed':'Employment Duration (Days)', 'avg_wage':'Wage (Yen)'})
# drop obserations with NAs for employment duration
edited_data.dropna(subset=['Employment Duration (Days)'], inplace = True)

# Create histogram showing the distribution of employment duration among hired foreigners
st.subheader("Distribution of Employment Duration (in Days) among Hired Foreigners")
upper_limit = st.slider(label="Select upper limit (in days)",min_value=100, max_value=10000, value=9000)
chart_wages = alt.Chart(edited_data[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < upper_limit)]).mark_bar().encode(
    alt.X("Employment Duration (Days)", bin=alt.Bin(maxbins=30), axis = alt.Axis(title='Employment Duration (Days)')),
    y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
    tooltip=['count()'],
).interactive()
st.altair_chart(chart_wages.properties(width=700, height=500))

# compute corresponding average and variance of wages
average_employment_duration = np.average(edited_data.loc[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < 5000),'Employment Duration (Days)'])
variance_employment_duration = np.var(edited_data.loc[(edited_data['Employment Duration (Days)'] > 0) & (edited_data['Employment Duration (Days)'] < 5000),'Employment Duration (Days)'])
st.markdown("Average employment duration: {:.0f} days".format(average_employment_duration))
st.markdown("Standard error: {:.2f}".format(np.sqrt(variance_employment_duration)))


# enter some blank space
st.write("#")


# (6) Distribution of Wages among oyatoi -----

# drop obserations with NAs for employment duration
edited_data.dropna(subset=['Wage (Yen)'], inplace = True)

# Create histogram showing the distribution of wages among hired foreigners
st.subheader("Distribution of Wages among Hired Foreigners")
edited_data['Log Wage (Yen)'] = np.log(edited_data['Wage (Yen)'])
# Altair chart looks better than st.bar_chart
chart_wages = alt.Chart(edited_data[(edited_data['Wage (Yen)'] > 0) & (edited_data['Wage (Yen)'] < 2500)]).mark_bar().encode(
    alt.X("Wage (Yen)", bin=alt.Bin(maxbins=25), axis = alt.Axis(title='Wage (Yen)')),
    y=alt.Y('count()', axis=alt.Axis(title='# Employment Spells')),
    tooltip=['count()'],
) # .interactive()
st.altair_chart(chart_wages.properties(width=700, height=500))

# compute corresponding average and variance of wages
average_wage = np.average(edited_data.loc[edited_data['Wage (Yen)'] > 0,'Wage (Yen)'])
variance_wage = np.var(edited_data.loc[edited_data['Wage (Yen)'] > 0,'Wage (Yen)'])
st.markdown("Average Wage: {:.2f} Yen".format(average_wage))
st.markdown("Standard error: {:.2f}".format(np.sqrt(variance_wage)))


# enter some blank space
st.write("#")


# # (7) Raw Data -----
# # add a checkbox in order to not always show the raw data
# if st.checkbox("Show Raw Data", False):
#     st.subheader('Raw Data')
#     st.write(data)
#
#
# # enter some blank space
# st.write("#")


# # .csv file and pdf documentation
# components.html(
#     """
#     <div>
#         <p style="color: white; text-align: center">The raw data can be downloaded <a href="https://www.hired-foreigners.com/data/oyatoi.csv">here</a> and the documentation <a href="https://www.hired-foreigners.com/pdf/Oyatoi_Documentation.pdf">here</a></p>
#     </div>
#     """,
# )

# Footer
components.html(
    """
    <div>
         <p style="color: white; text-align: left; font-size:1em;">The raw data can be downloaded <a href="https://www.hired-foreigners.com/data/oyatoi.csv">here</a> and the documentation <a href="https://www.hired-foreigners.com/pdf/Oyatoi_Documentation.pdf">here</a></p>
    </div>
    </br>
    <div style="position: fixed; bottom: 0px;">
        <p style="color:white; font-size:1em;">Created by <a href="https://floriancaro.com" target="_blank">Florian Caro</a>.</p>
    </div>
    """,
)

# # remove data loading text
# time.sleep(10)
# data_load_state.text("")
