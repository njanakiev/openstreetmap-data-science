import argparse
import functools
import multiprocessing
import pandas as pd
import geopandas as gpd
from geopandas.tools import sjoin
from tqdm.auto import tqdm


def spatial_join(gdf_amenity, gdf_geometry, index_col):
    gdf_amenity = gpd.GeoDataFrame(
        gdf_amenity,
        geometry=gpd.points_from_xy(
            gdf_amenity.lon, gdf_amenity.lat), 
        crs="epsg:4326").drop(columns=['lon', 'lat'])
    
    gdf_amenity.sindex
    gdf = sjoin(gdf_geometry, gdf_amenity, how='left')

    s_counts = gdf.groupby(
        [index_col, 'amenity'])['geometry'].count()
    s_counts.name = "counts"
    
    return s_counts.reset_index()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Spatial join")
    parser.add_argument(
        help="Input csv.gz or csv filepath",
        action='store', dest='src_filepath')
    parser.add_argument(
        help="geomtry filepath",
        dest='geometry_filepath')
    parser.add_argument(
        help="Output filepath csv.gz or txt.gz",
        action='store', dest='dst_filepath')
    parser.add_argument(
        "-i", "--index-col",
        help="geometry index column",
        dest="index_col", default="id")
    parser.add_argument(
        "-v", "--verbose",
        help="Verbose output",
        action="store_true", dest="verbose")
    parser.add_argument(
        "-m", "--multiprocessing",
        help="Multiprocessing",
        action="store_true", dest="multiprocessing")
    args = parser.parse_args()
    
    gdf_geometry = gpd.read_file(
        args.geometry_filepath,
        driver='GPKG')
    gdf_geometry = gdf_geometry[[args.index_col, 'geometry']]
    gdf_geometry.sindex
    if args.verbose:
        gdf_geometry.info(memory_usage='deep')
    
    gdf_iterator = pd.read_csv(
        args.src_filepath,
        compression='gzip',
        chunksize=1_000_000,
        usecols=['amenity', 'lon', 'lat'])
    
    df_list = []
    if args.multiprocessing:
        with multiprocessing.Pool() as pool:
            df_list = pool.map(
                functools.partial(
                    spatial_join,
                    gdf_geometry=gdf_geometry,
                    index_col=args.index_col),
                gdf_iterator)
    else:
        for i, gdf_amenity in enumerate(tqdm(gdf_iterator)):
            df_list.append(
                spatial_join(gdf_amenity, gdf_geometry, args.index_col))
        
        
    df_counts = pd.concat(df_list)
    df_counts = df_counts \
        .groupby([args.index_col, 'amenity'])['counts'].sum() \
        .reset_index()
    if args.verbose:
        df_counts.info(memory_usage='deep')
    
    df_counts.to_csv(args.dst_filepath, compression='gzip', index=False)
