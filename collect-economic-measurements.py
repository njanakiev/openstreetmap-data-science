import wbdata
import pandas as pd
import numpy as np


def load_world_bank(countries, year=2016):
    """Load data from World Bank"""
    indicators = {'SP.POP.TOTL':'Population',
                  'NY.GDP.PCAP.PP.CD':'GDP', # GDP per capita
                  'NY.GNP.PCAP.PP.KD':'GNI'} # GNI per capita

    df = wbdata.get_dataframe(indicators, country=countries)
    df.reset_index(inplace=True)

    # Rename Slovak Republic with Slovakia
    df['country'] = df['country'].replace({'Slovak Republic': 'Slovakia'})

    # Convert date to integer
    df['date'] = df['date'].astype(int)

    # Set MultiIndex
    df.set_index(['country', 'date'], inplace=True)

    df_wb = df.reset_index()
    df_wb = df_wb[df_wb['date'] == year].drop(columns='date').set_index('country')
    df_wb.sort_index(inplace=True)

    return df_wb


def load_big_mac_index(filepath='data/BMFile2000toJan2018.xls', sheet='Jan2018'):
    """Load Big Mac Index"""
    df_bm = pd.read_excel(filepath, sheet=sheet)
    df_bm.rename(columns={'Country':'country'}, inplace=True)
    df_bm.set_index('country', inplace=True)
    df_bm = df_bm[['dollar_price', 'dollar_ppp']]
    df_bm.rename(columns={'dollar_price': 'BM Dollar',
                          'dollar_ppp': 'BM Dollar PPP'}, inplace=True)
    return df_bm


def load_hdi(filepath='data/HDI_human_development_reports.xls'):
    """Load HDI Data"""
    df_hdi = pd.read_excel(filepath)
    df_hdi = df_hdi.iloc[5:196]
    df_hdi = df_hdi.drop(columns=[df_hdi.columns[i] for i in [2, 4, 6, 8, 10, 12]])
    df_hdi.dropna(inplace=True)
    df_hdi.columns = ['country',
                  'HDI',
                  'Life Expectancy at Birth',
                  'Expected Years of Schooling',
                  'Mean Years of Schooling',
                  'GNI per Capita',
                  'GNI per Capita minus HDI Rank',
                  'HDI Rank 2014']
    df_hdi['HDI Rank'] = df_hdi.index
    df_hdi.set_index('country', inplace=True)
    df_hdi = df_hdi.astype({'HDI':float,
                    'Life Expectancy at Birth':float,
                    'Expected Years of Schooling':float,
                    'Mean Years of Schooling':float,
                    'GNI per Capita':float,
                    'GNI per Capita minus HDI Rank':int,
                    'HDI Rank 2014':int,
                    'HDI Rank':int})
    return df_hdi


# Load eu codes for European countries
df_eu_codes = pd.read_csv('data/country_codes.csv')
countries = tuple(df_eu_codes['country_code'])

df_wb = load_world_bank(countries)
#df_wb.to_csv('data/world_bank_eu.csv')
# Load data from CSV instead
#df_wb = pd.read_csv('data/world_bank_eu.csv')
#df_wb.set_index(['country', 'date'], inplace=True)

df_bm = load_big_mac_index()

df_hdi = load_hdi()

df_hdi.to_csv('data/human_development_reports.csv')
#df_hdi = pd.read_csv('data/human_development_reports.csv', index_col='country')
df_hdi.drop(columns=['GNI per Capita', 'GNI per Capita minus HDI Rank', 'HDI Rank 2014'], inplace=True)

# Merge economic measurements
df_targets = df_eu_codes.set_index('country').join(df_wb)
df_targets = df_targets.join(df_bm, how='left')
df_targets = df_targets.join(df_hdi, how='left')
df_targets.to_csv('data/economic_measurements.csv')
print(df_targets.head())
