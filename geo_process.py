import geopandas as gpd
import pandas as pd
import numpy as np
import os
from collections import defaultdict
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.transform import from_bounds
from shapely.geometry import box, Point
import matplotlib.pyplot as plt
from pyproj import Transformer  # for transforming geometries between CRS
from typing import List
from skimage.segmentation import find_boundaries  # to draw only the border
import time

FMM_REP_DATA_PATH = "replicate_fmm/Data/china/"
# for the sea information near china
EXTRA_MAP_PATH = "replicate_fmm/Data/ne_10m_admin_0_countries/"
NORMAL_LON_LAT_CRS = 'EPSG:4326'
CRS_IN_METER = 'EPSG:2333'  # CHGis default CRS
# To avoid typo:
OUTLINE = 'outline'
SEA = 'sea'
RIVER = 'river'
ROAD = 'road'
LOCATION = 'location'


class ChinaGeoProcessor():
    def __init__(self, main_map_path: str, out_path: str = 'output/') -> None:
        self.__filepaths = {OUTLINE: main_map_path}
        self.__out_path = out_path

        if not os.path.exists(out_path):
            os.makedirs(out_path)

    def add_sea(self, path: str):
        self.__filepaths[SEA] = path

    def add_rivers(self, path: str):
        self.__filepaths[RIVER] = path

    def add_roads(self, path: str):
        self.__filepaths[ROAD] = path

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
        cols_to_keep = ['portcode', 'lon', 'lat']
        fake_data = [[0, 0, 0]]  # avoid concat empty dataframe later
        point_df = pd.DataFrame(fake_data, columns=cols_to_keep)

        cur_ptcode = 1000
        for i, p in enumerate(add_points):
            if not p:
                continue
            cur_ptcode += i
            new_row = {c: val for c, val in zip(cols_to_keep, [cur_ptcode]+p)}
            point_df = point_df.append(new_row)

        if port_path:
            ports = pd.read_excel(port_path)
            ports = ports[cols_to_keep]
            point_df = pd.concat([ports, point_df], ignore_index=True)

        # 0 is fake data, not a valid code in our data
        point_df = point_df[point_df['portcode'] != 0]

        point_gdf = gpd.GeoDataFrame(
            point_df,
            geometry=gpd.points_from_xy(point_df['lon'], point_df['lat'])
        )
        point_gdf.set_crs(NORMAL_LON_LAT_CRS, inplace=True)  # EPSG:4326

        self.__filepaths[LOCATION] = point_gdf

        print('Location dataframe created.')

    def generate_matrices(self):
        '''
        This function will return a dict of matrices stated to add.

        Return
        ------
        matrices
            dict. Besides 'location' will be a list of index, all others are
            map matrices.
        map_info
            dict. Includes transform for maps and the crs.
        '''
        col_to_note = {
            OUTLINE: 'NAME_FT',  # province names
            SEA: 'SOVEREIGNT',  # country names
            RIVER: 'NAME_FT',  # river names
            ROAD: 'type',  # 陸, 水, 水陸
            LOCATION: 'portcode'
        }

        # This is to store info about map that will be used in saving to GeoTiff
        map_info = {}

        # ===============
        #  China Outline
        # ===============
        # EPSG:2333
        cur_map = OUTLINE
        main_gdf = gpd.read_file(
            self.__filepaths[cur_map],
            encoding='utf-8'
        )

        # want to keep only these columns for all of the data, so will need to
        # rename later for each dataset.
        cols_to_keep = ['maptype', 'note', 'geometry']

        # 25047~25051 是南沙群島 (萬里長沙, 千里石塘, 曾母暗沙, 東沙, 中沙)
        main_gdf = main_gdf[main_gdf['SYS_ID'] < '25047']

        main_gdf['maptype'] = cur_map
        main_gdf.rename(columns={col_to_note[cur_map]: 'note'}, inplace=True)
        main_gdf = main_gdf[cols_to_keep]

        # ===========================
        #  River, Road, and Location
        # ===========================
        # river first because need to combine river and outline (both 2333) first
        # and then turn them into 4326 to combine with road, location, and later sea
        for cur_map in [RIVER, ROAD, LOCATION]:
            if not cur_map in self.__filepaths.keys():
                # if river is not added, convert the main gdf to lon lat
                # (if it was added, the conversion will happen after main and river merged)
                if cur_map == RIVER:
                    print(f"No {cur_map}")
                    main_gdf = main_gdf.to_crs(NORMAL_LON_LAT_CRS)
                continue  # if this map is not added, ignore it

            print(f"With {cur_map}")
            # get the gdf
            if cur_map == LOCATION:
                # avoid changes apply to the original dataframe
                cur_gdf = self.__filepaths[cur_map].copy()
            else:
                cur_gdf = gpd.read_file(
                    self.__filepaths[cur_map],
                    encoding='utf-8'
                )

            # later will based on this to give values (on the matrix)
            cur_gdf['maptype'] = cur_map

            # the original ming traffic data does not include CRS, but it is lon lat
            if cur_map == ROAD:
                cur_gdf = cur_gdf.set_crs(NORMAL_LON_LAT_CRS)

            # keep the informative column and turn its name to 'note'
            cur_gdf.rename(
                columns={col_to_note[cur_map]: 'note'}, inplace=True)
            cur_gdf = cur_gdf[cols_to_keep]

            main_gdf = pd.concat([main_gdf, cur_gdf], ignore_index=True)

            if cur_map == RIVER:
                main_gdf = main_gdf.to_crs(NORMAL_LON_LAT_CRS)

        # Bounds in lon, lat
        # [ 69.75457966  18.160896   144.75150107  55.92380503]
        lon_min, lat_min, lon_max, lat_max = main_gdf.total_bounds

        # =================
        #  Sea (EPSG:4326)
        # =================
        # Steps: set bound -> same prep steps as other maps
        #    some concern here is the coast line might have some pixel overlapping,
        #    => will use pixels from Outline if conflict
        cur_map = SEA
        if cur_map in self.__filepaths.keys():
            world = gpd.read_file(self.__filepaths[cur_map])
            east_asia = gpd.clip(world, box(
                lon_min, lat_min, lon_max, lat_max))

            east_asia['maptype'] = cur_map
            east_asia.rename(
                columns={col_to_note[cur_map]: 'note'}, inplace=True)
            east_asia = east_asia[cols_to_keep]

            main_gdf = pd.concat([main_gdf, east_asia], ignore_index=True)

        # =====================
        #  Start Rasterization
        # =====================
        # I set this manually, idea from the scale version in pg.py
        cols, rows = 6000, 4200

        # for transforming geometry to matrix
        transform = from_bounds(lon_min, lat_min, lon_max, lat_max, cols, rows)
        map_info['transform'] = transform

        # get current crs
        map_info['crs'] = main_gdf.crs

        # base value
        bv = 250  # lower than 255

        # each map type will store a distinct matrix,
        # except for location, it will be list of indices of the locations in the matrix
        matrices = {}

        sub_vals = {
            ROAD: {'陸': bv, '水': bv//2, '水陸': bv//5},
            LOCATION: dict(zip(
                self.__filepaths[LOCATION]['portcode'],
                self.__filepaths[LOCATION].index + 1
            ))
        }

        for type in self.__filepaths.keys():
            cur_type_map = main_gdf[main_gdf['maptype'] == type]

            # Since directly rasterize wouldn't retain the information for
            # each location point. I will use portcodes' index as the value
            if type in [ROAD, LOCATION]:
                geom_vals = [
                    (geom, sub_vals[type].get(note, 0))
                    for geom, note in zip(cur_type_map.geometry, cur_type_map['note'])
                ]
            else:
                geom_vals = [(geom, bv) for geom in cur_type_map.geometry]

            matrix = rasterize(
                geom_vals,
                out_shape=(rows, cols),
                transform=transform,
                fill=0,
                all_touched=True,  # Adjust as needed for precision
                dtype='uint8'
            )

            if type == LOCATION:
                to_df = []
                # This step takes some time
                for ptcode, val in sub_vals[type].items():
                    new_row = [ptcode] + np.argwhere(matrix == val)[0].tolist()
                    to_df.append(new_row)

                out_df = pd.DataFrame(
                    to_df, columns=['portcode', 'row', 'col'])

                matrices[type] = pd.merge(
                    out_df, self.__filepaths[type].drop(columns=['geometry']),
                    on='portcode', how='left'
                )
            else:
                matrices[type] = matrix

            print(f"Matrix of {type} Done!")

        return matrices, map_info

    def plot_matrix(self, mat: np.ndarray, map_info: dict,
                    title: str = "title", save_im=False):
        '''Save the raster as a GeoTIFF'''
        fig, ax = plt.subplots()
        cax = ax.imshow(mat, cmap='gray', interpolation='none')
        ax.set_axis_off()

        if save_im:
            output_path = self.__out_path + f'China_{title}.tif'

            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=mat.shape[0],
                width=mat.shape[1],
                count=1,  # Number of bands, eg. 3 means RGB
                dtype=mat.dtype,
                crs=map_info['crs'],  # Coordinate system
                transform=map_info['transform']  # Transformation matrix
            ) as dst:
                dst.write(mat, 1)  # Write the raster data to the first band
            print(f"Map of {title} saved.")
        else:
            plt.show()


def main():
    start_time = time.time()
    out_path = "output/"
    cgp = ChinaGeoProcessor(
        main_map_path=f"{FMM_REP_DATA_PATH}CHGis/v6_1820_prov_pgn_utf/",
        out_path=out_path
    )

    # cgp.add_sea(path="replicate_fmm/Data/ne_10m_admin_0_countries/")
    # cgp.add_rivers(path=f"{FMM_REP_DATA_PATH}CHGis/v6_1820_coded_rvr_lin_utf/")
    # cgp.add_roads(path=f"{FMM_REP_DATA_PATH}ming_traffic/")
    cgp.add_locations(port_path='data/top_ports_lon_lat.xlsx')

    mats, map_info = cgp.generate_matrices()

    for t, m in mats.items():
        if t == LOCATION:
            # m.to_csv(f'{out_path}China_customs.csv', index=False)
            m.to_stata(f'{out_path}China_customs.dta', write_index=False)
        else:
            cgp.plot_matrix(mat=m, map_info=map_info, title=t, save_im=True)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.4f} seconds")


if __name__ == "__main__":
    main()
