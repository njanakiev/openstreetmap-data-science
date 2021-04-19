import argparse
import requests
import pandas as pd


def load_values(key, pages=1, results_per_page=100):
    """Load statistics for most common values for a given key in
    OpenStreetMap via the taginfo API"""
    taginfo_url = "https://taginfo.openstreetmap.org/api/4/key/values"
    data = []
    for i in range(pages):
        r = requests.get(taginfo_url, params={
            'key': key,
            'page': i,
            'rp': results_per_page,
            'sortname': 'count',
            'sortorder': 'desc'
        })
        data += r.json()['data']

    df = pd.DataFrame(data).drop_duplicates()
    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Download statistics from taginfo.openstreetmap.org API")
    parser.add_argument(
        'key', type=str, help='OpenStreetMap tag')
    parser.add_argument(
        'filepath', type=str, help='Destination filepath')
    parser.add_argument(
        '-v', '--verbose', action='store_true', 
        help='verbose output')
    args = parser.parse_args()

    df = load_values(args.key, 10, 500)
    if args.verbose:
        df.info(memory_usage='deep')

    df.to_csv(args.filepath, index=False)
