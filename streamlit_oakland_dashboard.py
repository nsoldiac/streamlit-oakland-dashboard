from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import altair as alt
import datetime, textwrap #, scipy, time

st.set_page_config(layout="wide")


st.image('big_logo.png')
st.markdown(
    "<span style='font-style:italic; font-size:20px; color:gray;'>💡 Empower Oakland's 2024 <a href='https://empoweroakland.com/voter-guide/' target='_blank'>Voter Guide</a> is live. Check it out for more information on the candidates and measures on the ballot.</span>",
    unsafe_allow_html=True
)



st.subheader('Oakland City Statistics')
st.write('''
Welcome to Empower Oakland's city statistics dashboard. This dashboard provides a central location for siloed and disconnected data sources. This dashboard attempts to show a picture of how Okland is doing today vs the past.
''')
''
# Sidebar here 👇
# st.sidebar.text("Use the sidebar to select the data you want to see")


col1, col2 = st.columns(2, gap='large')

with col1:
    
    st.header('Crime Activity and Response')

    min_value = 2015 
    max_value = datetime.datetime.now().year 

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

    # Altair line chart
    altair_crimeChart = alt.Chart(filtered_crime_df).mark_line(interpolate="monotone").encode(
        x=alt.X('date_month', title=None),  # No title for x-axis
        y=alt.Y('count', title='Crime count'),  # No title for y-axis,
        color=alt.Color('crimetype', scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']), legend=alt.Legend(title=None, orient='bottom', direction='horizontal', labelFontSize=12, labelOverlap=True))
    ).properties(
        height=450,
        padding={"left": 15, "top": 0, "right": 0, "bottom": 0},
        title=alt.Title(text='Crime Counts for top crime types', anchor='start', dx=45, subtitle="Source: Oakland Open Data Platform, OPD's CrimeWatch dataset")
    )

    # st.altair_chart((altair_crimeChart + annotation_layer).interactive(), use_container_width=True)
    st.altair_chart(altair_crimeChart.interactive(), use_container_width=True)
    # st.caption("_Source: [Oakland Police Department](https://data.oaklandnet.com/)_")
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
        title=alt.Title(text='Violent crime change vs prior year', anchor='start', dx=30, dy=-15, subtitle="Source: Oakland Police Department's crime dataset"),
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
        title=alt.Title(text="Average Police call to arrival in minutes", anchor='start', dx=30, subtitle="Source: OPD's Supplemental Biannual Staffing Report (updated September 2023)") 
    )

    # st.altair_chart((altair_crimeChart + annotation_layer).interactive(), use_container_width=True)
    st.altair_chart(altair_opd_call_wait.interactive(), use_container_width=True)




with col2:
    st.header('Campaign Funding Reporting')
    st.caption("Source: Oakland Open Data Platform, Public Ethics Commission's Candidate Contributions (Show Me the Money) dataset")

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

    st.divider()
    ''
    
    st.header('City Service Requests')
    st.caption("Source: Oakland Open Data Platform, Public Works/Department of Transportation's Service requests received by the Oakland Call Center dataset")

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
    
    ''
    
    # Select a category for detailed breakdown
    service_category = st.selectbox('**Select a category for detailed breakdown below**', df_service_requests_aggregated['Category'].unique(), index=1)

    # Total service requests
    altair_service_requests = alt.Chart(df_service_requests).mark_bar(
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
        height=400,
        padding={"left": 40, "top": 0, "right": 0, "bottom": 0},
        # title=alt.Title(text=None) #, dy=0)
    ).transform_filter(
        (alt.datum.Category == service_category)
        & (alt.datum.Year >= 2022)
    )

    st.altair_chart(altair_service_requests.interactive(), use_container_width=True)
        
st.divider()
''
st.header('Mapping criminal activity over time')
st.caption("Source: Oakland Open Data Platform, OPD's CrimeWatch dataset")

url_crime_map = 'https://docs.google.com/spreadsheets/d/1Ye0jVwOa_aAK6AvOoXKBy9AOe0VxldjudldyLhIkyaE/edit?usp=sharing'
df_crime_map = conn.query('''
                            select CrimeType, DateQuarter, Latitude, Longitude
                            from "Crime map" 
                            where 
                                Latitude is not null
                                and Longitude is not null
                                and CrimeType is not null
                            ''', spreadsheet=url_crime_map)

col_mapping_1, col_mapping_2 = st.columns([1,2], vertical_alignment="top")

mapping_crime_type = col_mapping_1.selectbox(
    "**Select a crime type**",
    sorted(df_crime_map['CrimeType'].unique()),
    index=7)

mapping_crime_quarter = col_mapping_2.select_slider(
    '**Time of reporting (in yearly quarters)**',
    options = sorted(df_crime_map['DateQuarter'].unique()),
)

# Filter df_crime_map based on user inputs above
filtered_crime_map = df_crime_map[
    (df_crime_map['CrimeType'] == mapping_crime_type)
    & (df_crime_map['DateQuarter'] == mapping_crime_quarter)
    ]

# st.write(filtered_crime_map)

chart_data = filtered_crime_map[['Latitude', 'Longitude']]

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=37.8,
            longitude=-122.24,
            zoom=10.8,
            pitch=30,
        ),
        layers=[
            pdk.Layer(
                # "HexagonLayer",
                "HeatmapLayer",
                opacity=0.2,
                data=chart_data,
                get_position="[Longitude, Latitude]",
                radius=300,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            # pdk.Layer(
            #     "ScatterplotLayer",
            #     data=chart_data,
            #     get_position="[Longitude, Latitude]",
            #     get_color="[200, 30, 0, 160]",
            #     get_radius=150,
            # ),
        ],
    )
)

''
''

st.divider()
''

st.markdown('''
# 2024 Campaign Expenditure Reporting
The following section shows aggregated and detailed campaign expenditures for offices up in this 2024 election cycle. The data is sourced from the Oakland Open Data Platform, originally published by the Public Ethics Commission's Candidate Expenditure's ("Show Me The Money") dataset.
''')

url_campaign_expenditures = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=101441109#gid=101441109'
df_campaign_expenditures = conn.query('''
                                     select *
                                     from "Candidate Expenditures" 
                                     ''', spreadsheet=url_campaign_expenditures
                                     )

df_campaign_expenditures['expenditure_date'] = pd.to_datetime(df_campaign_expenditures['expenditure_date'])

col_race_office_1, col_race_office_2 = st.columns([1,2], vertical_alignment="top")
race_expense_office = col_race_office_1.selectbox(
    "**Select an Office race**",
    df_campaign_expenditures['office'].unique(),
    index=1)

race_expense_committee_type = col_race_office_2.multiselect(
    "**Select Committee Types**",
    df_campaign_expenditures['committee_type_name'].unique(),
    df_campaign_expenditures['committee_type_name'].unique())

filtered_expenditures_df = df_campaign_expenditures[['expenditure_date', 'committee_name','committee_type_name','amount','filer_name','recipient_name','expenditure_type','expenditure_description','office','jurisdiction','expenditure_month_date']]
filtered_expenditures_df = filtered_expenditures_df[
    (filtered_expenditures_df['office'] == race_expense_office) 
    & (filtered_expenditures_df['committee_type_name'].isin(race_expense_committee_type))
]
# Wrap text in the 'label' column
filtered_expenditures_df["committee_name_wrapped"] = filtered_expenditures_df["committee_name"].apply(lambda x: "|".join(textwrap.wrap(x, width=25)))
filtered_expenditures_df['expenditure_month_date'] = pd.to_datetime(filtered_expenditures_df['expenditure_month_date'], errors='coerce')
filtered_expenditures_df['expenditure_month_date_str'] = filtered_expenditures_df['expenditure_month_date'].dt.strftime('%m - %B')

''

col_expenditures_left, col_expenditures_right = st.columns([2,1], vertical_alignment="top")

with col_expenditures_left:
    # Bar chart for aggregated campaign expenditures
    altair_campaign_expenditures = alt.Chart(filtered_expenditures_df).mark_bar(
        # width=35,  # Set the width of the bars
        stroke='white',
        strokeWidth=1
    ).encode(
        x=alt.X('expenditure_month_date_str:N', title=None), 
        y=alt.Y('sum(amount):Q', title='Expenditure Amount', axis=alt.Axis(format='$,.0f')),  
        color=alt.Color(
            'committee_name_wrapped:N', 
            scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']),
            legend=alt.Legend(
                orient='right', 
                title='Committee Name',
                titleFontWeight='bold',
                direction='vertical', 
                labelExpr="split(datum.label, '|')",
                labelSeparation=10,
            )
        ), 
        order=alt.Order('amount', sort='descending'),
        tooltip=[
            alt.Tooltip('committee_name:N', title='Committee Name'), 
            alt.Tooltip('amount:Q', format='$,.0f', title='Expense amount'),
            alt.Tooltip('expenditure_type:N', title='Expense type'),
            alt.Tooltip('committee_type_name:N', title='Expense type'),
            # alt.Tooltip('expenditure_month_date:N', format='%B, 2024', title='Expense month'),
            ],
    ).properties(
        height=450,
        title=alt.Title(text='Detailed campaign monetary contrubutions over time'),
        # padding={"left": 40, "top": 0, "right": 0, "bottom": 0},
        # title=alt.Title(text=None) #, dy=0)
    )

    yzoom = alt.selection_interval(encodings=['y'], bind="scales", zoom="wheel![event.altKey]")
    altair_campaign_expenditures.add_params(yzoom)
    st.altair_chart(altair_campaign_expenditures.interactive(), use_container_width=True)

with col_expenditures_right:
    agg_filtered_expenditures_df = filtered_expenditures_df.groupby(['committee_name']).agg({'amount': sum}).reset_index()
    altair_expenditures_arc = alt.Chart(agg_filtered_expenditures_df).mark_arc(
        innerRadius=50,padAngle=0.02
        ).encode(
            theta=alt.Theta('amount:Q'),
            color=alt.Color(
                'committee_name:N', 
                scale=alt.Scale(range=['#1AAE74', '#1C2628', '#EB5E55', '#7C6C77', '#477998']),
                legend=None
            ), 
            tooltip=[
                alt.Tooltip('committee_name:N', title='Committee Name'), 
                alt.Tooltip('amount:Q', format='$,.0f', title='Expense amount')
                ],
            order=alt.Order('amount', sort='descending')
        ).properties(
            title=alt.Title(text='Total campaign monetary contrubutions'),
            # padding={"left": 0, "top": 50, "right": 0, "bottom": 0},
            height=350,
        )
        
    st.altair_chart(altair_expenditures_arc, use_container_width=True)

# Table for detailed campaign expenditures
st.data_editor(
    filtered_expenditures_df[filtered_expenditures_df.columns.difference(['committee_name_wrapped','expenditure_month_date_str','expenditure_month_date'])],
    hide_index=True,
    column_config={
        "amount": st.column_config.NumberColumn(
            "Amount (in USD)",
            help="The amount of the expenditure",
            format="$%.2f",
        )
    },
)