import pandas as pd
from math import ceil

datapath = "X:/HAB-Adresses-REU/data/"

df = pd.read_parquet(
    datapath + "2_Nettoyage_manuel_adresses/deduplicated_cleaned_addresses_long.parquet"
)
print(len(df))
df = df[df["commune_identique"] == "1"]  # On se restreint aux communes de rattachement
print(len(df))

proportion_sample = (
    1  # Choose the proportion of data you want to sample (1, 1/100, ...)
)

# Choose if you want to determine batch_size or n_batchs

batch_size = 10**5
n_batchs = ceil(len(df) / batch_size)

for i in range(n_batchs):
    # We define a cut of the table
    tranche_df = df[
        (i * batch_size <= df["identifiant_groupe"])
        & (df["identifiant_groupe"] < (i + 1) * batch_size)
    ]
    if len(tranche_df) == 0:
        break
    # The samples are taken proportionally to the prevalence of the departments
    dep_weights = tranche_df.groupby("departement")["departement"].transform("count")
    sample = tranche_df.sample(
        n=int(len(tranche_df) * proportion_sample), weights=dep_weights, random_state=1
    )
    # sample['identifiant_ligne'] = sample['identifiant_ligne'].astype(str) + "_" + sample['address_type']
    sample.to_csv(
        # Warning: create the folder extracts_{int(100 * proportion_sample)}% if not existing already
        f'{datapath}2_Nettoyage_manuel_adresses/slices_{int(100 * proportion_sample)}%_deduplicated_cleaned_addresses_long/extract_addresses_{"{:03d}".format(i)}.csv',
        index=False,
    )
    print(f"### Sampling {i} finished")
