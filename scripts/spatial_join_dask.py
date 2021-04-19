import numpy as np
import pandas as pd
import pygeos
import geopandas as gpd
from geopandas.tools import sjoin

import dask_geopandas
import dask.dataframe as dd
from dask.distributed import Client


def spatial_join_map_partition(points_filepath, nuts_filepath, blocksize=1_000_000):
    def spatial_join(gdf_regions):
        def compute_spatial_join(df):
            df = gpd.GeoDataFrame(df, 
                geometry=gpd.points_from_xy(df.lon, df.lat), 
                crs="epsg:4326")

            df = sjoin(df, gdf_regions, how='left')
            return df[['nuts_id', 'amenity', 'osm_id']]
        return compute_spatial_join
    
    gdf_nuts = gpd.read_file(
        nuts_filepath, 
        ignore_fields=[
            'levl_code', 'cntr_code', 
            'name_latn', 'nuts_name',
            'population'],
        driver='GPKG')
    
    ddf_amenity = dd.read_csv(
        points_filepath,
        blocksize=blocksize)
    print(ddf_amenity.npartitions)
    
    ddf_amenity = ddf_amenity.map_partitions(
        spatial_join(gdf_nuts.copy()),
        meta={
            'nuts_id': object,
            'amenity': object,
            'osm_id':  object
        })
    
    s = ddf_amenity.groupby(['nuts_id', 'amenity'])['osm_id'] \
                   .count() \
                   .compute()
    s.name = 'counts'
    df = s.reset_index()

    return df
    

if __name__ == '__main__':
    client = Client(memory_limit='4GB', 
                    processes=True,
                    threads_per_worker=4,
                    n_workers=2)
    print("Dashboard Link", client.dashboard_link)
    
    amenity_filepath = "data/europe-amenity.csv"
    nuts_filepath = "data/nuts_60m.gpkg"
    dst_filepath = "data/europe-amenity-counts-3.csv.gz"
    
    df = spatial_join_map_partition(amenity_filepath, nuts_filepath)
    df.to_csv(dst_filepath, index=False)
