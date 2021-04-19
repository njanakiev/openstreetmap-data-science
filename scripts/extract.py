import gzip
import math
import osmium
import shapely.wkb
import pandas as pd
from enum import Enum
from collections import defaultdict


class OSMType(Enum):
    node=0
    way=1
    area=2
    relation=3


class OSMTagHandler(osmium.SimpleHandler):
    def __init__(self, key, file_handler=None, filter_amenities=None):
        super(OSMTagHandler, self).__init__()
        self.key = key
        self.file_handler = file_handler
        self.filter_amenities = filter_amenities
        self.counter = defaultdict(int)
        self.bounds = [math.inf, math.inf, -math.inf, -math.inf]

        if self.file_handler is not None:
            # Write CSV header
            self.file_handler.write("osm_id,osm_type,amenity,lon,lat\n")
            self.wkbfab = osmium.geom.WKBFactory()

    def write_row(self, osm_id, osm_type, amenity, lon=None, lat=None):
        lon = "" if lon is None else lon
        lat = "" if lat is None else lat
        self.file_handler.write(
            f"{osm_id},{osm_type},{amenity},{lon},{lat}\n")

    def update_bounds(self, lon, lat):
        if lon is not None and lat is not None:
            if lon < self.bounds[0]:
                self.bounds[0] = lon
            if lon > self.bounds[2]:
                self.bounds[2] = lon
            if lat < self.bounds[1]:
                self.bounds[1] = lat
            if lat > self.bounds[3]:
                self.bounds[3] = lat

    def process_element(self, elem, osm_type):
        for tag in elem.tags:
            if (tag.k == self.key) and \
               (tag.v in self.filter_amenities if self.filter_amenities else True):
                self.counter[osm_type.name] += 1
                self.counter['total'] += 1
                if self.file_handler is None:
                    break

                lon, lat = None, None
                try:
                    if osm_type == OSMType.node:
                        lon = elem.location.lon
                        lat = elem.location.lat 
                    elif osm_type == OSMType.way:
                        geom = shapely.wkb.loads(
                            self.wkbfab.create_linestring(elem), 
                            hex=True)
                        c = geom.centroid
                        lon, lat = c.x, c.y
                    elif osm_type == OSMType.area:
                        geom = shapely.wkb.loads(
                            self.wkbfab.create_multipolygon(elem), 
                            hex=True)
                        c = geom.centroid
                        lon, lat = c.x, c.y
                except RuntimeError as e:
                    print(f"RuntimeError: {e}, for {osm_type.name}: {elem.id}")

                self.update_bounds(lon, lat)
                self.write_row(elem.id, osm_type.value, tag.v, lon, lat)

    def node(self, elem):
        self.process_element(elem, OSMType.node)

    def way(self, elem):
        self.process_element(elem, OSMType.way)

    def area(self, elem):
        self.process_element(elem, OSMType.area)

    def relation(self, elem):
        self.process_element(elem, OSMType.relation)


if __name__ == '__main__':
    src_filepath = "data/europe-amenity.osm.pbf"
    src_stats_filepath = "data/taginfo_amenity_counts.csv"
    dst_filepath = "data/europe-amenity.csv.gz"
    key = "amenity"

    # Load taginfo statistics
    df_taginfo = pd.read_csv(src_stats_filepath)
    df_taginfo = df_taginfo.sort_values(by='count', ascending=False)
    filter_amenities = set(df_taginfo['value'][:50].values)

    with gzip.open(dst_filepath, "wt") as f:
        handler = OSMTagHandler("amenity", f, filter_amenities=filter_amenities)
        handler.apply_file(src_filepath)
        print(handler.counter)
        print(handler.bounds)
