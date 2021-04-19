import pandas as pd
import geopandas as gpd


if __name__ == '__main__':
    amenity_filepath = "data/europe-amenity-counts.csv.gz"
    nuts_filepath = "data/nuts_60m.gpkg"
    src_stats_filepath = "data/taginfo_amenity_counts.csv"
    dst_filepath = "data/europe-amenity-features.csv.gz"
    verbose = True

    # Load taginfo statistics
    df_taginfo = pd.read_csv(src_stats_filepath)
    df_taginfo = df_taginfo.sort_values(by='count', ascending=False)
    amenity_columns = df_taginfo['value'][:50].values

    # Read nuts regions
    df_nuts = gpd.read_file(nuts_filepath, driver='GPKG')
    df_nuts = df_nuts[['nuts_id', 'population']]
    if verbose:
        df_nuts.info(memory_usage='deep')

    # Read amenity counts
    df_amenity = pd.read_csv(amenity_filepath)
    if verbose:
        df_amenity.info(memory_usage='deep')

    # Join nuts regions and amenity counts
    df = pd.merge(df_nuts, df_amenity, 
                  on='nuts_id', how='left')

    # Calculate features as counts / population
    df['feature'] = df['counts'] / df['population']
    df = df[['nuts_id', 'amenity', 'feature']]
    df = df.pivot(
        index='nuts_id', columns='amenity', values='feature')
    df = df[amenity_columns]
    if verbose:
        df.info(memory_usage='deep')

    # Save features
    df.to_csv(dst_filepath)
