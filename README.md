# NYC School Capacity Dashboard
A Streamlit app visualizing New York City public school building utilization and overcrowding trends. [Live app ->](https://nycschoolcapacitydashboard.streamlit.app/)

## Background
Building utilization is defined as the ratio of a school building's enrollment to its designated capacity - for example, a utilization rate of 120% would mean that a building enrolls 20% more students than its intended capacity. While this data is publicly available through NYC Open Data, it can be difficult for stakeholders (students, families, educators, and policymakers) to interpret. This dashboard aims to make this information accessible and visually intuitive.

## Features
- Dynamic visualizations of building utilization rates by district
- Citywide and district-level summary statistics and overcapacity bands
- Detailed building-level data table for all 32 NYC school districts

## Tech Stack
<b>Pandas & Geopandas</b> for data cleaning and analysis<br>
<b>Plotly</b> for visualizations<br>
<b>Streamlit</b> for page layout and design<br>
<b>Streamlit Cloud</b> for deployment

## Instructions for Running Locally
1. Clone repo
```bash
git clone https://github.com/dolsen23/nyc_school_capacity_dashboard
```

2. Install dependencies
```bash
cd nyc-school-capacity
pip install -r requirements.txt
```

3. Run on local server
```bash
streamlit run app.py
```

## Data Source
Data is sourced from NYC Open Data's [Enrollment Capacity and Building Utilization Reports](https://data.cityofnewyork.us/Education/Enrollment-Capacity-And-Utilization-Reports/gkd7-3vk7/about_data) dataset.

## Contact
For questions, feedback, or suggestions, please open an issue on this repository.

---
**Author**: David Olsen

