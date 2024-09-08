from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time, datetime, scipy


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
        '**Year filter** (will filter applicable charts only)',
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
    ANNOTATIONS = [
        ("Jan 05, 2015", "Libby Schaaf 1st term"),
        ("Jan 07, 2019", "Libby Schaaf's 2nd term"),
        ("Mar 17, 2020", "COVID-19 lockdown + restrictions encated"),
        ("Jan 09, 2023", "Sheng Tao + Pamela Price assume office"),
    ]

    # Create a chart with annotations
    annotations_df = pd.DataFrame(ANNOTATIONS, columns=["date_month", "event"])
    annotations_df.date_month = pd.to_datetime(annotations_df.date_month)
    annotations_df["y"] = 0
    annotation_layer = (
        alt.Chart(annotations_df)
        .mark_text(size=20, text="⬇️", dx=0, dy=-100, align="center")
        .encode(
            x="date_month:T",
            y=alt.Y("y:Q"),
            tooltip=["event"],
        )
        .interactive()
    )

    # Altair line chart
    altair_crimeChart = alt.Chart(filtered_crime_df).mark_line(interpolate="monotone").encode(
        x=alt.X('date_month', title=None),  # No title for x-axis
        y=alt.Y('count', title='Crime count'),  # No title for y-axis
        color=alt.Color('crimetype',legend=alt.Legend(title=None, orient='bottom', labelFontSize=12, labelOverlap=True))
    ).properties(
        title='Crime Counts by month for top crime types',
        height=400
    )

    st.altair_chart((altair_crimeChart + annotation_layer).interactive(), use_container_width=True)
    # st.altair_chart(altair_crimeChart, use_container_width=True)


with col2:
    # Add some spacing
    ''
    ''

    url_campaign_funding = 'https://docs.google.com/spreadsheets/d/18UO3R-DiBSUqNyHCIMP5HgmCQcpNd0su1IUDsyZkvNI/edit?gid=645810962#gid=645810962'
    df_campaign_funding = conn.query('''
                                     select From_Date, Committee_Type, Filer_NamL as Reporter, sum(Amount_A) as amount 
                                     from "Campaign finance summary totals" 
                                     where Line_Item = '3' and Form_Type in ('A','B1','C','D','E','F','G','H','I')
                                     group by 1,2,3
                                     ''', spreadsheet=url_campaign_funding)
    df_campaign_funding['From_Date'] = pd.to_datetime(df_campaign_funding['From_Date'])
    # st.dataframe(df_campaign_funding)
    
    codes = df_campaign_funding['Committee_Type'].unique()

    if not len(codes):
        st.warning("Select at least one country")
    
    selected_codes = st.multiselect(
        'Which Committee Types would you like to view?',
        codes,
        ['CAO', 'CTL', 'RCP', 'BMC'])
    
    # Filter the data
    filtered_campaign_funding_df = df_campaign_funding[
        (df_campaign_funding['Committee_Type'].isin(selected_codes))
        & (df_campaign_funding['From_Date'] <= pd.to_datetime(to_year, format='%Y'))
        & (pd.to_datetime(from_year, format='%Y') <= df_campaign_funding['From_Date'])
    ]

    # extract year from From_Date as string into new column 'Year'
    filtered_campaign_funding_df['Year'] = filtered_campaign_funding_df['From_Date'].dt.year.astype(str)

    altair_campaign_funding = alt.Chart(filtered_campaign_funding_df).mark_bar(cornerRadius=3).encode(
        x=alt.X('Year', title=None, axis=alt.Axis(labelAngle=45)),  # Tilt x-axis labels 90 degrees
        y=alt.Y('amount', title=None, axis=alt.Axis(format='$,.2r')),  # No title for y-axis
        color=alt.Color('Reporter',legend=None)
    ).properties(title='Campaign funding by year', height=400)
    st.altair_chart(altair_campaign_funding, use_container_width=True)

    # progress_bar = st.sidebar.progress(0)
    # status_text = st.sidebar.empty()
    # last_rows = np.random.randn(1, 1)
    # chart = st.line_chart(last_rows)

    # for i in range(1, 20):
    #     new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
    #     # status_text.text("%i%% Complete" % i)
    #     chart.add_rows(new_rows)
    #     # progress_bar.progress(i)
    #     last_rows = new_rows
    #     time.sleep(0.05)
    # st.dataframe(last_rows)
    # progress_bar.empty()

    # # Streamlit widgets automatically run the script from top to bottom. Since
    # # this button is not connected to any other logic, it just causes a plain
    # # rerun.
    # st.button("Re-run")






