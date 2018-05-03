import os
import json
import requests
import pandas as pd
import traceback
import time
from math import sqrt


def query_city_relation(city_name, country_code, admin_level, lat, lon):
    """Query Overpass API for the relation of a city"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
        [out:json];
        area["ISO3166-1"="{0}"][admin_level=2];
        (rel["name"="{1}"][boundary="administrative"][admin_level={2}](area);
        );
        out bb;
    """.format(country_code, city_name, admin_level)

    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    try:
        data = response.json()
    except Exception as e:
        print(response.text)
        traceback.print_exc()
        print(country_code, value)
        return None

    if len(data['elements']) == 0:
        raise Exception('No elements returned : {}'.format(
            len(data['elements'])))

    # Take closest relation to the given city
    elif len(data['elements']) > 1:
        element = data['elements'][0]
        bounds = element['bounds']
        rel_lat = (bounds['minlat'] + bounds['maxlat']) / 2
        rel_lon = (bounds['minlon'] + bounds['maxlon']) / 2
        dist_2 = (rel_lat - lat)**2 + (rel_lon - lon)**2

        for tmp_element in data['elements']:
            bounds = tmp_element['bounds']
            rel_lat = (bounds['minlat'] + bounds['maxlat']) / 2
            rel_lon = (bounds['minlon'] + bounds['maxlon']) / 2

            tmp_dist_2 = (rel_lat - lat)**2 + (rel_lon - lon)**2
            if dist_2 > tmp_dist_2:
                dist_2 = tmp_dist_2
                element = tmp_element
    else:
        element = data['elements'][0]

    entry = {}
    entry['bounds'] = element['bounds']
    entry['id'] = element['id']
    entry['tags'] = element['tags']
    return entry


def query_city_nodes(country_code):
    """Load saved city nodes into a DataFrame"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    area["ISO3166-1"="{}"][admin_level=2]->.search;

    (node[place="city"](area.search);
     node[place="town"](area.search);
     //node[place="village"](area.search);
    );
    out center;""".format(country_code)
    response = requests.get(overpass_url, params={'data': overpass_query})

    try:
        data = response.json()
    except Exception as e:
        print(response)
        print(response.text)
        raise Exception('Failed to load query')

    rows = [(element['tags']['name'],
             element['tags']['place'],
             element['tags']['population']
                if 'population' in element['tags'] else None,
             element['tags']['wikidata']
                if 'wikidata' in element['tags'] else None,
             # Geojson saves coordinates in lon, lat order
             element['lat'], element['lon'])
             for element in data['elements']
                if 'name' in element['tags']]

    df = pd.DataFrame(rows, columns=['name', 'place', 'population', 'wikidata', 'lat', 'lon'])
    df['place'] = df['place'].astype('category')
    df['population'] = pd.to_numeric(df['population'])
    df['lat'] = pd.to_numeric(df['lat'])
    df['lon'] = pd.to_numeric(df['lon'])
    df.set_index('name', inplace=True)
    return df


def save_city_relations(filepath, country_code, admin_level):
    df = pd.read_csv(filepath, index_col='name')
    df = df[df['place'] == 'city'].sort_values(by='population',
                                               ascending=False)

    #rerun_cities = ['Saint-Denis', 'Montreuil']
    for i, city in enumerate(df.index):
        print('{:3d}/{} : {}'.format(i + 1, len(df.index), city))
        #if city not in rerun_cities: continue
        lat, lon = df[['lat', 'lon']].iloc[i]

        time.sleep(2)
        try_count = 0
        skip = False
        while try_count < 4:
            try:
                if city == 'Klagenfurt':
                    entry = query_city_relation('Klagenfurt am Wörthersee', country_code, admin_level, lat, lon)
                elif city in ['Wien', 'Berlin', 'Hamburg']:
                    entry = query_city_relation(city,
                        country_code, 4, lat, lon)
                elif city in ['Paris']:
                    entry = query_city_relation(city,
                        country_code, 6, lat, lon)
                elif city in ['Hannover', 'Aachen', 'Saarbrücken', 'Neuss', 'Paderborn', 'Göttingen', 'Recklinghausen', 'Reutlingen', 'Bergisch Gladbach', 'Moers', 'SIegen', 'Hildesheim']:
                    entry = query_city_relation(city,
                        country_code, 8, lat, lon)
                elif city in ['Fare', 'Vaitape', 'Le Port', 'Vai’ea']:
                    skip = True
                    break
                else:
                    entry = query_city_relation(city,
                        country_code, admin_level, lat, lon)
                break
            except:
                try_count += 1
                traceback.print_exc()
                print('Failed loading query, try count : {}'.format(try_count))
                time.sleep((try_count + 1) * 10)
                continue
        if not skip:
            entry['population'] = df['population'].iloc[i]
            entry['lat'] = df['lat'].iloc[i]
            entry['lon'] = df['lon'].iloc[i]
            relation_filepath = 'data/city_relations/{}_{:04d}_{}.json'.format(
                country_code, i, city)
            with open(relation_filepath, 'w') as f:
                json.dump(entry, f, indent=4)


def collect_city_relations_to_dataframe(folder):
    """Collect city relation JSON files to single DataFrame"""
    filepaths = [os.path.join(folder, f) for f in sorted(os.listdir(folder))
                 if f.endswith('.json')]

    print(filepaths)

    rows = []
    for filepath in filepaths:
        country_code, idx, city = os.path.basename(
                                    filepath).split('.')[0].split('_')
        print(country_code, idx, city)
        with open(filepath, 'r') as f:
            data = json.load(f)

        row = (country_code,
               city, int(idx), int(data['id']),
               data['lat'], data['lon'],
               data['population']
                   if 'population' in data else None,
               data['tags']['wikidata']
                   if 'wikidata' in data['tags'] else None)
        rows.append(row)

    df = pd.DataFrame(rows, columns=['country_code', 'city', 'city_id',
        'rel_id', 'lat', 'lon', 'population', 'wikidata'])



country_code, admin_level = 'DE', 6
#country_code, admin_level = 'AT', 6
#country_code, admin_level = 'CH', 8
#country_code, admin_level = 'FR', 8

# Query all city and town nodes for a given country
#df = query_city_nodes(country_code)
#df.to_csv('data/city_nodes_{}.csv'.format(country_code))
#print(df.head())

# Save all relations
#save_city_relations('data/city_nodes_{}.csv'.format(country_code), country_code, admin_level)

# Collect all intermediate JSON files into single CSV file
df = collect_city_relations_to_dataframe('data/city_relations')
df.to_csv('data/city_relations.csv', index=False)
