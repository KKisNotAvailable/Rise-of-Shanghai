import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries

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
   (interactive) https://www.ageeye.cn/china/

3. the small dotted lines could be the official roads
   https://openmuseum.tw/muse/digi_object/6e47e7b0da0762633c25a773a6a01d19

4. has ming dynasty's official road (interactive map)
   https://gis.sinica.edu.tw/showwmts/index.php?s=ccts&l=mingtraffic

5. from palace museum (13排銅版map)
   https://rarebooks-maps.npm.edu.tw/index.php?act=Archive/drawing/1-20/eyJzZWFyY2giOltdLCJ0cGZpbHRlciI6eyJwcV9zdWJqZWN0Ijp7InRlcm1zIjpbIui8v%2BWcsOmhniJdfX19   
'''

def peep_geo(map_name):
    cur_map = gpd.read_file(
        f"{FMM_REP_DATA_PATH}CHGis/{map_name}/", 
        encoding='utf-8'
    )

    print(cur_map.crs)
    print(cur_map.info())
    print(cur_map.head(5))

    # print(cur_map[['SYS_ID', 'NAME_FT']])

    # check = cur_map.head(5)
    # check.to_csv(f"{FMM_REP_DATA_PATH}{mn}.csv", index=False)

def plot_test(map_name):
    '''
    This is to test how to transform the border / land area to matrix

    TODO:
    1. the ratio of width and height (等比例縮小吧 改個寫法)
    '''
    cur_map = gpd.read_file(
        f"{FMM_REP_DATA_PATH}CHGis/{map_name}/", 
        encoding='utf-8'
    )

    # 25047~25051 是南沙群島 (萬里長沙, 千里石塘, 曾母暗沙, 東沙, 中沙)
    cur_map = cur_map[cur_map['SYS_ID'] <= '25047']

    # print(cur_map['NAME_FT'])

    adjust_scale = 1000

    minx, miny, maxx, maxy = cur_map.total_bounds

    # Calculate the width and height of each grid cell
    cols = int((maxx - minx) / adjust_scale)
    rows = int((maxy - miny) / adjust_scale)

    # Create a numpy matrix to hold the rasterized data
    matrix = np.zeros((rows, cols), dtype=int)

    # Rasterize the polygons
    transform = rasterio.transform.from_bounds(
        minx, miny, maxx, maxy, 
        width=cols, height=rows
    )

    # Iterate through each polygon in the GeoDataFrame and update the matrix
    for geom in cur_map['geometry']:
        # Convert the polygon to a rasterized mask
        mask = geometry_mask([geom], transform=transform, invert=True, out_shape=(rows, cols))
        
        # Update the matrix where the mask is True
        matrix[mask] = 1

    # 但真的在計算的時候陸地用1應該會比較方便吧 不用border
    border_matrix = find_boundaries(matrix, mode='inner')

    # Display the resulting matrix
    plt.imshow(matrix, cmap='gray', interpolation='none')
    plt.title("Matrix Representation of the China Map")
    plt.xlabel("Columns")
    plt.ylabel("Rows")
    plt.show()

def main():
    # lin = LINESTRING; pgn = POLYGON
    mn = "v6_1820_coded_rvr_lin_utf"
    mn = "v5_1820_coast_lin"
    mn = "v6_1820_prov_pgn_utf" # NAME_FT is traditional chinese
    # peep_geo(mn)
    plot_test(mn)


if __name__ == "__main__":
    main()