import pandas as pd
import geopandas as gpd
from geopandas.tools import sjoin


if __name__ == '__main__':
    amenity_filepath = "data/europe-amenity.csv.gz"
    nuts_filepath = "data/nuts_60m.gpkg"
    dst_filepath = "data/europe-nuts-amenity-counts.csv.gz"
    verbose = True
    
    gdf_nuts = gpd.read_file(
        nuts_filepath, 
        ignore_fields=[
            'levl_code', 'cntr_code', 
            'name_latn', 'nuts_name',
            'population'],
        driver='GPKG')
    gdf_nuts.sindex
    gdf_nuts.info(memory_usage='deep')
    
    
    gdf_amenity_iterator = pd.read_csv(
        amenity_filepath,
        compression='gzip',
        chunksize=1_000_000,
        usecols=['amenity', 'lon', 'lat'])
    
    df_list = []
    for i, gdf_amenity in enumerate(gdf_amenity_iterator):
        if verbose: print(f"Chunk {i}")
        
        gdf_amenity = gpd.GeoDataFrame(
            gdf_amenity,
            geometry=gpd.points_from_xy(gdf_amenity.lon, gdf_amenity.lat), 
            crs="epsg:4326").drop(columns=['lon', 'lat'])
        gdf_amenity.sindex
        gdf = sjoin(gdf_nuts, gdf_amenity, how='left')

        s_counts = gdf.groupby(['nuts_id', 'amenity'])['geometry'].count()
        s_counts.name = "counts"
        
        df_list.append(s_counts.reset_index())
        
        
    df_counts = pd.concat(df_list)
    df_counts = df_counts.groupby(['nuts_id', 'amenity'])['counts'].sum() \
                         .reset_index()
    if verbose:
        df_counts.info(memory_usage='deep')
    
    df_counts.to_csv(dst_filepath, compression='gzip', index=False)
