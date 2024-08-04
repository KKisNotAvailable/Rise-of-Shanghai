import pandas as pd
import os
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt

# check out https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

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

    # "promote" means the promotion year, 
    # none year figures and NaN set to 0 for easier filter later
    df.loc[df['promote'] < 1800, "promote"] = 0

    # "year" means the observation year, has 3 NaNs
    df.dropna(subset=['year'], inplace=True, ignore_index=True)

    # "begin" should be the year that worker started the job.
    # so figures smaller than 1800 are set to 0 for easier filter later
    df.loc[df['begin'] < 1800, "begin"] = 0
    df.loc[:, 'begin'] = df['begin'].astype(int)

    # "transfer" should mean the year of transferring to that recorded job
    # not sure how this column will be used, simply changed the NaNs to 0
    # for easier filter later

    # "pay" is the wage, originally wants to igonre all the NaNs,
    # but there are too many of them (15222), so I keep them for now
    # NaN set to 0 for easier filter later

    # --------
    # Analysis
    # --------
    # filters for analysis
    cond_c0 = df['certainty_lvl'] == 0 # 2274; 1: 859
    cond_c2 = df['certainty_lvl'] == 2 # 6445
    cond_c3 = df['certainty_lvl'] == 3 # 61351
    cond_highpay = df['pay'] > 1000 # 22, one in shashi 1116, other in hankow

    # portcode freq
    conds = cond_c3 | cond_c2 # can apply other conds with '&' or '|'
    port_freq = Counter(df.loc[conds, 'portcode'])
    top_ports = port_freq.most_common(10)

    print(top_ports)

    # for scatter plot, ignore NaNs. 
    # But need to report the total count and Na counts.
    for cur_port, _ in top_ports:
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

        plt.savefig(f"graphs/{ttl}.jpg")
        plt.close() 

    return

def main():
    df = pd.read_excel("data/data_port_processed.xlsm", sheet_name="Sheet1")

    cols_to_keep = [
        "year", "rank", "begin", "promote", "transfer", "pay", "areacode", 
        "portcode", "certainty_lvl", "port", "possible_names"
    ]

    out_dir = "./output/"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # analysis(df[cols_to_keep])

if __name__ == "__main__":
    main()