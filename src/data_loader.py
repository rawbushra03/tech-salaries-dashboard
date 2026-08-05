import pandas as pd
import os

def clean_data(df):
    """
    Cleans and standardizes the tech salaries dataframe.
    """
    # 1. Basic Cleaning
    df = df.drop_duplicates()
    df = df.dropna()

    # 2. Filter years (last 5 years: 2021-2025)
    df = df[df['work_year'] >= 2021]

    # 3. Standardize Regions
    # Map 2-letter country codes to Regions
    region_map = {
        'US': 'US',
        'CA': 'US', # Grouping Canada with US as North America
        'GB': 'EU', 'DE': 'EU', 'FR': 'EU', 'ES': 'EU', 'IT': 'EU', 'NL': 'EU', 'PT': 'EU', 'PL': 'EU', 'GR': 'EU', 'DK': 'EU', 'FI': 'EU', 'SE': 'EU',
        'BR': 'LATAM', 'MX': 'LATAM', 'CO': 'LATAM', 'AR': 'LATAM', 'CL': 'LATAM', 'PE': 'LATAM', 'PR': 'LATAM',
        'IN': 'ASIA', 'CN': 'ASIA', 'JP': 'ASIA', 'SG': 'ASIA', 'PK': 'ASIA', 'TH': 'ASIA', 'VN': 'ASIA',
        'AU': 'OCEANIA', 'NZ': 'OCEANIA',
        'ZA': 'AFRICA', 'NG': 'AFRICA', 'EG': 'AFRICA', 'KE': 'AFRICA'
    }
    
    # Function to get region from country code
    def get_region(country_code):
        return region_map.get(country_code, 'Other')

    df['region'] = df['company_location'].apply(get_region)
    
    # 4. Experience Level Mapping
    experience_map = {
        'EN': 'Entry-level',
        'MI': 'Mid-level',
        'SE': 'Senior-level',
        'EX': 'Executive-level'
    }
    df['experience_level_name'] = df['experience_level'].map(experience_map)

    # 5. Remote Ratio Mapping
    def get_remote_status(ratio):
        if ratio == 100: return 'Remote'
        elif ratio == 50: return 'Hybrid'
        else: return 'On-site'
    
    df['remote_status'] = df['remote_ratio'].apply(get_remote_status)
    return df

def load_and_clean_data(raw_path='data/salaries_raw.csv', cleaned_path='data/salaries_cleaned.csv'):
    """
    Loads, cleans and standardizes the tech salaries dataset from a local path.
    """
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return None

    df = pd.read_csv(raw_path)
    df = clean_data(df)

    # Save cleaned data
    df.to_csv(cleaned_path, index=False)
    print(f"Cleaned data saved to {cleaned_path}")
    return df

if __name__ == "__main__":
    load_and_clean_data()
