"""
Irish Travel Advisory Scraper
Collects travel advisory data from the Irish Department of Foreign Affairs website.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep

# Headers to mimic a real browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def get_country_urls():
    """
    Scrape the main DFA travel advice page to get all country URLs.
    Returns a DataFrame with country names and their advisory page URLs.
    """
    base_url = "https://www.ireland.ie/en/dfa/overseas-travel/advice/"
    
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        country_links = []
        
        # Find all links that match the pattern for country advisory pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match pattern: /dfa/overseas-travel/advice/[country-name]/
            if '/advice/' in href and href.count('/') >= 5:
                # Filter out non-country pages
                if not any(x in href.lower() for x in ['covid', 'index', 'search', 'about']):
                    full_url = href if href.startswith('http') else f"https://www.ireland.ie{href}"
                    country_slug = href.rstrip('/').split('/')[-1]
                    country_name = country_slug.replace('-', ' ').title()
                    
                    country_links.append({
                        'country': country_name,
                        'url': full_url
                    })
        
        df = pd.DataFrame(country_links).drop_duplicates()
        return df
    
    except Exception as e:
        print(f"Error fetching country list: {e}")
        print("\nThe website may be blocking automated requests.")
        print("Alternative method: Use your browser's developer console")
        print("\n1. Go to: https://www.ireland.ie/en/dfa/overseas-travel/advice/")
        print("2. Open console (F12) and paste this JavaScript:\n")
        print("""
countries = [];
document.querySelectorAll('a[href*="/advice/"]').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href.split('/').length >= 5) {
        const country = href.split('/').filter(x=>x).pop();
        if (!['covid','index','search','about'].includes(country)) {
            countries.push({
                country: country.replace(/-/g, ' '),
                url: 'https://www.ireland.ie' + href
            });
        }
    }
});
console.log(JSON.stringify(countries, null, 2));
        """)
        print("\n3. Copy the output and save it as 'countries.json'")
        print("4. Then modify this script to load from that file instead")
        return None

def get_advisory_level(url):
    """
    Extract the advisory level from a country's page.
    Returns an integer 1-4 representing the advisory level, or None if unable to determine.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the specific advisory accordion element
        # The DFA website uses: <div class="accordion_travel [level] accordion is-open">
        advisory_div = soup.find('div', class_='accordion_travel')
        
        if advisory_div:
            classes = advisory_div.get('class', [])
            classes_str = ' '.join(classes).lower()
            
            # Check the class name for the advisory level
            if 'do-not-travel' in classes_str:
                return 4
            elif 'avoid-non-essential-travel' in classes_str or 'avoid-unnecessary-travel' in classes_str:
                return 3
            elif 'high-degree-of-caution' in classes_str or 'high-degree-caution' in classes_str:
                return 2
            elif 'normal-precautions' in classes_str:
                return 1
        
        # Fallback: Look for the h3 title within the accordion
        accordion_title = soup.find('h3', class_='accordion__title')
        if accordion_title:
            title_text = accordion_title.get_text().strip().lower()
            
            if 'do not travel' in title_text:
                return 4
            elif 'avoid non-essential travel' in title_text or 'avoid unnecessary travel' in title_text:
                return 3
            elif 'high degree of caution' in title_text:
                return 2
            elif 'normal precautions' in title_text:
                return 1
        
        return None
            
    except Exception as e:
        print(f"  Error: {e}")
        return None

def standardize_country_name(country):
    """
    Map DFA country names to ISO standard names used by mapping libraries.
    Add more mappings as needed if countries don't appear on the map.
    """
    mapping = {
        'Usa': 'United States',
        'United States Of America': 'United States',
        'Uk': 'United Kingdom',
        'Uae': 'United Arab Emirates',
        'Democratic Republic Of The Congo': 'Democratic Republic of the Congo',
        'Drc': 'Democratic Republic of the Congo',
        'Congo': 'Republic of the Congo',
        'North Korea': 'North Korea',
        'Dpr Korea': 'North Korea',
        'South Korea': 'South Korea',
        'Republic Of Korea': 'South Korea',
        'Czech Republic': 'Czechia',
        "Cote D'ivoire": "Côte d'Ivoire",
        'Ivory Coast': "Côte d'Ivoire",
        'Burma': 'Myanmar',
        'Cape Verde': 'Cabo Verde',
        'East Timor': 'Timor-Leste',
        'Laos': 'Lao PDR',
        'Macedonia': 'North Macedonia',
        'Swaziland': 'Eswatini',
        'The Bahamas': 'Bahamas',
        'The Gambia': 'Gambia',
    }
    return mapping.get(country, country)

def main():
    """Main execution function"""
    print("=" * 60)
    print("Irish Travel Advisory Scraper")
    print("=" * 60)
    
    # Get list of countries
    print("\nFetching country list from DFA website...")
    countries_df = get_country_urls()
    
    if countries_df is None or len(countries_df) == 0:
        print("\nUnable to automatically scrape country list.")
        print("Please use the manual method described above.")
        return
    
    print(f"Found {len(countries_df)} countries\n")
    
    # Scrape advisory levels for each country
    print("Scraping advisory levels (this will take a few minutes)...")
    print("-" * 60)
    
    advisory_levels = []
    for idx, row in countries_df.iterrows():
        print(f"{idx+1}/{len(countries_df)}: {row['country']}...", end=' ')
        level = get_advisory_level(row['url'])
        if level:
            print(f"Level {level}")
        else:
            print("Unable to determine")
        advisory_levels.append(level)
        sleep(1)  # Be polite to the server
    
    # Add data to dataframe
    countries_df['advisory_level'] = advisory_levels
    countries_df['country_standardized'] = countries_df['country'].apply(standardize_country_name)
    
    # Filter out countries where we couldn't determine the level
    countries_with_data = countries_df[countries_df['advisory_level'].notna()].copy()
    
    # Add readable labels
    level_labels = {
        1: 'Normal Precautions',
        2: 'High Degree of Caution',
        3: 'Avoid Unnecessary Travel',
        4: 'Do Not Travel'
    }
    countries_with_data['advisory_label'] = countries_with_data['advisory_level'].map(level_labels)
    
    # Save to CSV
    countries_with_data.to_csv('irish_travel_advisories.csv', index=False)
    
    print("\n" + "=" * 60)
    print(f"Successfully scraped {len(countries_with_data)} countries")
    print("=" * 60)
    print("\nAdvisory level distribution:")
    print(countries_with_data['advisory_level'].value_counts().sort_index())
    print("\nData saved to 'irish_travel_advisories.csv'")
    print("Run 'python create_map.py' to generate the map visualization.")

if __name__ == "__main__":
    main()
