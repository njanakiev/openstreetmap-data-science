import io
import requests
import argparse
import numpy as np
import pandas as pd
import shapely.geometry
import geopandas as gpd
import matplotlib.pyplot as plt

from zipfile import ZipFile
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing"
NUTS_BASE_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/download/"


def download_population_data(verbose=False):
    url = EUROSTAT_BASE_URL + "?file=data/demo_r_pjangrp3.tsv.gz"
    if verbose:
        print(f"Downloading {url}")
    
    df = pd.read_csv(url, delimiter='\t', low_memory=False)
    df = df.rename(columns={df.columns[0]: 'nuts_id'})
    df = df[df['nuts_id'].str.startswith('T,NR,TOTAL')]
    df['nuts_id'] = df['nuts_id'].str.split(',').str[-1]
    df = df.set_index('nuts_id')

    df.columns = [c.strip() for c in df.columns]
    df = df.applymap(lambda item: 
            float(item.split()[0]) if ':' not in item else None)
    df = df.fillna(method='backfill', axis=1)

    return df


def download_gdp_data(unit="EUR_HAB", verbose=False):
    url = EUROSTAT_BASE_URL + "?file=data/nama_10r_3gdp.tsv.gz"
    if verbose:
        print(f"Downloading {url}")
        
    df = pd.read_csv(url, delimiter='\t', low_memory=False)

    first_column = df.columns[0]
    index = first_column.split(",")
    df_units = df[first_column].apply(
        lambda s: pd.Series(s.split(","), index=index))

    df = df.join(df_units);
    df.columns = df.columns.str.strip()
    df = df[df['unit'] == unit]
    df = df.rename(columns={index[1]: 'nuts_id'})

    df = df.drop(columns=[first_column, index[0]])
    df = df.set_index('nuts_id')
    df = df.applymap(
        lambda v: np.nan if v.strip() == ':' else float(v.split()[0]))
    
    return df


def download_nuts_regions(resolution="60m", verbose=False):
    if resolution not in ["01m", "03m", "10m", "20m", "60m"]:
        raise ValueError("resolution not available")

    gdf_list = []
    for year in [2013, 2016]:
        url = NUTS_BASE_URL + f"ref-nuts-{year}-{resolution}.geojson.zip"
        if verbose: 
            print(f"Downloading {url}")
        
        r = requests.get(url, verify=True)
        r.raise_for_status()
        with ZipFile(io.BytesIO(r.content)) as z:
            for nuts_level in range(4):
                filename = f"NUTS_RG_{resolution.upper()}_{year}_4326_LEVL_{nuts_level}.geojson"
                if verbose:
                    print(f"\tExtracting {filename}")
                
                with z.open(filename) as f:
                    gdf = gpd.read_file(f, driver='GeoJSON')
                    gdf['year'] = year
                    gdf_list.append(gdf)

    gdf = gpd.GeoDataFrame(
        pd.concat(gdf_list, ignore_index=False), 
        crs=gdf_list[0].crs)
    gdf = gdf.drop_duplicates(subset=['NUTS_ID'], keep='first')
    gdf.columns = gdf.columns.str.lower()
    gdf = gdf.drop(
        columns=['mount_type', 'urbn_type', 'coast_type', 'id', 'fid'])
    gdf = gdf.set_index('nuts_id')
    
    return gdf


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download and prepare Eurostat NUTS regions with population data")
    parser.add_argument(
        'filepath', type=str, help='destination filepath')
    parser.add_argument(
        '-r', '--resolution', type=str, action='store', default='60m',
        help='set NUTS region resolution (01m, 03m, 10m, 20m, 60m)')
    parser.add_argument(
        '-v', '--verbose', action='store_true', 
        help='verbose output')
    args = parser.parse_args()
    
    if not any(args.filepath.endswith(ext) for ext in [".json", '.geojson', '.gpkg']):
        print("File extension not supported")
        exit(-1)
    
    if args.resolution not in ["01m", "03m", "10m", "20m", "60m"]:
        print("File extension not supported")
        exit(-1)
    
    # Download data
    df_pop = download_population_data(verbose=args.verbose)
    df_gdp = download_gdp_data(verbose=args.verbose)
    gdf = download_nuts_regions(args.resolution, verbose=args.verbose)
    
    # Merge data
    s_pop = df_pop['2018'].dropna()
    s_pop.name = 'population'
    s_gdp = df_gdp['2018'].dropna()
    s_gdp.name = 'gdp'
    gdf = gdf.join(s_pop).join(s_gdp)
    
    # Convert Polygons to Multipolygons
    gdf.geometry = gdf.geometry.apply(
        lambda geom: MultiPolygon([geom]) if isinstance(geom, Polygon) else geom)
    
    if args.verbose:
        gdf.info(memory_usage='deep')
    
    # Save data
    if args.filepath.endswith(".gpkg"):
        gdf.to_file(args.filepath, driver="GPKG")
    elif args.filepath.endswith(".geojson") or args.filepath.endswith(".json"):
        gdf.to_file(args.filepath, driver="GeoJSON")
