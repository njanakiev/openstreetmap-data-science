"""
Script to create GeoJSON from collected json files of the bounding box of each collected city in the 'data/city_relations' folder
"""
import os
import json


folder = 'data/city_relations'
filepaths = [os.path.join(folder, f) for f in os.listdir(folder)
             if f.endswith('.json')]

features = []
for filepath in filepaths:
    print(filepath)
    with open(filepath, 'r') as f:
        data = json.load(f)

        bb = [data['bounds']['minlon'],
              data['bounds']['minlat'],
              data['bounds']['maxlon'],
              data['bounds']['maxlat']]

        co = [[bb[0], bb[1]],
              [bb[2], bb[1]],
              [bb[2], bb[3]],
              [bb[0], bb[3]],
              [bb[0], bb[1]]]

        print(co)

        feature = {}
        feature['type'] = 'Feature'
        feature['geometry'] = {}
        feature['geometry']['type'] = 'Polygon'
        feature['geometry']['coordinates'] = [co]
        features.append(feature)


geojson = {}
geojson['type'] = 'FeatureCollection'
geojson['features'] = features
geojson['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }

with open('data/city_rectangles.json', 'w') as f:
    json.dump(geojson, f, indent=4)
