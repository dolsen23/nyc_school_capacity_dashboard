import streamlit as st
from utils.data_processing import prep_city_data, create_district_dict, clean_data, clean_geodata, create_plot_df, format_geojson, load_data, process_data
from utils.visualizations import choropleth, bar_chart, pie_chart


# --- Functions ---

@st.cache_data
def prep_data():
    """Loads, cleans, and processes data for plotting; cached for faster performance"""
    # Load in dataframe and geodataframe
    df, geodf = load_data()
    # Clean geodataframe
    clean_geodf = clean_geodata(geodf)
    # Format geodata
    formatted_geodata = format_geojson(clean_geodf)
    # Clean dataframe
    clean_df = clean_data(df)
    # Process dataframe for choropleth and bar chart visualizations
    processed_data = process_data(clean_df)
    # Create dataframe used for choropleth and bar chart
    plotting_df = create_plot_df(processed_data, clean_geodf)
    # Calculate district statistics and store in dictionary
    district_stats_dict = create_district_dict(processed_data, plotting_df)
    # Calculate citywide statistics and store in dictionary
    city_stats_dict = prep_city_data(plotting_df, processed_data)

    return plotting_df, formatted_geodata, processed_data, city_stats_dict, district_stats_dict


def citywide_summary(city_stats):
    """Lays out citywide summary panel"""

    st.subheader('Citywide Summary')

    # Positions top row of stats
    col1, col2, col3 = st.columns(3)
    col1.metric('Total Buildings Measured', city_stats['total_bldgs'])
    col2.metric('Overcapacity Buildings', city_stats['total_overcapacity'])
    col3.metric('Percent Overcapacity', f"{city_stats['pct_overcapacity']}%")

    # Generates pie chart of overcapacity ranges
    st.plotly_chart(pie_chart(city_stats, legend_x=0.85), use_container_width=True)

    # Positions bottom row of stats
    st.markdown('**Citywide Averages**')
    col8, col9, col10 = st.columns(3)
    col8.metric('Median Building Utilization', f"{city_stats['median_bldg_util']}%")
    col9.metric('Median Buildings per District', int(city_stats['median_bldgs']))
    col10.metric('Median District Overcapacity Rate', f"{city_stats['median_district_pctovercap']}%")

def district_summary(district_num, plot_df, district_data):
    """Lays out district level summmary panel"""

    st.subheader(f'District {district_num} Summary')
    
    # Lay out top row, containing geographic information
    col1, col2 = st.columns([1, 2])
    col1.markdown(f"**Borough:**<br>{plot_df.loc[district_num, 'Borough']}", unsafe_allow_html=True)
    col2.markdown(f"**Neighborhoods:**<br>{plot_df.loc[district_num, 'Neighborhoods'].replace('<br>', ' ')}", unsafe_allow_html=True)

    # Lay out middle row of stats
    st.markdown('#### Key Statistics')
    col3, col4, col5 = st.columns(3)
    col3.metric('Total Buildings Measured', district_data['total_bldgs'])
    col4.metric('Overcapacity Buildings', district_data['total_overcapacity'])
    col5.metric('Percent Overcapacity', f"{district_data['pct_overcapacity']}%")

    # Lay out bottom row of stats
    col6, col7, col8 = st.columns(3)
    col6.metric(
        'Rank by Overcapacity',
        int((plot_df.loc[plot_df['SchoolDist'] == district_num, 'RankByOverCapacity']).iloc[0]),
        help='Rank 1 = highest percentage of overcapacity buildings'
    )
    col7.metric('Median Building Utilization', f"{district_data['median_bldg_util']}%")
    col8.metric('Max Building Utilization', f"{district_data['max_bldg_util']}%")
    
    # Generates pie chart of overcpacity ranges; if no buildings are overcapacity, displays info box in lieu of pie chart
    if district_data['total_overcapacity'] == 0:
        st.info('All buildings in this district are at or below capacity.')
    else:
        st.plotly_chart(pie_chart(district_data, legend_x=0.7))

    # Displays school directory dataframe in an expander box
    with st.expander("View Detailed District Building Data"):
        st.dataframe(
            district_data['dataframe'],
            hide_index=True,
            column_config={
                'Capacity': st.column_config.NumberColumn(
                    width=20
                ),
                'Enrollment': st.column_config.NumberColumn(
                    width=20
                ),
                'Over Capacity?': st.column_config.CheckboxColumn(
                    width=20
                ),
                'Utilization': st.column_config.NumberColumn(
                    format='percent',
                    width=20
                ),
            }
        )


# --- Initialization ---

# Readies data
plot_df, geodata, processed_df, city_stats, district_stats = prep_data()

# Sets page configuration settings
st.set_page_config(
    page_title='NYC School Building Utilization',
    layout='wide'
)


# --- Page Heading ---

st.title('NYC Public School Building Utilization Dashboard')
st.markdown("*Utilization* is defined as the ratio of a building's enrollment to its designated capacity. \
            This dashboard examines utilization rates across the 32 NYC public school districts, highlighting \
            the number of buildings operating over their designated capacity (i.e., with utilization greater \
            than 100%). Data is sourced from NYC Open Data's \"Enrollment Capacity and Utilization Reports\" \
            dataset and reflects the most recently available reporting.")
st.divider()


# --- Choropleth & Citywide Summary ---

col1, col2 = st.columns(2, gap='medium')

# Displays choropleth in top left column
with col1:
    st.subheader('Percentage of Overcapacity School Buildings by NYC School District, 2023')
    st.plotly_chart(choropleth(plot_df, geodata), use_container_width=True)
    st.markdown('***Intrepretation:*** This map shows the percentage of overcapacity school buildings in each of the thirty-two NYC public school districts for 2023.\
                Green shades indicate lower overcapacity, while red shades indicate higher overcapacity. The color scale is centered at the citywide median district\
                overcapacity rate of 25%.')

# Displays citywide summary in top right column
with col2:
    citywide_summary(city_stats)

st.divider()


# --- Bar Chart ---
st.subheader('Overcapacity Rate by District')

# Radio menu for selecting ordering of x-axis in bar chart
x_order = st.radio(
    label='Select Preferred Ordering for x-axis',
    options=['By Borough', 'By Over-Capacity Percentage (least to greatest)', 'By Over-Capacity Percentage (greatest to least)']
)
# Turns on/off horizontal bar at median district overcapaity level
display_median = st.checkbox('Display median')

# Displays bar chart
fig_bar = bar_chart(plot_df, x_order, city_stats, display_median, city_stats['median_district_pctovercap'])
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()


# --- District Summary ---

# Selectbox allows user to select district for district level summary (values from 1-32)
district_num = st.selectbox(label='Select district', options=sorted(district_stats.keys()))

# Displays district summary for selected district
district_summary(district_num, plot_df, district_stats[district_num])

st.divider()


# --- Footnote ---
st.markdown(
    "**Data:** Sourced from [NYC Open Data](https://data.cityofnewyork.us/Education/Enrollment-Capacity-And-Utilization-Reports/gkd7-3vk7/about_data).\n\n",
    unsafe_allow_html=True
)
st.markdown('**Methodology:** Only buildings with reported enrollment and capacity data in 2023 were included, \
    and only buildings with utilization greater than 0% are considered.')