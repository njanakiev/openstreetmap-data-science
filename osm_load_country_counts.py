import os
import time
import requests
import pandas as pd
import traceback


def query_key_value_counts(country_code, key, value):
    """Query counts of key-value pair elements in specific county with Overpass API"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    #overpass_url = "http://overpass.openstreetmap.fr/api/interpreter"
    #overpass_url = "https://z.overpass-api.de/api/interpreter"
    overpass_query = """
        [out:json];
        area["ISO3166-1"="{0}"][admin_level=2]->.search_area;
        (node["{1}"="{2}"](area.search_area);
          way["{1}"="{2}"](area.search_area);
          rel["{1}"="{2}"](area.search_area);
        );
        out count;
    """.format(country_code, key, value)
    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    try:
        data = response.json()
        counts = data['elements'][0]['tags']
        counts['country_code'] = country_code
        counts['value'] = value
    except Exception as e:
        print(response)
        print(response.text)
        #traceback.print_exc()
        print(country_code, value)
        raise Exception('query_key_value_counts failed for : {}, {}, {}'.format(country_code, key, value))

    return counts

def load_country_counts(key='amenity'):
    df_values = pd.read_csv('data/taginfo/taginfo_{}_values.csv'.format(key))
    df_counrty_codes = pd.read_csv('data/country_codes.csv').set_index('Country')
    columns = ['country_code', 'value', 'total',
               'areas', 'nodes', 'ways', 'relations']

    #for country, country_code in df_counrty_codes.itertuples():
    for country, country_code in df_counrty_codes.loc['France':].itertuples():
    #for country, country_code in [('Austria', 'AT')]:
        counts = []
        print()
        print(country, country_code)
        for value in df_values['value'][:50]:
            print(value)
            try_count, max_try_count = 0, 10
            while try_count < max_try_count:
                try:
                    count = query_key_value_counts(country_code, key, value)
                    break
                except Exception as e:
                    #traceback.print_exc()
                    try_count += 1
                    print('Failed loading query : {}, try count : {}'.format(e, try_count))
                    time.sleep(try_count * 20)

            if try_count == max_try_count:
                print('Failed loading query')
                exit()

            print(count)
            counts.append(count)
            time.sleep(10)

        df_counts = pd.DataFrame(data=counts, columns=columns)
        df_counts.to_csv('data/counts/{0}_counts/{1}_{0}_counts.csv'.format(
            key, country_code), index=False)

def collect_results(folder='data/country_amenity_counts'):
    filepaths = [os.path.join(folder, f) for f in os.listdir(folder)
                 if f.endswith('.csv')]

    frames = []
    for filepath in sorted(filepaths):
        print(filepath)
        df = pd.read_csv(filepath)
        country_code = df['country_code'][0]
        df = df[['value', 'total']].T
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        df.index = pd.Series([country_code], name='country_code')
        df.reset_index(inplace=True)
        frames.append(df)

    df = pd.concat(frames, axis=0)
    df.set_index('country_code', inplace=True)

    df_country_codes = pd.read_csv('data/country_codes.csv')
    df_country_codes.rename(columns={'Country Code':'country_code', 'Country':'country'}, inplace=True)
    df_country_codes.set_index('country_code', inplace=True)
    df = df_country_codes.join(df)

    df.reset_index(inplace=True)
    df.to_csv('data/country_amenity_counts.csv', index=False)

    print(df.head())

#load_country_counts()
collect_results()
