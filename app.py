import streamlit as st
import pandas as pd
import datetime as dt
import os
import plotly.express as px

#mapbox settings
mapbox_token = 'pk.eyJ1IjoiZHJlY2M0IiwiYSI6ImNsZ2dubnlkeTBkZ2ozbWt4dWdnZHdua2wifQ.s0oh8OhFM1LIsd88hpS_iQ'
px.set_mapbox_access_token(mapbox_token)

#------------------------------------------------------------------------------------------------------------------------------------------------------------

#Page Settings

def max_width(width:str = '1600px'):
    st.markdown(f""" 
                <style> 
                .appview-container .main .block-container{{ max-width: {width}; }}
                </style>    
                """, 
                unsafe_allow_html=True,
    )

#set page width 
max_width()

#------------------------------------------------------------------------------------------------------------------------------------------------------------

#Data Prep

#load data files
df_cdn = pd.read_excel('./processed/School Locations Geocoded/Location Data - CDN.xlsx')
df_cdn['Brand'] = 'CDN'

df_kindercare = pd.read_excel('./processed/School Locations Geocoded/Location Data - Kindercare.xlsx')
df_kindercare['Brand'] = 'Kindercare'

#process data files

#process CDN table
df_cdn = df_cdn.rename(columns={'Director': 'CenterDirector', 'School': 'SchoolID'})
df_cdn['CenterPageLink'] = 'none'
df_cdn_processed = df_cdn[['Brand', 'SchoolID', 'CenterName', 'CenterDirector', 'GeocodedLat', 'GeocodedLon', 'CenterPageLink']]

#process kindercare table
df_kindercare = df_kindercare.rename(columns={'CenterLeaderName': 'CenterDirector'})
df_kindercare['SchoolID'] = df_kindercare['CenterPageLink'].str[-6:]

#exclude bad data - around 100 schools don't have addreses, need to correct on crawler later!!
df_kindercare_processed = df_kindercare[['Brand', 'SchoolID', 'CenterName', 'CenterDirector', 'GeocodedLat', 'GeocodedLon', 'CenterPageLink']]
df_kindercare_processed = df_kindercare_processed.loc[df_kindercare_processed['CenterDirector'] != 'error']

#combine processed tables
df_combined_processed = pd.concat([df_cdn_processed, df_kindercare_processed])

#------------------------------------------------------------------------------------------------------------------------------------------------------------

#Metrics

total_locations_kindercare = df_kindercare.SchoolID.nunique()
locations_with_addresses_kindercare = df_kindercare_processed.SchoolID.nunique()
locations_missing_addresses_kindercare = total_locations_kindercare - locations_with_addresses_kindercare


#------------------------------------------------------------------------------------------------------------------------------------------------------------


#Plot Function

#colors
color_blue = '#2a3bfa'
color_red = '#fa512a'

def show_map(clusters):

    #fig
    fig = px.scatter_mapbox(df_combined_processed, lat='GeocodedLat', lon='GeocodedLon', color='Brand',
                            color_discrete_sequence=[color_blue, color_red],
                            hover_data=['SchoolID', 'CenterName', 'CenterDirector', 'CenterPageLink'],
                            zoom=4, mapbox_style='light',
                            center=dict(lat=39.8283, lon=-98.5795))

    if clusters == "clusters on":
        fig.update_traces(marker_size=16, marker_opacity=0.50, cluster=dict(enabled=True, opacity=0.75, step=2))
    else:
        fig.update_traces(marker_size=16, marker_opacity=0.50)

    fig.update_layout(
        height=1000, width=1600,
        legend=dict(font_size=18, title='', orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font_family='Roboto', margin=dict(l=0, r=0, t=100, b=0)
        )


    return(fig)

#------------------------------------------------------------------------------------------------------------------------------------------------------------

#Sidebar
st.sidebar.write('## Map Options')

show_clusters = st.sidebar.radio(label= '', options=['clusters on', 'clusters off'], horizontal=False)

#------------------------------------------------------------------------------------------------------------------------------------------------------------

#Page Output

st.header('Childcare Centers in the U.S.')
st.write('---')


st.plotly_chart(show_map(show_clusters), use_container_width=True)

#add footnotes
st.write(f'*Some address data could not be geocoded due to bad/non-matching address data. These points were plotted according to their zip code instead.')
st.write(f'*Showing {locations_with_addresses_kindercare} of {total_locations_kindercare} total Kindercare locations, where address data was available.')
st.write('---')


#view and download data

#prep export file, reoder cols for cleaner export
cols = ['Brand', 'SchoolID', 'CenterName', 'CenterDirector', 'CenterLeaderTitle', 'CenterHours', 'CenterAddressCity', 'CenterAddressState', 'CenterAddressZip', 'CenterPageLink']
df_kindercare_export = df_kindercare[cols]
df_kindercare_export = df_kindercare_export.sort_values(by='SchoolID')


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

df_export = convert_df(df_kindercare_export)

with st.expander("View Kindercare Data"):
    st.dataframe(df_kindercare_export)
    st.download_button('Download Data File', data=df_export, file_name='kindercare-locations.csv', mime='text/csv')



