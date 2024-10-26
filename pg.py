import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.transform import from_bounds
from shapely.geometry import box
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries  # to draw only the border

FMM_REP_DATA_PATH = "replicate_fmm/Data/china/"

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
    print(cur_map.columns)
    print(cur_map.info())
    print(cur_map.head(5))

    # print(cur_map[['SYS_ID', 'NAME_FT']])
    print(cur_map[['SEA_ID', 'SOURCE', 'ARC_ID']])

    # Get distribution of "type"
    # check_dist = cur_map['type'].value_counts()
    # print(check_dist)

    # check = cur_map.head(5)
    # check.to_csv(f"{FMM_REP_DATA_PATH}{mn}.csv", index=False)


def contour_matrix(map_name: str) -> np.ndarray:
    '''
    transform the border / land area to matrix and plot

    Return
    ------
    2d ndarray
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

    # determine the size of matrix
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
        mask = geometry_mask([geom], transform=transform,
                             invert=True, out_shape=(rows, cols))

        # Update the matrix where the mask is True
        matrix[mask] = 1

    map_info = {
        'minx': minx,
        'miny': miny,
        'maxx': maxx,
        'maxy': maxy,
        'rows': rows,
        'cols': cols,  # would like to check if transform carries the data above, if yes then no need to keep
        'transform': from_bounds(minx, miny, maxx, maxy, cols, rows),
        'crs': cur_map.crs
    }

    print('Contour Done.')
    return matrix, map_info


def line_to_matrix(filename: str, map_info: dict):
    '''
    River:
        'FNODE_', 'TNODE_', 'LENGTH', 'CODED_RIVE', 'CODED_RI_1', 'KEY_ID',
        'SYSTEM_ID', 'MOUTH', 'ORDER_', 'RIVERS_ID', 'KEY_ID_1', 'NAME_CH',
        'NAME_FT', 'NAME_PY', 'MIDPOINT_X', 'MIDPOINT_Y', 'geometry'

    Coast line:
        'SEA_ID', 'SOURCE', 'ARC_ID', 'geometry'

    Ming roads:
        columns: 'type', 'name', 'geometry'
        type: 陸(1009) or 水(436) or 水陸(23)
        name: start ~ end, eg. 會同館～固節驛

    '''
    value_mapping = {'陸': 1, '水': 0.5, '水陸': 0.2}

    if filename == 'ming_traffic':
        cur_lines = gpd.read_file(
            f"{FMM_REP_DATA_PATH}{filename}/",
            encoding='utf-8'
        )
        # the original LINESTRING currently is in normal long-lat format
        cur_lines = cur_lines.set_crs("EPSG:4326")
        cur_lines = cur_lines.to_crs(map_info['crs'])
    else:
        cur_lines = gpd.read_file(
            f"{FMM_REP_DATA_PATH}CHGis/{filename}/",
            encoding='utf-8'
        )

    if not 'type' in cur_lines.columns:
        cur_lines['type'] = '陸'

    # Rasterize the river geometries
    raster = rasterize(
        ((geom, value_mapping[road_type]) for geom, road_type in zip(
            cur_lines['geometry'], cur_lines['type'])),
        out_shape=(map_info['rows'], map_info['cols']),
        # maps pixel coordinates to geographic coordinates
        transform=map_info['transform'],
        fill=0,  # Value for empty cells
        all_touched=True,  # Include all pixels touched by river, coast line, roads
    )

    return raster


def plot_matrix(mat: np.ndarray, title: str = "some title", save_fig=True):
    n, m = mat.shape
    fig, ax = plt.subplots()
    cax = ax.imshow(mat, cmap='gray', interpolation='none')
    # ax.set_title(title)
    ax.set_axis_off()

    if save_fig:
        plt.savefig(
            f'{FMM_REP_DATA_PATH}raw/{title}.tif',
            format='tiff',
            dpi=600
        )
    else:
        plt.show()


def main():
    # lin = LINESTRING; pgn = POLYGON

    mn = "v5_1820_coast_lin"
    # peep_geo(mn)

    # contour
    cont = "v6_1820_prov_pgn_utf"  # NAME_FT is traditional chinese
    cont_mat, map_info = contour_matrix(cont)  # 4761, 6075
    # plot_matrix(cont_mat, title='China - outline', save_fig=False)

    # river
    rvr = "v6_1820_coded_rvr_lin_utf"
    # rvr_mat = line_to_matrix(rvr, map_info=map_info)
    # plot_matrix(rvr_mat, title='China - rivers', save_fig=False)

    # coast
    coast = "v5_1820_coast_lin"
    # coast_mat = line_to_matrix(coast, map_info=map_info)
    # plot_matrix(coast_mat, title='China - coastline', save_fig=False)

    # road data
    road_ming = 'ming_traffic'
    # road_mat = line_to_matrix(road_ming, map_info=map_info)
    # plot_matrix(road_mat, title='China - Ming Roads', save_fig=False)

    print("Done")


if __name__ == "__main__":
    main()
