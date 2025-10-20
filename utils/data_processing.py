import json
import pandas as pd
import geopandas as gpd
import warnings


# List of neighborhoods served by each district, ordered by district number
# List elements will eventually be read as HTML, so <br> tags are used in place of newlines
NEIGHBORHOODS = [
    'East Village, Lower East Side',
    'Financial District, Tribeca,<br>West Village, Clinton,<br>Midtown, Gramercy,<br>Upper East Side',
    'Lincoln Square, Upper West Side',
    'East Harlem, Randall\'s Island',
    'Central Harlem, Morningside Heights',
    'Inwood, Washington Heights',
    'Mott Haven, Port Morris',
    'Country Club, Edgewater Park,<br>Soundview, Hunts Point',
    'Morris Heights, Mount Eden',
    'Riverdale, Bedford Park,<br>Norwood',
    'Wakefield, Co-op City,<br>Pelham Parkway',
    'East Tremont, Claremont Village',
    'Brooklyn Heights, Fort Greene,<br>Clinton Hill',
    'Greenpoint, Williamsburg',
    'Sunset Park, Cobble Hill',
    'Bedford Stuyvesant, Weeksville',
    'Prospect Park, Wingate',
    'Canarsie, East Flatbush',
    'Cypress Hills, East New York,<br>Starrett City',
    'Bay Ridge, Fort Hamilton,<br>Dyker Heights',
    'Coney Island, Sheepshead Bay,<br>Gravesend, Ocean Parkway',
    'Marine Park, Georgetown,<br>Flatlands',
    'Brownsville, Ocean Hill',
    'Glendale, Ridgewood,<br>Maspeth, Jackson Heights,<br>Sunnyside',
    'College Point, Whitestone,<br>Hillcrest',
    'Floral Park, Little Neck,<br>Bayside, Fresh Meadows',
    'Richmond Hill, Woodhaven,<br>Howard Beach, South Ozone Park',
    'Rego Park, Forest Hills,<br>Kew Gardens',
    'Rosedale, Saint Albans,<br>Cambria Heights, Queens Village',
    'Hunters Point, Long Island City,<br>Astoria, Steinway',
    'Staten Island',
    'Bushwick'
    ]


def load_data():
    """Loads in csv as DataFrame and shapefile as GeoDataFrame"""
    df = pd.read_csv('data/Enrollment_Capacity_And_Utilization_Reports.csv')
    geodf = gpd.read_file('data/nysd_25c/nysd.shp')
    return df, geodf


def clean_data(df):
    """Cleans DataFrame to ready for further processing; returns separate dataframes for visualizations and district summary"""
    
    clean_df = df.copy()

    # Convert dates in 'Data As Of' column from Pandas object to datetime64
    clean_df['Data As Of'] = pd.to_datetime(clean_df['Data As Of'], format='%m/%d/%Y')

    # Filter rows where year is 2023
    clean_df = clean_df[clean_df['Data As Of'].dt.year == 2023]

    # Drop rows with na values in utilization column
    clean_df = clean_df.dropna(subset=['Target Bldg Util'])

    # Drop rows where the Building Utilization is 0
    # These outliers likely represent closed or not yet opened school buildings
    clean_df = clean_df[clean_df['Target Bldg Util'] != 0]

    # Consolidates clean_df by using groupby to merge rows representing schools houses in the same building
    # Also drops the following columns: 'Org_ID', 'Incl. Class', 'Org Enroll', 'Org Target Cap', 'Org Target Util',
    # 'PreK Cap', 'No. of Cluster / Spec Rms Reported', 'No. of Cluster Rms Needed'
    clean_df = clean_df.groupby(['Bldg ID', 'Bldg Name', 'Geo Dist', 'Bldg Enroll', 'Target Bldg Cap', 'Target Bldg Util', 'Data As Of'])\
    ['Organization Name'].agg(lambda x: ', '.join(sorted(x))).reset_index()
    clean_df.index += 1

    clean_df = clean_df.rename(columns={'Geo Dist': 'SchoolDist', 'Organization Name': 'Schools In Bldg'})

    #clean_df now has eight columns:
        # SchoolDist: NYC School District (int64 from 1-32)
        # Bldg ID: Unique ID corresponding to each designated NYC DOE school building (object)
        # Bldg Name: Name of school building (object)
        # Bldg Enroll: Number of students enrolled in schools housed within the building (float64)
        # Schools In Bldg: Names of schools/orgs housed in building (object)
        # Target Bldg Cap: Student capacity for building (float64)
        # Target Bldg Util: (Bldg Enroll) / (Target Bldg Cap) (float64, rounded to nearest whole number)
        # Data As Of: Date of data collection (currently object, will be converted to datetime64)

    return clean_df


def process_data(cleaned_df):
    """Processes cleaned DataFrame; returns processed_df, a DataFrame that will be used to create plot_df and generate various statistics"""

    processed_df = cleaned_df.copy()

    # Add column of boolean values; value is True if building is over-capacity, False otherwise
    processed_df['OverCapacity'] = processed_df['Target Bldg Util'].apply(lambda x: True if (x > 100) else False)

    # Add four columns of Boolean values; value is True if building is within specified utilization range, False otherwise
    processed_df['Util_101_110'] = processed_df['Target Bldg Util'].apply(lambda x: True if ((x > 100) & (x <= 110)) else False)
    processed_df['Util_111_120'] = processed_df['Target Bldg Util'].apply(lambda x: True if ((x > 110) & (x <= 120)) else False)
    processed_df['Util_121_130'] = processed_df['Target Bldg Util'].apply(lambda x: True if ((x > 120) & (x <= 130)) else False)
    processed_df['Util_131plus'] = processed_df['Target Bldg Util'].apply(lambda x: True if (x > 130) else False)

    return processed_df


def create_plot_df(processed_df, cleaned_geodf):
    """Create new plot_df DataFrame with nine columns:
        # SchoolDist: NYC School District (int64 from 1-32)
        # OverCapacity: number of over-capacity school buildings in district (int64)
        # Total Bldgs: total number of school buildings in district (int64)
        # PctOverCapacity: percentage of school buildings over capacity in district (float64)
        # RankByOverCapacity: ranks districts by percent of overcapacity buildings (rank 1 = highest overcapacity percentage)
        # Borough: NYC Borough in which district is located (object)
        # Neighborhoods: NYC neighborhoods served by district (object)
        # label_lon: Longitude of district label (float64)
        # label_lat: Latitude of sitrict label (float64)"""

    # Initialize plot_df through merging on school district
        # left is a dataframe with a column of the total number of overcapacity buildings in each district
        # right is a dataframe with a column containing the total number of school buildings in each district
    plot_df = pd.merge(
        left=processed_df.groupby('SchoolDist')['OverCapacity'].sum(),
        right=processed_df.groupby('SchoolDist')['Bldg ID'].nunique(),
        on='SchoolDist'
    )

    # Reset table index to avoid issues when plotting
    plot_df = plot_df.reset_index()


    # Rename Bldg ID column for clarity
    plot_df = plot_df.rename(columns={'Bldg ID': 'Total Bldgs'})


    # Add column of percentages of over-capacity buildings for each district
    plot_df['PctOverCapacity'] = ((plot_df['OverCapacity'].astype(float) / plot_df['Total Bldgs'].astype(float)) * 100).round(2)

    # Add column for district overcapacity rank (rank 1 = most overcrowded district)
    plot_df['RankByOverCapacity'] = plot_df['PctOverCapacity'].rank(method='min', ascending=False)

    # Add Borough column to dataframe; assigns each district its corresponding Borough based on district number
    plot_df.loc[plot_df['SchoolDist'] <= 6, 'Borough'] = 'Manhattan'
    plot_df.loc[(plot_df['SchoolDist'] >= 7) & (plot_df['SchoolDist'] <= 12), 'Borough'] = 'Bronx'
    plot_df.loc[((plot_df['SchoolDist'] >= 13) & (plot_df['SchoolDist'] <= 23)) | (plot_df['SchoolDist'] == 32), 'Borough'] = 'Brooklyn'
    plot_df.loc[(plot_df['SchoolDist'] >= 24) & (plot_df['SchoolDist'] <= 30), 'Borough'] = 'Queens'
    plot_df.loc[plot_df['SchoolDist'] == 31, 'Borough'] = 'Staten Island'

    
    # Add column of neighborhoods served by each school district using NEIGHBORHOODS list
    plot_df['Neighborhoods'] = NEIGHBORHOODS

    # Suppress warning when calculating centroid for placing district labels on choropleth
    # This warning states that calculations for the centroid of district shapes may be inaccurate due to the chosen coordinate system
    # This is correct, but does not have a meaningful impact on functionality
    warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

    # Add label_lon and label_lat columns by calculating each district's centroid
    plot_df['label_lon'] = cleaned_geodf.geometry.centroid.x
    plot_df['label_lat'] = cleaned_geodf.geometry.centroid.y

    # Manually set specific label coordinates for legibility
    manual_coords = {
    4: (-73.938, 40.7925),
    13: (-73.969759, 40.687),
    15: (-73.991, 40.663772),
    27: (-73.797, 40.655), 
    }

    # Update label coordinates for districts spcified in manueal_coords dictionary
    for district, (new_lon, new_lat) in manual_coords.items():
        plot_df.loc[plot_df['SchoolDist'] == district, 'label_lon'] = new_lon
        plot_df.loc[plot_df['SchoolDist'] == district, 'label_lat'] = new_lat
    
    # Align index with district numbers
    plot_df.index += 1
    
    return plot_df


def clean_geodata(geodf):
    """Cleans geodataframe"""

    clean_geodf = geodf.copy()

    # Resolve issue where District 10 occupies two separate rows in geodataframe
    clean_geodf = clean_geodf.dissolve('SchoolDist').reset_index()

    # Convert geodataframe from EPSG:2263 to EPSG:4326 geographic coordinate system (gcs)
    # EPSG:4326 is the required coordinate system for Plotly's choropleth function
    clean_geodf = clean_geodf.to_crs(epsg=4326)

    return clean_geodf


def format_geojson(cleaned_geodf):
    """Converts cleaned geodataframe to Python dictionary formatted for Plotly"""

    return json.loads(cleaned_geodf.to_json())


def prep_city_data(plot_df, processed_df):
    """Prepares data for citywide summary panel. Generates various statistics. Returns dictionary with data to be displayed."""

    # Generate statistics
    total_bldgs = len(processed_df)     # total number of buildings citywide included in analysis

    num_overcapacity = processed_df['OverCapacity'].sum()      # total number of overcapacity buildings (buildings where utilization > 100%)

    pct_overcapacity = round((num_overcapacity / total_bldgs) * 100, 2)     # percentage of total buildings that are overcapacity

    mean_bldg_util = round(processed_df['Target Bldg Util'].mean(), 2)      # mean building utilization
    median_bldg_util = processed_df['Target Bldg Util'].median()            # median building utilization

    mean_bldgs_per_district = round(plot_df['Total Bldgs'].mean(), 2)       # mean number of school buildings per district
    median_bldgs_per_district = plot_df['Total Bldgs'].median()             # median number of school buildings per district
    median_district_pctovercap = plot_df['PctOverCapacity'].median()        # median district overcapacity rate (percent of buildings in district that are overcapacity)
    
    # Calculcate utilization ranges for overcapacity buildings; if no buildings are overcapacity, sets all four ranges to 0
    if num_overcapacity == 0:
        pct_101_110 = 0
        pct_111_120 = 0
        pct_121_130 = 0
        pct_131_plus = 0
    else:
        pct_101_110 = round((processed_df['Util_101_110'].sum() / num_overcapacity) * 100, 2)
        pct_111_120 = round((processed_df['Util_111_120'].sum() / num_overcapacity) * 100, 2)
        pct_121_130 = round((processed_df['Util_121_130'].sum() / num_overcapacity) * 100, 2)
        pct_131_plus = round((processed_df['Util_131plus'].sum() / num_overcapacity) * 100, 2)

    # Create dictionary to store citywide statistics
    city_stats = {
        'total_bldgs': total_bldgs,
        'total_overcapacity': num_overcapacity,
        'pct_overcapacity': pct_overcapacity,
        'num_util_101_110': processed_df['Util_101_110'].sum(),
        'num_util_111_120': processed_df['Util_111_120'].sum(),
        'num_util_121_130': processed_df['Util_121_130'].sum(),
        'num_util_131_plus': processed_df['Util_131plus'].sum(),
        'pct_util_101_110': pct_101_110,
        'pct_util_111_120': pct_111_120,
        'pct_util_121_130': pct_121_130,
        'pct_util_131_plus': pct_131_plus,
        'mean_bldg_util': mean_bldg_util,
        'median_bldg_util': median_bldg_util,
        'mean_bldgs': mean_bldgs_per_district,
        'median_bldgs': median_bldgs_per_district,
        'median_district_pctovercap': median_district_pctovercap
    }

    return city_stats

def prep_district_data(processed_df, plot_df, district_num):
    """Prepares data for district level summary panel. Generates various statistics. 
    Returns dictionary with data to be displayed, which will be added to district_dict below."""

    # Filters processed_df for values in district number corresponding to argument given for district_num
    filtered_df = processed_df[processed_df['SchoolDist'] == district_num]

    # Generate statistics
    total_bldgs = len(filtered_df)      # total number of school buildings in district included in analysis
    num_overcapacity = filtered_df['OverCapacity'].sum()    # total number of overcapacity buildings in district (buildings where utilizaion > 100%)
    pct_overcapacity = round((num_overcapacity / total_bldgs) * 100, 2)     # percent of buildings that are overcapacity
    
    # Calculcate utilization ranges for overcapacity buildings; if no buildings are overcapacity, sets all four ranges to 0
    if num_overcapacity == 0:
        pct_101_110 = 0
        pct_111_120 = 0
        pct_121_130 = 0
        pct_131_plus = 0
    else:
        pct_101_110 = round((filtered_df['Util_101_110'].sum() / num_overcapacity) * 100, 2)
        pct_111_120 = round((filtered_df['Util_111_120'].sum() / num_overcapacity) * 100, 2)
        pct_121_130 = round((filtered_df['Util_121_130'].sum() / num_overcapacity) * 100, 2)
        pct_131_plus = round((filtered_df['Util_131plus'].sum() / num_overcapacity) * 100, 2)
    
    max_bldg_util = filtered_df['Target Bldg Util'].max()   # Maximum utilization percent in district
    mean_bldg_util = round(filtered_df['Target Bldg Util'].mean(), 2)   # mean utilization percent in district
    median_bldg_util = filtered_df['Target Bldg Util'].median()     # median utilization percent in district

    overcapacity_rank = plot_df.loc[plot_df['SchoolDist'] == district_num, 'RankByOverCapacity']    # district overcapacity rank

    school_directory = create_school_directory(filtered_df)     # generates school directory dataframe

    # Stores district level data in dictionary
    district_data = {
        'total_bldgs': total_bldgs,
        'total_overcapacity': num_overcapacity,
        'pct_overcapacity': pct_overcapacity,
        'rank': overcapacity_rank,
        'num_util_101_110': filtered_df['Util_101_110'].sum(),
        'num_util_111_120': filtered_df['Util_111_120'].sum(),
        'num_util_121_130': filtered_df['Util_121_130'].sum(),
        'num_util_131_plus': filtered_df['Util_131plus'].sum(),
        'pct_util_101_110': pct_101_110,
        'pct_util_111_120': pct_111_120,
        'pct_util_121_130': pct_121_130,
        'pct_util_131_plus': pct_131_plus,
        'max_bldg_util': max_bldg_util,
        'mean_bldg_util': mean_bldg_util,
        'median_bldg_util': median_bldg_util,
        'dataframe': school_directory
    }

    return district_data


def create_school_directory(filtered_df):
    """Creates school directory dataframe to be displayed in district summary"""

    # Makes copy of filtered_df
    school_directory = filtered_df.copy() 

    # Drops unneeded columns  
    school_directory = school_directory.drop(['Bldg ID', 'SchoolDist', 'Data As Of', 'Util_101_110', 'Util_111_120', 'Util_121_130', 'Util_131plus'], axis=1)

    # Renames remaining columns for clarity
    school_directory = school_directory.rename(columns={
        'Bldg Name': 'Building Name',
        'Bldg Enroll': 'Enrollment',
        'Target Bldg Cap': 'Capacity',
        'Target Bldg Util': 'Utilization',
        'Schools In Bldg': 'Schools in Building',
        'OverCapacity': 'Over Capacity?'
    })

    # Converts Utilization column to proportions by multiplying each value by .01
    # Needed to properly display column as percentages in streamlit
    school_directory['Utilization'] = school_directory['Utilization'].apply(lambda x: x * .01)

    return school_directory

def create_district_dict(processed_df, plot_df):
    """Creates master dictionary containing data for all districts. Keys are district numbers, values are associated district data dictionaries."""

    district_dict = {}      # initialize master disctionary

    # Populates master dictionary.
    # Keys: district numbers
    # Values: district_data dictionary generated by prep_district_data function
    for district_num in plot_df['SchoolDist']:
        district_data = prep_district_data(processed_df, plot_df, district_num)
        district_dict[district_num] = district_data
    
    return district_dict

