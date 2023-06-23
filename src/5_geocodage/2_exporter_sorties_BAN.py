# Import packages

import pandas as pd

# Import BAN results

df_list = [
    pd.read_csv(f"/home/onyxia/work/geo-extract_addresses_{i:03d}.csv", dtype=str)
    for i in range(195)
]

# Concatenate BAN results

df = pd.concat(df_list)
print(len(df))
# 07/02/2023 : 19 384 090

# Possible correction

if "identifiant_ligne" in df.columns:
    df.rename(columns={"identifiant_ligne": "id_adresse"}, inplace=True)
if "code_commune" in df.columns:
    df.rename(columns={"code_commune": "code_commune_ref"}, inplace=True)
if "index_brut_bv" in df.columns:
    df.rename(columns={"index_brut_bv": "id_brut_bv"}, inplace=True)

# Filter entries with a match in the BAN database

df_adresses = df[df["geo_adresse"].notnull()]
df_adresses = df_adresses[df_adresses["geo_adresse"] != ""]
print(len(df_adresses))
# 07/02/2023 : 19 370 409
# 0.07% d'adresses perdues

# Select columns

df_adresses = df_adresses[
    [
        "id_adresse",
        "geo_adresse",
        "code_commune_ref",
        "reconstitution_code_commune",
        "commune_identique",
        "id",
        "api_line",
        "geo_type",
        "geo_score",
        "longitude",
        "latitude",
        "id_brut_bv",
    ]
]

df_adresses[["geo_score", "longitude", "latitude"]] = df_adresses[
    ["geo_score", "longitude", "latitude"]
].apply(lambda x: x.astype(float))

# Export results

# df_adresses.to_csv('sorties_BAN.csv', index=False)
df_adresses.to_parquet("sorties_BAN.parquet", index=False)

# mc cp sorties_BAN.parquet s3/projet-adresses-reu/data/sorties_BAN_20230207.parquet
