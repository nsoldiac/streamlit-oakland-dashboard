from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime #, scipy, time


st.set_page_config(layout="wide")

# Load the data from Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=0#gid=0'

st.image('big_logo.png')

st.write('''
# Oakland City Statistics  
Welcome to Empower Oakland's city statistics dashboard. This dashboard provides a central location for key city statistics that are otherwise reported in descentralized and heterogenous ways. The goal of this dashboard is to empower Oakland resudents to have easy access to this information to help them make opinions about the city's current state in context of its past.
''')
''
# Sidebar here 👇
# st.sidebar.text("Use the sidebar to select the data you want to see")

col1, col2 = st.columns(2, gap='large')

with col1:
    # slider example
    min_value = 2015 #crime_df['date_month'].min().year
    max_value = datetime.datetime.now().year #crime_df['date_month'].max().year

    from_year, to_year = st.slider(
        '**Year range for crime ativity**',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value])


    ## Crime Data
    crime_df = conn.read(spreadsheet=url, usecols=[0, 1, 2])

    # Clean the 'count' column by removing commas or any non-numeric characters
    crime_df['count'] = crime_df['count_rows'].str.replace(r'[^0-9]', '', regex=True)
    crime_df = crime_df.rename(columns={'by_month_datetime': 'date_month'})

    # Convert the cleaned 'count' column to numeric
    crime_df['count'] = pd.to_numeric(crime_df['count'], errors='coerce')
    # cast date_month as datetime
    crime_df['date_month'] = pd.to_datetime(crime_df['date_month'])
    crime_df = crime_df.sort_values(by='date_month')

    # Filter the data
    filtered_crime_df = crime_df[
        (crime_df['date_month'] <= pd.to_datetime(to_year, format='%Y'))
        & (pd.to_datetime(from_year, format='%Y') <= crime_df['date_month'])
    ]

    # Group by date and crimetype, and sum the 'count' column
    # df_grouped = crime_df.groupby(['date_month', 'crimetype'], as_index=False)['count'].sum()
    # df_grouped['date_month'] = pd.to_datetime(df_grouped['date_month'])

    # Pivot the DataFrame to create a new column for each distinct crime type
    # df_pivoted = df_grouped.pivot(index='date_month', columns='crimetype', values='count')

    # Fill any missing values with 0 (since there might be dates without specific crimes)
    # df_pivoted = df_pivoted.fillna(0)

    # Flatten the columns (optional, makes it easier to work with multi-index columns)
    # df_pivoted.columns = df_pivoted.columns.get_level_values(0)

    # st.dataframe(df_pivoted)
    # crime_line_chart = st.line_chart(df_pivoted)

    # Input annotations
    # ANNOTATIONS = [
    #     ("Jan 05, 2015", "Libby Schaaf 1st term"),
    #     ("Jan 07, 2019", "Libby Schaaf's 2nd term"),
    #     ("Mar 17, 2020", "COVID-19 lockdown + restrictions encated"),
    #     ("Jan 09, 2023", "Sheng Tao + Pamela Price assume office"),
    # ]

    # Create a chart with annotations
    # annotations_df = pd.DataFrame(ANNOTATIONS, columns=["date_month", "event"])
    # annotations_df.date_month = pd.to_datetime(annotations_df.date_month)
    # annotations_df["y"] = 0
    # annotation_layer = (
    #     alt.Chart(annotations_df)
    #     .mark_text(size=20, text="⬇️", dx=0, dy=-100, align="center")
    #     .encode(
    #         x="date_month:T",
    #         y=alt.Y("y:Q"),
    #         tooltip=["event"],
    #     )
    #     .interactive()
    # )

    # Altair line chart
    altair_crimeChart = alt.Chart(filtered_crime_df).mark_line(interpolate="monotone").encode(
        x=alt.X('date_month', title=None),  # No title for x-axis
        y=alt.Y('count', title='Crime count'),  # No title for y-axis,
        color=alt.Color('crimetype',legend=alt.Legend(title=None, orient='bottom', direction='horizontal', labelFontSize=12, labelOverlap=True))
    ).properties(
        height=450,
        padding={"left": 30, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text='Crime Counts for top crime types', anchor='start', dx=30, dy=-15)
    )

    # st.altair_chart((altair_crimeChart + annotation_layer).interactive(), use_container_width=True)
    st.altair_chart(altair_crimeChart.interactive(), use_container_width=True)
    ''
    ''


    ### Stops data (from Tim's sheet)
    url_stops = 'https://docs.google.com/spreadsheets/d/1bDUZO6l8xTXYz0K_ABJlPZbgh_mef4cvle70sgO_gXM/edit?gid=1616870163#gid=1616870163'
    df_stops = conn.query('''
                          select * --Year_Quarter, Difference_YoY
                          from "OPD Quarterly Crime stats" 
                          where Crimes_2 = 'Violent Crime Index (homicide, aggravated assault, rape, robbery)'
                          ''', spreadsheet=url_stops)
    # Year column to string
    # df_stops['Year'] = df_stops['Year'].astype(str)
    # df_stops['Annual_Change_YTD'] = df_stops['Annual_Change_YTD'].str.replace('%', '').astype(float) / 100

    # st.dataframe(df_stops)
    altair_stopsChart = alt.Chart(df_stops).mark_bar(interpolate="monotone").encode(
        x=alt.X('Year_Quarter:N', title='Quarter'),  # No title for x-axis
        y=alt.Y('Difference_YoY:Q', title='Yearly change in crime', scale=alt.Scale(nice=False, zero=False, padding=0)),  # No title for y-axis
        tooltip=[alt.Tooltip('Year_Quarter:N', title='Quarter'), alt.Tooltip('Difference_YoY:Q', format='.0%', title='Yearly change')],
        color=alt.condition(
            alt.datum.Difference_YoY < 0,
            alt.value('green'),  # color the bar green if the value is negative
            alt.value('red')  # color the bar red if the value is positive
        )
    ).properties(
        height=450,
        padding={"left": 0, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text='Violent crime change vs prior year', anchor='start', dx=30, dy=-15),
    ).configure_axisY(
        labelExpr="format(datum.value, '.0%')"
    )
    
    st.altair_chart((altair_stopsChart).interactive(), use_container_width=True)


with col2:
    subcol_race_type, subcol_race_year = st.columns(2, vertical_alignment="bottom")
    race_type = subcol_race_type.selectbox(
        "**Campaign race**",
        ('Mayor','City Council','District Attorney','School Board'), 
        index=0)
    race_year = subcol_race_year.selectbox( 
        "**Campaign funding year**",
        (2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024),
        index=7)

    # subfilter_col1, subfilter_col2 = st.columns(2, vertical_alignment="bottom")

    # subfilter_col1.year_option = st.selectbox(
    #     "Campaign funding year",
    #     (2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024),
    #     index=7,
    # )

    # subfilter_col2.race_option = st.selectbox(
    #     "Campaign race",
    #     ('Mayor','City Council','District Attorney','School Board'),
    #     index=0,
    # )

    url_campaign_funding = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=645810962#gid=645810962'
    df_campaign_funding = conn.query('''
                                     select From_Date, Campaign_type, Filer_NamL as Reporter, sum(Amount_A) as amount 
                                     from "Campaign finance summary totals" 
                                     where Line_Item = '3' and Form_Type in ('A','B1','C','D','E','F','G','H','I') and Campaign_type in ('Mayor','City Council','District Attorney','School Board')
                                     group by 1,2,3
                                     ''', spreadsheet=url_campaign_funding)
    df_campaign_funding['From_Date'] = pd.to_datetime(df_campaign_funding['From_Date'])
    df_campaign_funding['Year'] = df_campaign_funding['From_Date'].dt.year
    # st.dataframe(df_campaign_funding)

    subcol_left, subcol_right = st.columns(2, vertical_alignment="top")

    with subcol_left:
        ''
        ''
        ''
        # st.subcol_left(altair_campaign_funding, use_container_width=True)
        total_funding = df_campaign_funding['amount'].sum()
        formatted_funding = "${:,.0f}".format(total_funding)
        st.metric(label='**Total funding for filter selection**', value=formatted_funding, delta=0, delta_color='normal')

    with subcol_right:
        altair_campaign_funding = alt.Chart(df_campaign_funding).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('amount:Q'),
            color=alt.Color('Reporter',legend=None),
            tooltip=[alt.Tooltip('Reporter:N', title='Reporter'),
                alt.Tooltip('amount:Q', format='$,.0f', title='Amount')],
            order=alt.Order('amount', sort='descending')
        ).properties(
            title=alt.Title(text='Campaign funding by reporter'),
            padding={"left": 0, "top": 50, "right": 0, "bottom": 0},
            height=300,
        ).transform_filter(
            (alt.datum.Year == race_year) & (alt.datum.Campaign_type == race_type)
        )
        
        st.altair_chart(altair_campaign_funding, use_container_width=True)



    
    