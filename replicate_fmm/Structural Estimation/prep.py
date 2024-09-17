import pandas as pd


def coord_to_maps_pair(df):
    df['pair'] = None


def main():
    df = pd.read_stata("./replicate_fmm/Data/raw/district_geoloc.dta")

    # 'state', 'district', 'latitude_google', 'longitude_google'
    df['coords'] = list(zip(df['latitude_google'], df['longitude_google']))

    df = df[['coords', 'state', 'district']]

    df.to_csv("replicate_fmm/Structural Estimation/check_coord.csv", index=False)


if __name__ == "__main__":
    # replicate_fmm\Structural Estimation\prep.py
    main()
