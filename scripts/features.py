import argparse
import pandas as pd
import geopandas as gpd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Features")
    parser.add_argument(
        help="Amanity counts filepath .csv.gz or .csv",
        action='store', dest='amenity_filepath')
    parser.add_argument(
        help="NUTS geometry filepath",
        action="store", dest="nuts_filepath")
    parser.add_argument(
        help="Taginfo stats filepath",
        dest='src_stats_filepath')
    parser.add_argument(
        help="Output filepath csv.gz or txt.gz",
        action='store', dest='dst_filepath')
    parser.add_argument(
        "-v", "--verbose",
        help="Verbose output",
        action="store_true", dest="verbose")
    args = parser.parse_args()

    # Load taginfo statistics
    df_taginfo = pd.read_csv(args.src_stats_filepath)
    df_taginfo = df_taginfo.sort_values(by='count', ascending=False)
    amenity_columns = df_taginfo['value'][:50].values

    # Read nuts regions
    df_nuts = gpd.read_file(args.nuts_filepath, driver='GPKG')
    df_nuts = df_nuts[['nuts_id', 'population']]
    if args.verbose:
        df_nuts.info(memory_usage='deep')

    # Read amenity counts
    df_amenity = pd.read_csv(args.amenity_filepath)
    if args.verbose:
        df_amenity.info(memory_usage='deep')

    # Join nuts regions and amenity counts
    df = pd.merge(
        df_nuts, df_amenity, on='nuts_id', how='left')

    # Calculate features as counts / population
    df['feature'] = df['counts'] / df['population']
    df = df[['nuts_id', 'amenity', 'feature']]
    df = df.pivot(
        index='nuts_id', columns='amenity', values='feature')
    df = df[amenity_columns]
    if args.verbose:
        df.info(memory_usage='deep')

    # Save features
    df.to_csv(args.dst_filepath)
