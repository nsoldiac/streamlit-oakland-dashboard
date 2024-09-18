from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime #, scipy, time

st.set_page_config(layout="wide")


st.image('big_logo.png')

st.write('''
# Oakland City Statistics  
Welcome to Empower Oakland's city statistics dashboard. This dashboard provides a central location for city data usually siloed and disconnected. The goal of this dashboard is to bring these valuable bits of data together to show a cohesive view at how Okland is doing today and in context of its past.
''')
''
# Sidebar here 👇
# st.sidebar.text("Use the sidebar to select the data you want to see")


col1, col2 = st.columns(2, gap='large')

with col1:
    
    st.header('Crime Activity and Response')

    min_value = 2015 #crime_df['date_month'].min().year
    max_value = datetime.datetime.now().year #crime_df['date_month'].max().year

    from_year, to_year = st.slider(
        '**Year range for crime ativity**',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value])

    # Load the data from Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=0#gid=0'

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
        color=alt.Color('crimetype', scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']), legend=alt.Legend(title=None, orient='bottom', direction='horizontal', labelFontSize=12, labelOverlap=True))
    ).properties(
        height=450,
        padding={"left": 15, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text='Crime Counts for top crime types', anchor='start', dx=45, dy=-15)
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
        y=alt.Y('Difference_YoY:Q', title='Yearly change in crime'),  # No title for y-axis
        tooltip=[alt.Tooltip('Year_Quarter:N', title='Quarter'), alt.Tooltip('Difference_YoY:Q', format='.0%', title='Yearly change')],
        color=alt.condition(
            alt.datum.Difference_YoY < 0,
            alt.value('#1AAE74'),  # color the bar green if the value is negative
            alt.value('#EB5E55')  # color the bar red if the value is positive
        )
    ).properties(
        height=450,
        # padding={"left": 0, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text='Violent crime change vs prior year', anchor='start', dx=30, dy=-15),
    ).configure_axisY(
        labelExpr="format(datum.value, '.0%')"
    )
    
    st.altair_chart((altair_stopsChart).interactive(), use_container_width=True)
    ''
    
    
    # OPD Call wait times
    url_opd_call_wait = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=1550683969#gid=1550683969'
    df_opd_call_wait = conn.query('''
                                     select Num_month, Year, Wait_time
                                     from "OPD Call response times" 
                                     where Priority = '1'
                                     ''', spreadsheet=url_opd_call_wait)

    # st.write(df_opd_call_wait)

    altair_opd_call_wait = alt.Chart(df_opd_call_wait).mark_line(
        interpolate="monotone",
        point=alt.OverlayMarkDef(filled=True)
    ).encode(
        x=alt.X('Num_month:O', title=None),  # No title for x-axis
        y=alt.Y('Wait_time:Q', title='Minutes'),  # No title for y-axis,
        color=alt.Color(
            'Year:O', 
            scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']), 
            legend=alt.Legend(
                orient='bottom', 
                direction='horizontal', 
                labelFontSize=12, 
                labelOverlap=True), 
                title=None
                )
    ).properties(
        height=500,
        # padding={"left": 30, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text="Average Police call to arrival in minutes", anchor='start', dx=30) #, dy=0)
    )

    # st.altair_chart((altair_crimeChart + annotation_layer).interactive(), use_container_width=True)
    st.altair_chart(altair_opd_call_wait.interactive(), use_container_width=True)




with col2:
    st.header('Campaign Funding Reporting')

    subcol_race_type, subcol_race_year = st.columns(2, vertical_alignment="bottom")
    race_type = subcol_race_type.selectbox(
        "**Campaign race**",
        ('Mayor','City Council','District Attorney','School Board'), 
        index=0)
    race_year = subcol_race_year.selectbox( 
        "**Campaign funding year**",
        (2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024),
        index=7)

    url_campaign_funding = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=645810962#gid=645810962'
    df_campaign_funding = conn.query('''
                                     select From_Date, Campaign_type, Filer_NamL as Reporter, sum(Amount_A) as amount 
                                     from "Campaign finance summary totals" 
                                     where Line_Item = '5' and Form_Type = 'F460' and Campaign_type in ('Mayor','City Council','District Attorney','School Board')
                                     group by 1,2,3
                                     ''', spreadsheet=url_campaign_funding)
    df_campaign_funding['From_Date'] = pd.to_datetime(df_campaign_funding['From_Date'])
    df_campaign_funding['Year'] = df_campaign_funding['From_Date'].dt.year
    # st.dataframe(df_campaign_funding)

     # Filter the data
    filtered_campaign_funding_df = df_campaign_funding[
        (df_campaign_funding['Year'] == race_year)
        & (df_campaign_funding['Campaign_type'] == race_type)
    ]

    subcol_left, subcol_right = st.columns(2, vertical_alignment="top")

    with subcol_left:
        ''
        ''
        ''
        # st.subcol_left(altair_campaign_funding, use_container_width=True)
        total_funding = filtered_campaign_funding_df['amount'].sum()
        formatted_funding = "${:,.0f}".format(total_funding)
        prior_year = race_year - 1
        prior_year_contributions = "{:.0%}".format(total_funding / df_campaign_funding[(df_campaign_funding['Year'] == prior_year) & (df_campaign_funding['Campaign_type'] == race_type)]['amount'].sum() - 1)
        
        st.metric(
            label='**Total contributions & yearly change**', 
            value=formatted_funding, 
            delta=prior_year_contributions, 
            delta_color='normal'
        )

        total_reporters = filtered_campaign_funding_df['Reporter'].nunique()
        prior_year_contributors = "{:.0%}".format(total_reporters / df_campaign_funding[(df_campaign_funding['Year'] == prior_year) & (df_campaign_funding['Campaign_type'] == race_type)]['Reporter'].nunique() - 1)

        st.metric(
            label='**Total contributors & yearly change**', 
            value=total_reporters, 
            delta=prior_year_contributors, 
            delta_color='normal')

    with subcol_right:
        altair_campaign_funding = alt.Chart(df_campaign_funding).mark_arc(innerRadius=50,padAngle=0.02).encode(
            theta=alt.Theta('amount:Q'),
            color=alt.Color('Reporter',legend=None, scale=alt.Scale(range=['#1AAE74ff','#24B079ff','#2EB27Eff','#38B483ff','#42B789ff','#4BB98Eff','#55BB93ff','#5FBD98ff','#69BF9Dff','#73C1A2ff','#7DC3A7ff','#87C5ACff','#91C8B2ff','#9ACAB7ff','#A4CCBCff','#AECEC1ff','#B8D0C6ff'])), 
            tooltip=[alt.Tooltip('Reporter:N', title='Reporter'),
                alt.Tooltip('amount:Q', format='$,.0f', title='Amount')],
            order=alt.Order('amount', sort='descending')
        ).properties(
            title=alt.Title(text='Campaign monetary contrubutions'),
            padding={"left": 0, "top": 50, "right": 0, "bottom": 0},
            height=350,
        ).transform_filter(
            (alt.datum.Year == race_year) & (alt.datum.Campaign_type == race_type)
        )
        
        st.altair_chart(altair_campaign_funding, use_container_width=True)

    ''
    st.divider()
    ''
    ''
    
    st.header('City Service Requests')

    # Ciry Service Requests
    url_service_requests = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=1661792648#gid=1661792648'
    df_service_requests = conn.query('''
                                     select Month_date, Category, Status, Count
                                     from "City Service requests" 
                                     ''', spreadsheet=url_service_requests)
    df_service_requests['Status'] = df_service_requests['Status'].replace(['EVALUATED - NO FURTHER ACTION', 'GONE ON ARRIVAL'], 'CLOSED')
    df_service_requests['Status'] = df_service_requests['Status'].replace(['WOCREATE'], 'PENDING')
    df_service_requests['Year'] = pd.to_datetime(df_service_requests['Month_date']).dt.year
    
    # st.write(df_service_requests)
    
    ## Service requests data editor
    
    # Filter and aggregate data for 2023 and 2024
    df_service_requests_aggregated = df_service_requests[(df_service_requests['Year'].isin([ 2023, 2024]))].groupby(['Category']).agg({'Count': list}).reset_index()
    df_status_sum_rates = df_service_requests[(df_service_requests['Year'].isin([2023, 2024]))].groupby(['Category','Status']).agg({'Count': sum}).reset_index()
    # Pivot the Count in df_status_sum_rates by Status
    df_status_sum_rates_pivot = df_status_sum_rates.pivot(index='Category', columns='Status', values='Count').reset_index()

    # Sum the 'Count' array into a new column
    df_service_requests_aggregated['Total'] = df_service_requests_aggregated['Count'].apply(lambda x: sum(x))
    # Join the columns OPEN and CLOSED to df_service_requests_aggregated from df_status_sum_rates_pivot joining on 'Category'
    df_service_requests_aggregated = df_service_requests_aggregated.merge(df_status_sum_rates_pivot, on='Category', how='left')
    df_service_requests_aggregated['Closed Rate'] = (df_service_requests_aggregated['CLOSED'] / df_service_requests_aggregated['Total']).apply(lambda x: "{:.0%}".format(x))
    
    # Trim and reorder the columns
    df_service_requests_aggregated = df_service_requests_aggregated[['Category', 'Total', 'Closed Rate', 'Count']]
    # Sort by Total
    df_service_requests_aggregated = df_service_requests_aggregated.sort_values(by='Total', ascending=False)

    st.data_editor(
        df_service_requests_aggregated,
        column_config={
            "Count": st.column_config.AreaChartColumn(
                "Requets (since 2023)",
                width="medium",
                help="Reuqests count since 2023",
                y_min=0,
                y_max=100,
            ),
        },
        hide_index=True,
    )



    # Abandoned vehicle service requests
    altair_abandoned_vehicle_servce_requests = alt.Chart(df_service_requests).mark_bar(
        width=15,  # Set the width of the bars
    ).encode(
        x=alt.X('Month_date:T', title=None),  # No title for x-axis
        y=alt.Y('Count:Q', title='Requests'),  # No title for y-axis,
        color=alt.Color(
            'Status:O', 
            scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']), 
            legend=alt.Legend(
                orient='bottom', 
                direction='horizontal', 
                labelFontSize=12, 
                labelOverlap=True), 
                title=None
                )
    ).properties(
        height=450,
        padding={"left": 30, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text="Abandoned vehicle service requests", anchor='start', dx=50) #, dy=0)
    ).transform_filter(
        (alt.datum.Category == 'Abandoned vehicle')
        & (alt.datum.Year >= 2022)
    )

    st.altair_chart(altair_abandoned_vehicle_servce_requests.interactive(), use_container_width=True)


    
    # Street repair service requests
    altair_street_repair_servce_requests = alt.Chart(df_service_requests).mark_bar(
        width=15,  # Set the width of the bars
    ).encode(
        x=alt.X('Month_date:T', title=None),  # No title for x-axis
        y=alt.Y('Count:Q', title='Requests'),  # No title for y-axis,
        color=alt.Color(
            'Status:O', 
            scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']), 
            legend=alt.Legend(
                orient='bottom', 
                direction='horizontal', 
                labelFontSize=12, 
                labelOverlap=True), 
                title=None
                )
    ).properties(
        height=450,
        padding={"left": 30, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text="Street repair service requests", anchor='start', dx=50) #, dy=0)
    ).transform_filter(
        (alt.datum.Category == 'Street Repair/Maintenance')
        & (alt.datum.Year >= 2022)
    )

    st.altair_chart(altair_street_repair_servce_requests.interactive(), use_container_width=True)
    
    
    