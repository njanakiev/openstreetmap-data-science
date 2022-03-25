import gzip
import math
import logging
import argparse
import osmium
import shapely.wkb
from enum import Enum
from collections import defaultdict


class OSMType(Enum):
    node=0
    way=1
    area=2
    relation=3


class OSMTagHandler(osmium.SimpleHandler):
    def __init__(self, key, file_handler=None, filter_values=None):
        super(OSMTagHandler, self).__init__()
        self.key = key
        self.file_handler = file_handler
        self.filter_values = filter_values
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
               (tag.v in self.filter_values if self.filter_values else True):
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
                    logging.error(f"RuntimeError: {e}, for {osm_type.name}: {elem.id}")

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
    parser = argparse.ArgumentParser(description="OpenStreetMap Extractor")
    parser.add_argument(
        help="Input osm.pbf filepath",
        action='store', dest='src_filepath')
    parser.add_argument(
        help="Output filepath csv.gz or txt.gz",
        action='store', dest='dst_filepath')
    parser.add_argument(
        "-k", "--key",
        help="Specified OSM key",
        dest="key", default="amenity", type=str)
    parser.add_argument(
        "-f", "--filter", 
        help="Filter OSM values",
        dest="filter_values", default=None,
        type=lambda s: s.split(','))
    parser.add_argument(
        "-v", "--verbose",
        help="Verbose output",
        action="store_true", dest="verbose")
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG if args.verbose else logging.INFO)

    logging.debug(f"src_filepath  : {args.src_filepath}")
    logging.debug(f"dst_filepath  : {args.dst_filepath}")
    logging.debug(f"key           : {args.key}")
    logging.debug(f"filter_values : {args.filter_values}")

    if args.dst_filepath.endswith('.csv.gz') or \
       args.dst_filepath.endswith('.txt.gz'):
        with gzip.open(args.dst_filepath, "wt") as f:
            handler = OSMTagHandler(args.key, f, filter_values=args.filter_values)
            handler.apply_file(args.src_filepath)
            logging.info(dict(handler.counter))
            logging.info(handler.bounds)
    elif args.dst_filepath.endswith('.csv') or \
         args.dst_filepath.endswith('.txt'):
        with open(args.dst_filepath, "w") as f:
            handler = OSMTagHandler(args.key, f, filter_values=args.filter_values)
            handler.apply_file(args.src_filepath)
            logging.info(dict(handler.counter))
            logging.info(handler.bounds)    
    else:
        logging.error("Output file type not supported")
        exit(-1)
