import geopandas as gpd
import pandas as pd

FMM_REP_DATA_PATH = "replicate_fmm/Data/"

'''NOTE
建議可以查XX省水路輿圖或數位方輿裡面查"省輿圖"
https://digitalatlas.ascdc.sinica.edu.tw/

Potential Road data
0. have missing but might be a choice in the future
   https://see.org.tw/mqrl/mqrlgis1

1. university of toronto's rail and road data
   https://mdl.library.utoronto.ca/collections/geospatial-data/china-historical-roads-and-rail

2. has map of every province, but not sure have road data (the second link is same thing but might easier to download)
   http://ccamc.org/chinese_historical_map/index.php
   http://www.guoxue123.com/other/map/zgmap/015.htm

3. the small dotted lines could be the official roads
   https://openmuseum.tw/muse/digi_object/6e47e7b0da0762633c25a773a6a01d19

4. has ming dynasty's official road (interactive map)
   https://gis.sinica.edu.tw/showwmts/index.php?s=ccts&l=mingtraffic
'''

def peep_geo(map_name):
    cur_map = gpd.read_file(
        f"{FMM_REP_DATA_PATH}china_map/{map_name}/", 
        encoding='utf-8'
    )

    print(cur_map.crs)
    print(cur_map.info())
    print(cur_map.head(5))

    print(cur_map['X_COORD'])

    # check = cur_map.head(5)
    # check.to_csv(f"{FMM_REP_DATA_PATH}{mn}.csv", index=False)


def main():
    # lin = LINESTRING; pgn = POLYGON
    mn = "v6_1820_coded_rvr_lin_utf"
    mn = "v5_1820_coast_lin"
    mn = "v6_1820_prov_pgn_utf" # NAME_FT is traditional chinese
    peep_geo(mn)


if __name__ == "__main__":
    main()