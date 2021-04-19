import wbdata
import pandas as pd
import numpy as np


def load_world_bank(year=2019):
    """Load data from World Bank"""
    indicators = {'SP.POP.TOTL':'Population',
                  'NY.GDP.PCAP.PP.CD':'GDP', # GDP per capita
                  'NY.GNP.PCAP.PP.KD':'GNI'} # GNI per capita

    df = wbdata.get_dataframe(indicators)
    df = df.reset_index()

    # Rename Slovak Republic with Slovakia
    df['country'] = df['country'].replace(
        {'Slovak Republic': 'Slovakia'})
    
    df = df.rename(columns={
        'Population': 'population',
        'GDP': 'gdp',
        'GNI': 'gni'
    })

    # Convert date to integer
    df['date'] = df['date'].astype(int)

    # Set MultiIndex
    df = df.set_index(['country', 'date'])

    df = df.reset_index()
    df = df[df['date'] == year] \
        .drop(columns='date') \
        .set_index('country')

    return df


def load_big_mac_index(filepath, year=2019):
    """Load Big Mac Index"""
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df[df['date'].dt.year == year]
    df = df.rename(columns={ 'name': 'country' })
    df = df[['country', 'dollar_price']]
    df = df.set_index('country')
    
    return df


def load_hdi(filepath, year=2019):
    """Load HDI Data"""
    df = pd.read_csv(filepath, skiprows=5, encoding="latin 1")
    df = df.rename(columns={ 
        'Country': 'country', 
        'HDI Rank': 'hdi_rank', 
        '2019': 'hdi' 
    })
    df['country'] = df['country'].str.strip()
    df = df[['country', 'hdi', 'hdi_rank']]
    df = df.set_index('country')
    
    return df


if __name__ == '__main__':
    verbose = True
    year = 2018
    
    # Load eu codes for European countries
    df_eu_codes = pd.read_csv(
        'country_codes.csv', index_col='country')

    df_wb = load_world_bank(year=year)
    df_wb.to_csv(f'data/world_bank_{year}.csv')
    
    # Load data from CSV files
    if verbose: print("World Bank")
    df_wb = pd.read_csv(
        f'data/world_bank_{year}.csv',
        index_col='country')
    if verbose: print("Big Mac Index")
    df_bm = load_big_mac_index(
        'data/big-mac-full-index.csv', 
        year=year)
    if verbose: print("HDI")
    df_hdi = load_hdi(
        "data/Human Development Index (HDI).csv", 
        year=year)

    # Merge economic measurements
    df_targets = df_eu_codes.join(df_wb, how='left')
    df_targets = df_targets.join(df_bm, how='left')
    df_targets = df_targets.join(df_hdi, how='left')
    df_targets.to_csv('data/economic_indicators.csv')
    
    if verbose: print(df_targets.head())
