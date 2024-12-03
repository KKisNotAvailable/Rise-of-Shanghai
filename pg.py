import geopandas as gpd
import pandas as pd
import numpy as np
from collections import defaultdict
from rasterio.features import geometry_mask, rasterize
from rasterio.transform import from_bounds
from shapely.geometry import box, Point
import matplotlib.pyplot as plt
from pyproj import Transformer
from typing import List
from skimage.segmentation import find_boundaries  # to draw only the border

FMM_REP_DATA_PATH = "replicate_fmm/Data/china/"
EXTRA_MAP_PATH = "replicate_fmm/Data/ne_10m_admin_0_countries/" # for the sea information near china
NORMAL_LON_LAT_CRS = 'EPSG:4326'

# This dict is to set the values for different geometry types
# >> the reason behind this is to avoid distortion (some data need to transform 
#    from EPSG:4326 to WPSG:2333), so transform everything first to 4326, and 
#    back to 2333, we need to keep them in the same geo DataFrame.
GEO_TYPE_CODE = defaultdict(lambda: 1)
GEO_TYPE_CODE['LineString'] = 2 # road and river
GEO_TYPE_CODE['Point'] = 3 # location points

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


def polygon_to_matrix(cur_map, map_info):
    '''
    This function is to rasterize maps with polygon as geometry.
    Used on China outline and sea.
    '''
    rows, cols = map_info['rows'], map_info['cols']
    matrix = np.zeros((rows, cols), dtype=int)

    # Iterate through each polygon in the GeoDataFrame and update the matrix
    for geom in cur_map['geometry']:
        # Convert the polygon to a rasterized mask
        mask = geometry_mask([geom], transform=map_info['transform'],
                             invert=True, out_shape=(rows, cols))

        # Update the matrix where the mask is True
        matrix[mask] = 1

    return matrix


def contour_matrix(map_name: str) -> np.ndarray:
    '''
    transform the border / land area to matrix and plot
    ['SYS_ID', 'NAME_PY', 'NAME_CH', 'NAME_FT', 'NOTE_ID', 'OBJ_TYPE',
     'GEO_SRC', 'COMPILER', 'GEOCOMP', 'CHECKER', 'ENT_DATE', 'X_COORD',
     'Y_COORD', 'AREA', 'geometry']

    Return
    ------
    2d ndarray
    '''
    cur_map = gpd.read_file(
        f"{FMM_REP_DATA_PATH}CHGis/{map_name}/",
        encoding='utf-8'
    )

    # 25047~25051 是南沙群島 (萬里長沙, 千里石塘, 曾母暗沙, 東沙, 中沙)
    cur_map = cur_map[cur_map['SYS_ID'] < '25047']

    cur_map = cur_map.to_crs('EPSG:4326')
    cur_map = cur_map.to_crs('EPSG:2333')

    minx, miny, maxx, maxy = cur_map.total_bounds

    # for correctly set the boundries for other matrices
    normal_lon_lat_map = cur_map.to_crs(NORMAL_LON_LAT_CRS)

    adjust_scale = 1000 # can get this value with int(map_info['transform'].a)

    # determine the size of matrix
    cols = int((maxx - minx) / adjust_scale)
    rows = int((maxy - miny) / adjust_scale)

    map_info = {
        'lon_lat_bounds': normal_lon_lat_map.total_bounds,
        'rows': rows,
        'cols': cols,  # would like to check if transform carries the data above, if yes then no need to keep
        'transform': from_bounds(minx, miny, maxx, maxy, cols, rows),
        'crs': cur_map.crs
    }

    # ======
    #  Test
    # ======
    def test():
        print(f"The bounds of the original map is: {cur_map.total_bounds}")
        print(f"The bounds of the normal map is: {normal_lon_lat_map.total_bounds}")
        crs1 = 'EPSG:4326'
        crs2 = 'EPSG:2333'

        # 1. take the original bounds, use Transform and compare with normal_map
        print(">>> Test 1: EPSG:2333 to EPSG:4326")
        transformer1 = Transformer.from_crs(crs2, crs1, always_xy=True)
        print(f"EPSG:2333 min x and y: {minx}, {miny}")
        lon_t, lat_t = transformer1.transform(minx, miny)
        print(f"EPSG:4326 min x and y: {lon_t}, {lat_t}")

        print(f"EPSG:2333 max x and y: {maxx}, {maxy}")
        lon_t, lat_t = transformer1.transform(maxx, maxy)
        print(f"EPSG:4326 max x and y: {lon_t}, {lat_t}")

        # 2. take (0,0) times from_bound, and compare with original bound
        lon_t, lat_t = map_info['transform'] * (0,0)
        print("The (0,0) pair is", lon_t, lat_t)

        # 3. transform the normal map's bound to 2333
        print(">>> Test 3: EPSG:4326 to EPSG:2333")
        transformer2 = Transformer.from_crs(crs1, crs2, always_xy=True)
        x, y, _, _ = normal_lon_lat_map.total_bounds
        print(f"EPSG:4326 min x and y: {x}, {y}")
        lon_t, lat_t = transformer2.transform(x, y)
        print(f"EPSG:2333 min x and y: {lon_t}, {lat_t}")

    # Rasterize the polygons
    matrix = polygon_to_matrix(cur_map=cur_map, map_info=map_info)

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
            encoding='utf-8',
            layer='mingroad_line'
        )
        # the original LINESTRING is in normal long-lat format
        cur_lines = cur_lines.set_crs(NORMAL_LON_LAT_CRS)
        cur_lines = cur_lines.to_crs(map_info['crs'])

        # print(list(cur_lines[cur_lines['type'] != '陸']['name']))
        # return
    else:
        cur_lines = gpd.read_file(
            f"{FMM_REP_DATA_PATH}CHGis/{filename}/",
            encoding='utf-8'
        )

    # for checking river data (river name has a lot of None)
    def river_data_check():
        print(cur_lines[['ORDER_', 'RIVERS_ID', 'KEY_ID_1']])

        # tmp = cur_lines['NAME_FT']
        # tmp = tmp.dropna()
        # n = cur_lines.shape[0]
        # print(f"Total number of rivers: {n}")
        # print(f"Count of rivers with no name: {n - len(tmp)}")
        # print(f"Count of unique river names: {len(set(tmp))}")

    river_data_check()

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


def sea_matrix(map_info: dict, map_path: str = EXTRA_MAP_PATH):
    '''
    Since the outline of China does not indicate where the sea locates,
    I thus use the East Asian countries outline to determine.
    The sea matrix will serve as the 'road' where people can sail.
    '''
    world = gpd.read_file(map_path)

    lon_min, lat_min, lon_max, lat_max = map_info['lon_lat_bounds']

    east_asia = gpd.clip(world, box(lon_min, lat_min, lon_max, lat_max))
    east_asia = east_asia.to_crs(map_info['crs'])

    # Rasterize the polygons
    matrix = polygon_to_matrix(cur_map=east_asia, map_info=map_info)

    # This matrix has lands as 1 and sea as 0, we shall flip them
    matrix = abs(matrix - 1)
    
    # There are no sea available for China on the left (left of long 105 E)
    # we'll set those pixals to 0 as well ('land')
    # NOTE: even if we don't care about the lat, it still need to be in the 
    #       range of original map, otherwise the transform would return some
    #       wierd number 
    bound_lon, bound_lat = 105, 30 

    row_idx, col_idx = lonlat_to_idx(point=[bound_lon, bound_lat], map_info=map_info)

    print(map_info['rows'], map_info['cols'])
    print(row_idx, col_idx)

    # matrix[:, :col_idx] = 0

    return matrix


def lonlat_to_idx(point, map_info):
    '''
    This function would use the transform from the map_info to
    convert the desired point to the pixel index on the matrix
    '''
    lon, lat = point
    transformer = Transformer.from_crs(NORMAL_LON_LAT_CRS, map_info['crs'], always_xy=True)
    lon, lat = transformer.transform(lon, lat)

    row_idx, col_idx = ~map_info['transform'] * (lon, lat)

    return int(np.floor(row_idx)), int(np.floor(col_idx))


def add_points_on_map(
    target_map,
    points: List[List[int]] = [[0, 0]],
    radius: int = 10,
    value: int = 2
):
    '''
    points: expected to be list of row-col indices
    '''
    rows, cols = target_map.shape

    for p in points:
        # TODO: maybe should check if the point actually need transformation
        row_c, col_c = p
        # Define the bounding box around the center
        row_min = max(row_c - radius, 0)
        row_max = min(row_c + radius + 1, rows)
        col_min = max(col_c - radius, 0)
        col_max = min(col_c + radius + 1, cols)

        # Iterate over only the bounding box
        for row in range(row_min, row_max):
            for col in range(col_min, col_max):
                if (row - row_c) ** 2 + (col - col_c) ** 2 <= radius ** 2:
                    target_map[row, col] = value

    return
    

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


def get_locations_mat_idx(loc_df: pd.DataFrame, map_info):
    '''
    This function will turn the location list (with lon and lat)
    into a matrix, having the same size of the map we are using.

    好的，現在這個結果尚可接受，還是對不太齊。
    剛剛想到另一個方法，就是直接在大地圖的GDF下面append這些點，
    這樣在轉crs的時候應該會更準確 (just filter the Points in the 'geometry')
    => cont_mat 加一個argument: include loc, if yes then return an extra list
       of location indices on the matrix, 不要直接畫在outline圖上
    '''
    # TODO: Actually, I'm thinking turning these points just to row and col
    #       index, and then use the add_points_on_map to do the trick

    # 1. get the actual lon lat bounds as points for accurate crs transformation
    min_lon, min_lat, max_lon, max_lat = map_info['lon_lat_bounds']
    four_bounds = [
        {'portcode': 800, 'name_ch': 'bot_left', 'lon': min_lon, 'lat': min_lat},
        {'portcode': 801, 'name_ch': 'top_left', 'lon': min_lon, 'lat': max_lat},
        {'portcode': 802, 'name_ch': 'bot_right', 'lon': max_lon, 'lat': min_lat},
        {'portcode': 803, 'name_ch': 'top_right', 'lon': max_lon, 'lat': max_lat}
    ]
    four_bounds = pd.DataFrame(four_bounds)

    full_loc = pd.concat([loc_df, four_bounds], ignore_index=True)

    geometry = [Point(xy) for xy in zip(full_loc['lon'], full_loc['lat'])]

    gdf = gpd.GeoDataFrame(full_loc, geometry=geometry)
    gdf.set_crs(NORMAL_LON_LAT_CRS, inplace=True)
    gdf.to_crs(map_info['crs'], inplace=True)

    # 2. make all the points times inverse of transform to get the col-row indices
    coords = np.array([(point.x, point.y) for point in gdf['geometry']])
    cols, rows = ~map_info['transform'] * (coords[:, 0], coords[:, 1])

    cols_idx = np.floor(cols).astype(int)
    rows_idx = np.floor(rows).astype(int)

    # 3. discard the last four points (bounds)
    cols_idx = cols_idx[:-4]
    rows_idx = rows_idx[:-4]

    return [[r, c] for r, c in zip(rows_idx, cols_idx)]


def test_crs_transform(pt):
    '''
    SUPER WIERD! The following geo point transformation works as I thought
    but in our map transformation it was not like this...

    Ans: Since 2333 is in meters and 4326 is degree, and the direct transform
         back and forth gets the same result with the same default setting. 
         However, transforming the entire map would include the information of 
         the bounds, thus the projection would be different accordingly.
    '''
    lon, lat = pt
    crs1 = 'EPSG:4326'
    crs2 = 'EPSG:2333'

    transformer1 = Transformer.from_crs(crs1, crs2, always_xy=True)
    lon_t, lat_t = transformer1.transform(lon, lat)

    transformer2 = Transformer.from_crs(crs2, crs1, always_xy=True)
    lon_t, lat_t = transformer2.transform(lon_t, lat_t)

    print(f"Original point: {lon}, {lat}")
    print(f"Transformed twice point: {lon_t}, {lat_t}")


def main():
    # lin = LINESTRING; pgn = POLYGON
    # bounds: [ 69.75457966  15.78138    144.75150107  55.92380503]
    # bounds: [15923439.00897854  1745462.32141839 21998532.53324068  6506625.70738582]
    # transform:
    #   | 1000.02, 0.00, 15923439.01|
    #   | 0.00,-1000.03, 6506625.71|
    #   | 0.00, 0.00, 1.00|

    # test_crs_transform([121.564558, 25.03746])

    mn = "v5_1820_coast_lin"
    # peep_geo(mn)

    # NOTE: For all the following matices, I assume them to including only 0 and 1
    # contour
    cont = "v6_1820_prov_pgn_utf"  # NAME_FT is traditional chinese
    cont_mat, map_info = contour_matrix(cont)  # 4497, 6075
    # plot_matrix(cont_mat, title='China - outline', save_fig=False)

    # river
    rvr = "v6_1820_coded_rvr_lin_utf"
    rvr_mat = line_to_matrix(rvr, map_info=map_info)
    # plot_matrix(rvr_mat, title='China - rivers', save_fig=False)

    # road data
    road_ming = 'ming_traffic'
    # road_mat = line_to_matrix(road_ming, map_info=map_info)
    # plot_matrix(road_mat, title='China - Ming Roads', save_fig=False)

    # NOTE: I'm thinking do we need coast anymore? since there's no reason to 
    #       limit sailing only along the coast, should there be a huge bay but 
    #       the destination need to ignore the bay and sail straightly,
    #       in such case, limiting to coast line would overestimate the time
    # coast
    coast = "v5_1820_coast_lin"
    # coast_mat = line_to_matrix(coast, map_info=map_info)
    # plot_matrix(coast_mat, title='China - coastline', save_fig=False)

    # sea data
    # sea_mat = sea_matrix(map_info=map_info)
    # plot_matrix(sea_mat, title='China - sea nearby', save_fig=False)

    # location points
    # locations = pd.read_excel('data/top_ports_lon_lat.xlsx')
    # keep_cols = ['portcode', 'name_ch', 'lon', 'lat'] # 'customs'
    # loc_idx = get_locations_mat_idx(loc_df=locations[keep_cols], map_info=map_info)

    # add_points_on_map(cont_mat, loc_idx)
    # plot_matrix(cont_mat, title='China - outline', save_fig=False)

    print("Done")


if __name__ == "__main__":
    main()
