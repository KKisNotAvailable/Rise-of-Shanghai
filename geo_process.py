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
CRS_IN_METER = 'EPSG:2333' # CHGis default CRS

class ChinaGeoProcessor():
    def __init__(self, main_map_path: str) -> None:
        # 1X: Polygon and MultiPolygon, 2X: LineString, 3X: Point (not official code, just to distinguish)
        self.geotype_code = {
            'outline': 11,
            'sea': 12,
            'river': 21,
            'road': {'陸': 22, '水': 23, '水陸': 24}, # from column 'note' (originally 'type')
            'location': 30
        }
        self.__filepaths = {
            'outline': main_map_path
        } # this will have the same keys as geotype_code

    def add_sea(self, path: str):
        self.__filepaths['sea'] = path

    def add_rivers(self, path: str):
        self.__filepaths['river'] = path

    def add_roads(self, path: str):
        self.__filepaths['road'] = path

    def add_locations(self, port_path: str = "", add_points: List[List[float]] = [[]]):
        '''
        Given the port path and points to add, this function will add a 
        geoDataFrame to the self.__filepath pending for process with other
        maps. 
        Will give an empty dataframe if both of the arguments are empty.

        Parameter
        ---------
        port_path: str.
            Expected to be the file with the ports.
        add_points: List[List[float]].
            Expected to be list of points, and each point is a list of lon and lat.
        '''
        # TODO: currently ignore the warning, but need to fix:
        #    HOW TO DEAL WITH EMPTY DATAFRAME (one or both of them)
        cols_to_keep = ['portcode', 'lon', 'lat']
        point_df = pd.DataFrame(columns=cols_to_keep)

        cur_portcode = 1000
        for i, p in enumerate(add_points):
            if not p:
                continue
            cur_portcode += i
            new_row = {c: val for c, val in zip(cols_to_keep, [cur_portcode]+p)}
            point_df = point_df.append(new_row)

        if port_path:
            ports = pd.read_excel(port_path)
            ports = ports[cols_to_keep]
            point_df = pd.concat([ports, point_df], ignore_index=True)
        
        point_gdf = gpd.GeoDataFrame(
            point_df, 
            geometry=gpd.points_from_xy(point_df['lon'], point_df['lat'])
        )
        point_gdf.set_crs(NORMAL_LON_LAT_CRS, inplace=True) # EPSG:4326

        self.__filepaths['location'] = point_gdf

    def generate_matrices(self):
        '''
        This function will return a dict of matrices stated to add.
        
        Return
        ------
            dict. Besides 'location' will be a list of index, all others are
            map matrices.
        '''
        col_to_note = {
            'outline': 'NAME_FT', # province names
            'sea': 'SOVEREIGNT', # country names
            'river': 'NAME_FT', # river names
            'road': 'type', # 陸, 水, 水陸
            'location': 'portcode'
        }

        # ===============
        #  China Outline
        # ===============
        # EPSG:2333
        cur_map = 'outline'
        main_gdf = gpd.read_file(
            self.__filepaths[cur_map],
            encoding='utf-8'
        )

        # want to keep only these columns for all of the data, so will need to
        # rename later for each dataset.
        cols_to_keep = ['maptype', 'note', 'geometry']

        # 25047~25051 是南沙群島 (萬里長沙, 千里石塘, 曾母暗沙, 東沙, 中沙)
        main_gdf = main_gdf[main_gdf['SYS_ID'] <= '25047']

        main_gdf['maptype'] = cur_map
        main_gdf.rename(columns={col_to_note[cur_map]: 'note'}, inplace=True)
        main_gdf = main_gdf[cols_to_keep]

        # ===========================
        #  River, Road, and Location
        # ===========================
        # river first because need to combine river and outline (both 2333) first
        # and then turn them into 4326 to combine with road, location, and later sea
        for cur_map in ['river', 'road', 'location']:
            if not cur_map in self.__filepaths.keys():
                # if river is not added, convert the main gdf to lon lat
                # (if it was added, the conversion will happen after main and
                # river merged)
                if cur_map == 'river':
                    main_gdf = main_gdf.to_crs(NORMAL_LON_LAT_CRS)
                continue # if this map is not added, ignore it

            # get the gdf
            if cur_map == 'location':
                cur_gdf = self.__filepaths[cur_map]
            else:
                cur_gdf = gpd.read_file(
                    self.__filepaths[cur_map],
                    encoding='utf-8'
                )

            # later will based on this to give values (on the matrix)
            cur_gdf['maptype'] = cur_map

            # the original ming traffic data does not include CRS, but it is lon lat
            if cur_map == 'road':
                cur_gdf = cur_gdf.set_crs(NORMAL_LON_LAT_CRS)

            # keep the informative column and turn its name to 'note'
            cur_gdf.rename(columns={col_to_note[cur_map]: 'note'}, inplace=True)
            cur_gdf = cur_gdf[cols_to_keep]

            main_gdf = pd.concat([main_gdf, cur_gdf], ignore_index=True)

            if cur_map == 'river':
                main_gdf = main_gdf.to_crs(NORMAL_LON_LAT_CRS)


        # Bounds in lon, lat
        lon_min, lat_min, lon_max, lat_max = main_gdf.total_bounds

        # =================
        #  Sea (EPSG:4326)
        # =================
        # Steps: set bound -> same prep steps as other maps
        #    some concern here is the coast line might have some pixel overlapping,
        #    => will use pixels from Outline if conflict
        cur_map = 'sea'
        if cur_map in self.__filepaths.keys():
            world = gpd.read_file(self.__filepaths[cur_map])
            east_asia = gpd.clip(world, box(lon_min, lat_min, lon_max, lat_max))

            east_asia['maptype'] = cur_map
            east_asia.rename(columns={col_to_note[cur_map]: 'note'}, inplace=True)
            east_asia = east_asia[cols_to_keep]

            main_gdf = pd.concat([main_gdf, east_asia], ignore_index=True)
        # TODO: should check the issue of wierd blocks at the edges

        # =====================
        #  Start Rasterization
        # =====================
        main_gdf = main_gdf.to_crs(CRS_IN_METER) # EPSG:4326 => 2333

        minx, miny, maxx, maxy = main_gdf.total_bounds

        adjust_scale = 1000 # can get this value with int(map_info['transform'].a)

        # determine the size of matrix
        cols = int((maxx - minx) / adjust_scale)
        rows = int((maxy - miny) / adjust_scale)

        # for transforming geometry to matrix
        transform = from_bounds(minx, miny, maxx, maxy, cols, rows)

        # each map type will store a distinct matrix
        所以要改寫法
        for _, row in main_gdf.iterrows():
            # initiate a matrix
            matrix = np.zeros((rows, cols), dtype=int)
            # Convert the polygon to a rasterized mask
            mask = geometry_mask(
                [row['geometry']], transform=transform, invert=True, out_shape=(rows, cols)
            )

            # Update the matrix where the mask is True
            cur_type = row['maptype']
            if cur_type == 'road': # 陸, 水, 水陸
                val_to_set = self.geotype_code[cur_type][row['note']]
            else:
                val_to_set = self.geotype_code[cur_type]

            matrix[mask] = val_to_set

        print(matrix)

        # 4. 依照matrix裡面的值來切回不同的圖
        


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
            encoding='utf-8'
        )
        # the original LINESTRING currently is in normal long-lat format
        cur_lines = cur_lines.set_crs(NORMAL_LON_LAT_CRS)
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


def main():
    cgp = ChinaGeoProcessor(
        main_map_path=f"{FMM_REP_DATA_PATH}CHGis/v6_1820_prov_pgn_utf/"
    )

    cgp.add_sea(path="replicate_fmm/Data/ne_10m_admin_0_countries/")
    cgp.add_rivers(path=f"{FMM_REP_DATA_PATH}CHGis/v6_1820_coded_rvr_lin_utf/")
    cgp.add_roads(path=f"{FMM_REP_DATA_PATH}ming_traffic/")
    cgp.add_locations(port_path='data/top_ports_lon_lat.xlsx')

    cgp.generate_matrices()


if __name__ == "__main__":
    main()
