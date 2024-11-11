import pandas as pd
import os
import numpy as np
import geopandas as gpd
from collections import Counter
import statsmodels.api as sm
import matplotlib.pyplot as plt
from shapely.geometry import Point, box

# write the code in the style align with the upcoming pandas update
# check out https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

THRESHOLD = 100
MAIN_FILE_PATH = "data/data_port_processed.xlsm"
TOP_LOCATION_FILE = "data/top_ports_lon_lat.xlsx"
NORMAL_LON_LAT_CRS = 'EPSG:4326'


def plot_year_wage_scatter(df: pd.DataFrame, cur_port: int, graph_dir: str = "graphs", save_fig=False):
    '''
    This function plots the distribution of wage based on the observation year.
    '''
    df_to_plot = df.loc[df['portcode'] == cur_port,
                        ['year', 'pay']].reset_index(drop=True)

    # year_count = df_to_plot.groupby(by='year').size().reset_index(name='counts')
    # job_count = df_to_plot.groupby(by='rank').size().reset_index(name='counts')

    # https://ithelp.ithome.com.tw/articles/10211370
    plt.scatter(
        df_to_plot['year'].astype("int"),
        df_to_plot['pay']
    )
    ttl = f'{cur_port}_year_wage_scatter'
    plt.title(ttl)

    if save_fig:
        plt.savefig(f"{graph_dir}/{ttl}.jpg")
        plt.close()
    else:
        plt.show()

    return


def wage_index(locations, data: pd.DataFrame) -> pd.Series:
    '''
    This functions makes wage index for each designated area.
    But actually we don't need this, I misunderstood Terry.
    What we need is the fixed effect of each location.
    '''
    print(f'Currently working on location: {locations}')
    if not isinstance(locations, list):
        data = data.drop(columns=['portcode'])

    # limit to the first n years (since using all years won't give a valid result)
    first_n = 10
    first_n_year = data['year'].sort_values().drop_duplicates().head(first_n)
    data = data[data['year'].isin([r for r in first_n_year])]

    # for dropping the first year-col as base year
    min_year = min(data['year'])

    cols_to_dum = [c for c in data.columns if c not in ['pay', 'tenure']]
    data = pd.get_dummies(data, columns=cols_to_dum)

    data = data.drop(columns=[f'year_{min_year}'])

    var_x = [c for c in data.columns if c != 'pay']

    X = data[var_x]
    y = np.log(data['pay'])

    X = sm.add_constant(X)

    model = sm.OLS(y, X.astype(float)).fit()

    print(model.summary())

    p = model.params
    year_coef = p[p.index.str.contains('year')]

    # 最後有的會少這麼多職業我猜是因為在限制前10年資料下，很多職業就沒了
    return pd.concat([pd.Series([1], index=[f'year_{min_year}']), year_coef])


def location_fixed_effect(df: pd.DataFrame, suffixes: list, locations: list = [], display_fit_result=False) -> pd.DataFrame:
    '''
    The main purpose is to find the locational fixed effect, but
    will also get the fixed effects of some suffix of occupation

    Since we only care about the location fixed effect, choosing which occupation or year
    as the reference would not matter, since they don't affect the coefs of the locations. 
    '''
    cat_cols = ['year', 'portcode', 'rank_new'] + suffixes
    keep_cols = ['pay', 'tenure'] + cat_cols
    df = df[keep_cols]

    # step 1. filter the data to include only the given list of location
    #         if no location provided,include all of the locations
    if locations:
        df = df[df['portcode'].isin(locations)].reset_index(drop=True)

    # step 2. drop the rows with any of the category counts is less than the threshold
    for cur_cat in cat_cols:
        counts = df[cur_cat].value_counts()
        df = df[df[cur_cat].map(counts) >= THRESHOLD].reset_index(drop=True)

    # step 3. make year, location, occupation, and suffixes of occupations into dummy.
    # set the highest frequency or lowest paid occupation as the reference category
    top_freq_job = df['rank_new'].value_counts().idxmax()

    avg_wage = df.groupby('rank_new')['pay'].mean()
    cheapest_job = avg_wage.idxmin()

    cur_ref_job = cheapest_job
    # Reorder the 'rank_new' column so that the most frequent category is first
    df['rank_new'] = pd.Categorical(
        df['rank_new'],
        categories=[cur_ref_job] +
        [cat for cat in df['rank_new'].unique() if cat != cur_ref_job],
        ordered=True
    )

    for c in cat_cols:  # show the dropped category for each variable
        print(f"{c} reference cat: {pd.Categorical(df[c]).categories[0]}")

    # will add back to the output later: fixed effect = 0
    dropped_loc = pd.Categorical(df['portcode']).categories[0]

    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    # step 4. make X and y for OLS regression
    X = pd.concat(
        [
            df.filter(like='tenure'),
            df.filter(like='year_'),
            df.filter(like='portcode_'),
            df.filter(like='rank_new_'),
            df.filter(like='suffix_')
        ],
        axis=1
    )
    X = X.astype(float)
    X = sm.add_constant(X)
    y = df['pay']

    model = sm.OLS(y, X).fit()

    if display_fit_result:
        print(model.summary())

    # step 5. get the coefs as location fixed effect
    params = model.params  # basically a pd.Series, with the dummy names as the index
    params.rename('coef', inplace=True)  # for later locate this column
    portcode_params = params[params.index.str.contains(
        'portcode')].reset_index()
    portcode_params['portcode'] = portcode_params['index'].str.strip(
        "portcode_").astype(int)

    portcode_params = portcode_params[['portcode', 'coef']]
    portcode_params.loc[len(portcode_params)] = [dropped_loc, 0]

    return portcode_params


def map_display(gdf):
    # Plot the GeoDataFrame
    fig, ax = plt.subplots(figsize=(12, 8))
    gdf.plot(ax=ax, color='lightblue', edgecolor='black')

    # Customize the plot
    ax.set_title('Map Display')
    ax.set_axis_off()  # Hide the axis for better visual display

    # Show the plot
    plt.show()


def plot_loc(fixed_effects: pd.DataFrame):
    '''
    Not sure if we will plot other things on the map, but now only consider
    plotting fixed effect onto the map of China
    1. 老師希望所有的prefecture都可以畫上東西，所以我會把全部的location都弄，然後
       如果同個prefecture有重複的話就留比較高的。
    2. treaty port的prefecture可以特別標出來。
    '''
    # step 1. map the portcodes to name_ch and lon-lat
    code_to_name_ch = pd.read_excel(TOP_LOCATION_FILE)
    code_to_name_ch = code_to_name_ch[['portcode', 'name_ch', 'lon', 'lat']]

    fixed_effects = pd.merge(
        fixed_effects, code_to_name_ch, on='portcode', how='left'
    )

    geometry = [
        Point(xy) for xy in zip(fixed_effects['lon'], fixed_effects['lat'])]
    fixed_effects = gpd.GeoDataFrame(
        fixed_effects, geometry=geometry, crs=NORMAL_LON_LAT_CRS)

    # step 2. determine whether these ports are in the same prefecture,
    #         keep the highest fixed effect should there be any duplicate
    # 'SYS_ID', 'NAME_PY', 'NAME_CH', 'NAME_FT', 'PRES_LOC', 'TYPE_PY',
    # 'TYPE_CH', 'LEV_RANK', 'BEG_YR', 'BEG_RULE', 'END_YR', 'END_RULE',
    # 'DYN_PY', 'DYN_CH', 'LEV1_PY', 'LEV1_CH', 'NOTE_ID', 'OBJ_TYPE',
    # 'GEO_SRC', 'COMPILER', 'GEOCOMP', 'CHECKER', 'ENT_DATE', 'X_COORD',
    # 'Y_COORD', 'AREA', 'geometry'
    china_gdf = gpd.read_file(
        "replicate_fmm/Data/china/CHGis/v6_1820_pref_pgn_utf/",
        encoding='utf-8'
    )

    # 南沙群島: 萬里長沙, 千里石塘, None (should be 曾母暗沙), 東沙, None (should be 中沙)
    south_islands = ['2103', '2104', '2105', '2106', '2107']
    china_gdf = china_gdf[~china_gdf['SYS_ID'].isin(south_islands)]

    china_gdf = china_gdf[['SYS_ID', 'NAME_FT', 'geometry']]\
        .to_crs(NORMAL_LON_LAT_CRS)

    # get the prefetures where the points belong to
    fixed_effects = gpd.sjoin(
        fixed_effects, china_gdf, how='left', predicate='within')

    # keep the highest coef for the same SYS_ID
    fixed_effects = fixed_effects.loc[
        fixed_effects.groupby('SYS_ID')['coef'].idxmax()]\
        .reset_index(drop=True)

    # TODO: might want to get the dropped portcodes

    # step 3. might plot a heat map, so will need color bar
    to_plot_gdf = pd.merge(
        china_gdf, fixed_effects[['SYS_ID', 'coef']], on='SYS_ID', how='left')

    num_groups = 5
    to_plot_gdf['coef_group'] = pd.qcut(
        to_plot_gdf['coef'], num_groups, labels=False)

    # Plot the map, using 'coef_group' for coloring
    fig, ax = plt.subplots(figsize=(12, 8))
    to_plot_gdf.plot(
        column='coef_group', cmap='viridis', linewidth=0.4, ax=ax,
        edgecolor='gray', legend=True,
        missing_kwds={"color": "gainsboro", "label": "No data"}
    )

    # Customize the plot
    ax.set_title('Location Fixed Effects')
    ax.set_axis_off()

    # Show the plot
    plt.show()


def analysis(df: pd.DataFrame):
    # ============
    #  Preporcess
    # ============
    nan_to_zero = {
        'promote': 0,
        'begin': 0,
        'transfer': 0,
        'pay': 0
    }

    df.fillna(nan_to_zero, inplace=True)

    # Note that "promote" means the promotion year,
    # none year figures and NaN set to 0 for easier filter later
    # >> but actually figures smaller than 1800 might be the amount of prommotion,
    #    if we need a column indicating ever promoted, should use another way
    #    to preprocess data
    df.loc[df['promote'] < 1800, "promote"] = 0

    # "year" means the observation year, has 3 NaNs
    df.dropna(subset=['year'], inplace=True, ignore_index=True)
    df['year'] = df['year'].astype(int)

    # "begin" should be the year that worker started the job.
    # so figures smaller than 1800 are set to 0 for easier filter later
    df.loc[df['begin'] < 1800, "begin"] = 0
    df['begin'] = df['begin'].astype(int)

    # "transfer" should mean the year of transferring to that recorded job
    # not sure how this column will be used, simply changed the NaNs to 0
    # for easier filter later

    # "pay" is the wage, originally wants to igonre all the NaNs,
    # but there are too many of them (15222), so I keep them for now
    # NaN set to 0 for easier filter later

    # make tenure: use 'year' - 'begin', no 'begin' then 0
    df['tenure'] = df['year'] - df['begin']
    df.loc[df['begin'] == 0, 'tenure'] = 0

    # ==========
    #  Analysis
    # ==========
    # filters for analysis
    cond_c0 = df['certainty_lvl'] == 0  # 2274; 1: 859
    cond_c2 = df['certainty_lvl'] == 2  # 6445
    cond_c3 = df['certainty_lvl'] == 3  # 61351
    # > 1000 cases: 22, one in shashi 1116, other in hankow
    cond_normalpay = df['pay'] < 1000
    cond_positivepay = df['pay'] > 0

    # can apply other conds with '&' or '|'
    conds = (cond_c3 | cond_c2) & cond_normalpay & cond_positivepay

    # apply conditions
    df = df.loc[conds]

    # TOP N ports
    top_n = 20

    port_freq = Counter(df['portcode'])
    top_ports = [p for p, _ in port_freq.most_common(top_n)]

    # ---------------------------------------
    #  scatter plot of wage and observe year
    # ---------------------------------------
    # TODO:  report the total count and Na counts.
    # for cur_port in top_ports:
    #     plot_year_wage_scatter(df, cur_port)

    # --------------------
    #  wage index by area
    # --------------------
    # variables = ['pay', 'rank_new', 'tenure', 'portcode', 'year']

    # # Shanghai = 195; Soochow = 435
    # for loc in [195, 435, top_ports]:
    #     if isinstance(loc, list):
    #         df_fil = df[df['portcode'].isin(top_ports)]
    #     else:
    #         df_fil = df[df['portcode'] == loc]

    #     rank_freq = Counter(df_fil['rank_new'])
    #     top_rank = rank_freq.most_common(top_n)

    #     df_fil = df_fil[df_fil['rank_new'].isin([r for r, _ in top_rank])]

    #     index_srs = wage_index(loc, df_fil[variables])

    #     print(index_srs)

    # -----------------------
    #  location fixed effect
    # -----------------------
    suffix_cols = [c for c in df.columns if 'suffix' in c]
    fx_eff = location_fixed_effect(df=df, suffixes=suffix_cols)

    plot_loc(fx_eff)

    return


def main():
    df = pd.read_excel(MAIN_FILE_PATH, sheet_name="data")

    cols_to_keep = [
        "year", "rank", "begin", "promote", "transfer", "pay", "areacode",
        "portcode", "certainty_lvl", "port", "possible_names", "rank_new",
        "suffix_1", "suffix_2", "suffix_3", "suffix_4"
    ]

    # TODO: write as class, and put these two section into __init__
    out_dir = "./output/"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    graph_dir = "./graphs/"
    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)

    analysis(df)


if __name__ == "__main__":
    main()
