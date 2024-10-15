import pandas as pd
import os
import numpy as np
from collections import Counter
import statsmodels.api as sm
import matplotlib.pyplot as plt

# write the code in the style align with the upcoming pandas update
# check out https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

def plot_year_wage_scatter(df: pd.DataFrame, cur_port: int, graph_dir: str = "graphs", save_fig=False):
    '''
    This function plots the distribution of wage based on the observation year.
    '''
    df_to_plot = df.loc[df['portcode'] == cur_port, ['year', 'pay']].reset_index(drop=True)

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

    min_year = min(data['year']) # for dropping the first year-col as base year

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

def hedonic_reg(df, find_fix_cols):
    '''
    The main purpose is to find the locational fixed effect, but
    will also get the fixed effects of some suffix of occupation
    '''

def analysis(df: pd.DataFrame):
    # ----------
    # Preporcess
    # ----------
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


    # --------
    # Analysis
    # --------
    # filters for analysis
    cond_c0 = df['certainty_lvl'] == 0 # 2274; 1: 859
    cond_c2 = df['certainty_lvl'] == 2 # 6445
    cond_c3 = df['certainty_lvl'] == 3 # 61351
    cond_normalpay = df['pay'] < 1000 # > 1000 cases: 22, one in shashi 1116, other in hankow

    # can apply other conds with '&' or '|'
    conds = (cond_c3 | cond_c2) & cond_normalpay

    # apply conditions
    df = df.loc[conds]

    # TOP N ports
    top_n = 10

    port_freq = Counter(df['portcode'])
    top_ports = port_freq.most_common(top_n)

    # =======================================
    #  scatter plot of wage and observe year
    # =======================================
    # TODO:  report the total count and Na counts.
    # for cur_port, _ in top_ports:
    #     plot_year_wage_scatter(df, cur_port)

    # ====================
    #  wage index by area
    # ====================
    # variables = ['pay', 'rank_new', 'tenure', 'portcode', 'year']
    # ports = [p for p, _ in top_ports]
    
    # # Shanghai = 195; Soochow = 435
    # for loc in [195, 435, ports]:
    #     if isinstance(loc, list):
    #         df_fil = df[df['portcode'].isin(ports)]
    #     else:
    #         df_fil = df[df['portcode'] == loc]

    #     rank_freq = Counter(df_fil['rank_new'])
    #     top_rank = rank_freq.most_common(top_n)

    #     df_fil = df_fil[df_fil['rank_new'].isin([r for r, _ in top_rank])]

    #     index_srs = wage_index(loc, df_fil[variables])

    #     print(index_srs)

    # =======================
    #  location fixed effect
    # =======================


    return


def main():
    df = pd.read_excel("data/data_port_processed.xlsm", sheet_name="data")

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

    analysis(df[cols_to_keep])


if __name__ == "__main__":
    main()