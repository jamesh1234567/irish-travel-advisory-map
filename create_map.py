"""
Irish Travel Advisory Map Generator
Reads scraped travel advisory data and creates a color-coded world map.
"""

import pandas as pd
import plotly.express as px

def create_map():
    """
    Generate a choropleth map from the scraped travel advisory data.
    Exports as both PNG and HTML formats.
    """
    # Read the CSV file
    try:
        df = pd.read_csv('irish_travel_advisories.csv')
    except FileNotFoundError:
        print("Error: 'irish_travel_advisories.csv' not found.")
        print("Please run 'python scrape_advisories.py' first to collect the data.")
        return
    
    print(f"Loaded data for {len(df)} countries")
    
    # Convert advisory_level to integer then to string for categorical mapping
    df['advisory_level'] = df['advisory_level'].astype(int)
    df['advisory_level_cat'] = df['advisory_level'].astype(str)
    
    # Define color mapping
    color_map = {
        '1': 'green',
        '2': 'yellow',
        '3': 'orange',
        '4': 'red'
    }
    
    # Create the choropleth map
    fig = px.choropleth(
        df,
        locations='country_standardized',
        locationmode='country names',
        color='advisory_level_cat',
        hover_name='country',
        hover_data={
            'advisory_label': True,
            'advisory_level_cat': False,
            'country_standardized': False
        },
        color_discrete_map=color_map,
        category_orders={'advisory_level_cat': ['1', '2', '3', '4']},
        title='Irish Department of Foreign Affairs Travel Advisory Levels'
    )
    
    # Update layout
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        ),
        height=600,
        legend=dict(
            title="Advisory Level",
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )
    
    # Update legend labels to be more descriptive
    name_mapping = {
        '1': 'Level 1: Normal Precautions',
        '2': 'Level 2: High Degree of Caution',
        '3': 'Level 3: Avoid Unnecessary Travel',
        '4': 'Level 4: Do Not Travel',
        '1.0': 'Level 1: Normal Precautions',
        '2.0': 'Level 2: High Degree of Caution',
        '3.0': 'Level 3: Avoid Unnecessary Travel',
        '4.0': 'Level 4: Do Not Travel'
    }
    
    fig.for_each_trace(lambda t: t.update(name=name_mapping.get(t.name, t.name)))
    
    # Show the map
    fig.show()
    
    # Save as PNG (high resolution for sharing)
    try:
        fig.write_image('irish_travel_advisory_map.png', width=1920, height=1080, scale=2)
        print("Map saved as 'irish_travel_advisory_map.png' (high resolution)")
    except Exception as e:
        print(f"Could not save PNG: {e}")
        print("Note: PNG export requires 'kaleido' package: pip install kaleido")
    
    # Save as HTML (interactive version)
    fig.write_html('irish_travel_advisory_map.html')
    print("Interactive map saved as 'irish_travel_advisory_map.html'")
    print("\nYou can open the HTML file in your browser to explore the interactive map.")

if __name__ == "__main__":
    create_map()
