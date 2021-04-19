import argparse
import geopandas as gpd


def download_ne_regions(filepath, verbose=False):
    resolution = "10m"
    for layer_type in ["admin_0_countries", "admin_1_states_provinces"]:

        layer_name = f"ne_{resolution}_{layer_type}"
        url = "https://naciscdn.org/naturalearth/" \
              f"{resolution}/cultural/{layer_name}.zip"
        if verbose:
            print(f"Downloading {url}")
        
        gdf_ne = gpd.read_file(url, driver="ESRI Shapefile")
        gdf_ne.columns = [column.lower() for column in gdf_ne.columns]
        gdf_ne = gdf_ne[['ne_id', 'iso_a2', 'name', 'geometry']]
        gdf_ne.to_file(
            filepath, 
            driver='GPKG', 
            layer=layer_name)
        
        if verbose:
            print(f"Saved to {filepath}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download and prepare Eurostat NUTS regions with population data")
    parser.add_argument(
        'filepath', type=str, help='destination filepath')
    parser.add_argument(
        '-v', '--verbose', action='store_true', 
        help='verbose output')
    args = parser.parse_args()

    download_ne_regions(args.filepath, verbose=args.verbose)
