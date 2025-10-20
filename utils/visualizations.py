import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def choropleth(df, geodata):
    """Creates choropleth"""

    #Set up choropleth
    fig_map = px.choropleth(
        data_frame=df,
        geojson=geodata,
        locations='SchoolDist',
        color='PctOverCapacity',
        featureidkey='properties.SchoolDist',
        color_continuous_scale = [
            (0.0, "#2ECC71"),   
            (0.25, "#F4EBD0"),  
            (1.0, "#C0392B")    
        ],
        custom_data=['Borough', 'Neighborhoods', 'OverCapacity', 'Total Bldgs', 'PctOverCapacity']
    )

    # Add title, adjust margin, and set template
    fig_map.update_layout(
        height=500,
        margin={'r':0, 't':0, 'l':0, 'b':0},
        template='plotly_dark',
    )

    # Settings for hover label
    fig_map.update_traces(
        hovertemplate='<b>District %{location}</b>'+
        '<br><i>%{customdata[0]}</i>'+
        '<br>%{customdata[1]}'+
        '<br><br>Over-Capacity Buildings: %{customdata[2]}'+
        '<br>Total Buildings: %{customdata[3]}'+
        '<br>Percent Over-Capacity: %{customdata[4]}%',
        hoverlabel=dict(
            bgcolor='rgba(230, 245, 233, 0.9)',
            font_color='black'
        )
    )

    # Overlay numeric district labels on choropleth
    fig_map.add_trace(go.Scattergeo(
        lon=df['label_lon'],
        lat=df['label_lat'],
        text=['<b>{}</b>'.format(d) for d in df['SchoolDist']],
        mode='text',
        textfont=dict(color='black', size=10.5, family='Helvetica'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Set title for coloraxes
    fig_map.update_coloraxes(colorbar_title='Percent<br>Over-Capacity')

    # Set default map bounds
    fig_map.update_geos(fitbounds='locations', visible=False)

    return fig_map


def bar_chart(df, x_order, stats_dict, display_median, median):
    """Creates bar chart"""

    borough_order = ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']
    df['Borough'] = pd.Categorical(df['Borough'], categories=borough_order, ordered=True)

    # Set x-axis ordering based on radio menu selection
    if x_order == 'By Borough':
        df_sorted = df.sort_values(["Borough", "SchoolDist"])
    elif x_order == 'By Over-Capacity Percentage (least to greatest)':
        df_sorted = df.sort_values('PctOverCapacity')
    elif x_order == 'By Over-Capacity Percentage (greatest to least)':
        df_sorted = df.sort_values('PctOverCapacity', ascending=False)

    # Set up bar graph
    fig_bar = px.bar(
    data_frame=df_sorted,
    x='SchoolDist',
    y='PctOverCapacity',
    color='Borough',
    text=df_sorted['PctOverCapacity'].round(0),
    labels={
        'SchoolDist': 'School District',
        'PctOverCapacity': 'Percent Over-Capacity'
    },
    custom_data=['Borough', 'Neighborhoods', 'OverCapacity', 'Total Bldgs', 'PctOverCapacity'],
    category_orders={
        "SchoolDist": list(df_sorted['SchoolDist']),
        "Borough": ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
        }
    )

    # Set x-axis data type to categorical to ensure that all district labels are displayed
    fig_bar.update_xaxes(type='category')

    # Settings for hover label
    fig_bar.update_traces(
        hovertemplate='<b>District %{x}</b>'+
        '<br><i>%{customdata[0]}</i>'+
        '<br>%{customdata[1]}'+
        '<br><br>Over-Capacity Buildings: %{customdata[2]}'+
        '<br>Total Buildings: %{customdata[3]}'+
        '<br>Percent Over-Capacity: %{customdata[4]}%'+
        '<extra></extra>',
        hoverlabel=dict(
        bgcolor='rgba(230, 245, 233, 0.9)',
        font_color='black',
        )
    )

    # Set bar text to renders above bars; 'cliponaxis=False' ensures text on highest bar renders correctly
    fig_bar.update_traces(
        textposition='outside',
        cliponaxis=False
    )

    # Change hover mode to 'x' to ensure that hover labels display for all bars, including those of height = 0
    fig_bar.update_layout(
        hovermode='x'
    )

    # If checkbox is checked, draw horizontal line at median of district over-capacity percentage
    if display_median:
        fig_bar.add_hline(
            y=median,
            line_dash='dash',
            line_color='white',
            line_width=2,
            annotation_text='Median: ' + median.astype(str) + '%',
            annotation_position='bottom right',
            annotation_font_color='white',
            annotation_bgcolor='rgba(0,0,0,0.6)' 
            )

    return fig_bar

def pie_chart(stats_dict, legend_x):
    """Creates pie chart"""
    
    data = pd.DataFrame({
        'ranges': ['101-110%', '111-120%', '121-130%', '131%+'],
        'percents': [
            stats_dict['pct_util_101_110'],
            stats_dict['pct_util_111_120'],
            stats_dict['pct_util_121_130'],
            stats_dict['pct_util_131_plus']
        ],
        'counts': [
        stats_dict['num_util_101_110'],
        stats_dict['num_util_111_120'],
        stats_dict['num_util_121_130'],
        stats_dict['num_util_131_plus']
        ]
    })

    

    # Set up pie chart
    fig_pie = px.pie(
        data_frame=data,
        values='percents',
        names='ranges',
        hole=0.3,
        color='ranges',
        color_discrete_map={
            '101-110%': '#fff3b0',
            '111-120%': '#feca57', 
            '121-130%': '#ff6b6b', 
            '131%+': '#c5283d',     
        },
        category_orders={'ranges': ['101-110%', '111-120%', '121-130%', '131%+']},
        custom_data=['counts']
    )

    # Set up textual overlays & hoverlabel
    fig_pie.update_traces(
        textinfo='label+percent',
        textposition='inside',
        hovertemplate='Range: %{label}<br>Buildings: %{customdata[0][0]}<extra></extra>',
        hoverlabel=dict(
        bgcolor='rgba(230, 245, 233, 0.9)',
        font_color='black',
        )
    )

    # Set up title, legend
    fig_pie.update_layout(
    title=dict(
        text=f"Breakdown of Utilization in Overcapacity Buildings ({stats_dict['pct_overcapacity']}% of Buildings Overcapacity)",
        x=0.5,
        xanchor='center'
    ),
    margin={'r':50, 't':80, 'l':50, 'b':50},
    legend_title_text='Utilization Range',
    legend=dict(
        x=legend_x,     # Uses legend_x argument to determine horizontal position of legend; set to 0.85 for citywide summary and 0.7 for district summary  
        xanchor='left',      
    )
    )

    return fig_pie