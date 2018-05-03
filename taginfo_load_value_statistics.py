import os
import json
import requests
import pandas as pd


def load_values(key, pages=1, results_per_page=100):
    """Load statistics for most common values for a given key in
    OpenStreetMap via the taginfo API"""
    taginfo_url = "https://taginfo.openstreetmap.org/api/4/"
    data = []
    for i in range(pages):
        params = {
            'key':key,
            'page':i,
            'rp':results_per_page,
            'sortname':'count',
            'sortorder':'desc'
        }
        r = requests.get(taginfo_url + 'key/values', params=params)
        data += r.json()['data']

    df = pd.DataFrame(data=data)
    return df.drop_duplicates()


key = 'amenity'

df = load_values(key, 4, 500)
print(df.head())
print(df.info())

df.to_csv('data/taginfo_{}_values.txt'.format(key), index=False)
