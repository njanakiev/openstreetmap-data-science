import os
import json
import requests
import pandas as pd
import time


def query_amenities(relation_id, query_filter='amenity'):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
        [out:json];
        area(36{0:08d})->.search_area;
        (node[{1}}](area.search_area);
          way[{1}}](area.search_area);
          rel[{1}}](area.search_area);
        );
        out center;
    """.format(relation_id, query_filter)
    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    try:
        data = response.json()
    except Exception as e:
        print(response)
        print(response.text)
        raise Exception('query_amenities failed for relation_id : {}'.format(
                    relation_id))

    counts = {}
    for element in data['elements']:
        amenity = element['tags']['amenity']
        if amenity not in counts:
            counts[amenity] = 1
        else:
            counts[amenity] += 1

    return counts

def load_city_counts(filepath)
    country_dict = {'DE': 'Germany',
                    'AT': 'Austria',
                    'CH': 'Switzerland',
                    'FR': 'France'}
    elements = []
    df = pd.read_csv(filepath)
    for i, country_code, city, city_id, rel_id, lat, lon, population, wikidata in df.itertuples():
        print(i, country_code, city, city_id, rel_id, lat, lon, population, wikidata)

        time.sleep(2)
        try_count, max_try_count = 0, 4
        while try_count < max_try_count:
            try:
                amenities = query_amenities(rel_id)
                break
            except Exception as e:
                time.sleep((try_count + 1) * 10)
                print('Failed loading query, try count : {}'.format(try_count))
                try_count += 1

        if try_count == max_try_count:
            print('Failed loading query')
            exit()

        element = {}
        element['city'] = city
        element['city_id'] = city_id
        element['rel_id'] = rel_id
        element['country_code'] = country_code
        element['country'] = country_dict[country_code]
        element['population'] = population
        element['wikidata'] = wikidata
        element['lat'] = lat
        element['lon'] = lon
        element['amenities'] = amenities
        elements.append(element)

    # Store intermediate results
    #with open('data/city_amenities.json', 'w') as f:
    #    json.dump(elements, f, indent=4)

    df_values = pd.read_csv('data/taginfo/taginfo_amenity_values.csv')
    columns = ['country_code', 'country', 'city', 'city_id', 'rel_id', \
               'population', 'wikidata', 'lat' ,'lon']
    columns += list(df_values['value'][:50])

    # Load intermediate results
    #with open('data/city_amenities.json', 'r') as f:
    #    elements = json.load(f)

    rows = []
    for element in elements:
        city = element['city']
        city_id = element['city_id']
        rel_id = element['rel_id']
        country_code = element['country_code']
        country = element['country']
        population = element['population']
        wikidata = element['wikidata']
        lat, lon = element['lat'],element['lon']
        amenities = element['amenities']
        row = [country_code, country, city, city_id, rel_id, population, wikidata, lat, lon]
        row += [amenities[value] if value in amenities else 0
                for value in df_values['value'][:50]]

        print(row)
        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)
    return df


df = load_city_counts('data/city_relations.csv')
df.to_csv('data/city_amenities_counts.csv', index=False)
