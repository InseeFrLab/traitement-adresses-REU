import pandas as pd
from unidecode import unidecode

df = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/cleaned_addresses_large.parquet"
)
# Remove columns containing personal information
df.drop(["r_adresse_originale", "c_adresse_originale"], axis=1, inplace=True)
print("### Dataset Loaded!")
print(len(df), "rows")

# Pivot the data to put "adresses de contact" and "adresses de rattachement" on the same level
# Faster than R pivoting: manual pivoting
# Needs to ne adapted in case the address types change

# EDIT: Since january 2023 modifications, no more geolocalisation for 'adresses de contact'

liste_r_cols = [col for col in df.columns if col[:2] != "c_"]
df_r = df[liste_r_cols]
df_r["address_type"] = "r"

# df_c = df[liste_c_cols]
# liste_c_cols = [col for col in df.columns if col[:2] != 'r_']
# df_c['address_type'] = 'c'

for col in df.columns:
    if col[:2] == "r_":
        df_r.rename({col: col[2:]}, axis=1, inplace=True)
    # if col[:2] == "c_":
    #     df_c.rename({col: col[2:]}, axis=1, inplace=True)

# df = pd.concat([df_r, df_c])
df = df_r.copy()

print("### Pivot finished")

# Add dummies
df["is_rattachement"] = df["address_type"] == "r"
df["is_contact"] = df["address_type"] == "c"

# Group addresses by exact match - Priority to:
# - Les adresses de rattachement (where is_contact == 0)
# - The addresses without aggregation suspicion (flag_aggregation == 0)

# Since january 2023 modifications, no more geolocalisation for 'adresses de contact'
df = df[df["is_rattachement"]]

df.sort_values(by=["is_contact", "flag_aggregation", "identifiant_ligne"], inplace=True)
# Groupement à améliorer / modifier ?
df["adresse_tres_complete_no_punct"] = df["adresse_tres_complete"].apply(
    lambda x: unidecode(x.replace("-", " "))
)
df_grouped = df.groupby(
    by=["adresse_tres_complete_no_punct", "code_commune_ref", "id_brut_bv"], sort=False
)

# We get one id for each group of same addresses
df["identifiant_groupe"] = df_grouped.ngroup()

# We find one representant for each group
df_grouped = df_grouped.head(1)[
    ["identifiant_ligne", "address_type", "identifiant_groupe"]
]
print("### Groups and representatives found")
print(len(df_grouped), "représentants")

# We merge everything
df_grouped.rename(
    columns={"identifiant_ligne": "id_ligne_group", "address_type": "type_group"},
    inplace=True,
)
df = df.merge(df_grouped, on="identifiant_groupe", how="left")
df["representant_groupe"] = (df["id_ligne_group"] == df["identifiant_ligne"]) & (
    df["type_group"] == df["address_type"]
)
df.drop(["id_ligne_group", "type_group"], axis=1, inplace=True)
df.sort_values(
    by=["identifiant_groupe", "representant_groupe", "identifiant_ligne"], inplace=True
)
print("### Jointure finished")

# Déterminer si un groupe comprend une adresse de rattachement
summary_r = df.groupby("identifiant_groupe")["is_rattachement"].max().reset_index()
summary_c = df.groupby("identifiant_groupe")["is_contact"].max().reset_index()

# Transformer cette info en dictionnaire
dict_values_r = dict(zip(summary_r["identifiant_groupe"], summary_r["is_rattachement"]))
dict_values_c = dict(zip(summary_c["identifiant_groupe"], summary_c["is_contact"]))

# Remettre cette info dans la table initiale
df.loc[:, "contains_rattachement"] = df["identifiant_groupe"].map(dict_values_r)
df.loc[:, "contains_contact"] = df["identifiant_groupe"].map(dict_values_c)

# Re-order the columns in the most practical way to use the different APIs
df = df[
    [
        "identifiant_ligne",
        "address_type",  # Uniquement pour ne pas décaler colonnes --> dummy column
        "identifiant_groupe",
        "representant_groupe",
        "num_voie_clean",
        "voie_clean",
        "all_complements_clean",
        "lieu_dit_clean",
        "cp_clean",
        "contains_rattachement",  # Uniquement pour ne pas décaler colonnes --> dummy column
        "commune_clean",
        "code_commune_ref",
        "departement",
        "pays_clean",
        "adresse_complete",
        "adresse_tres_complete",
        "was_anonymized",
        "was_cleaned",
        "flag_aggregation",
        "reconstitution_code_commune",
        "commune_identique",
        "id_brut_bv",
    ]
]

# Save the table linking the id of the groups and those of the individuals

df_correspondance = df[
    [
        "identifiant_ligne",
        "address_type",  # A terme, à retirer --> on ne garde que les adresses de rattachement
        "identifiant_groupe",
        "representant_groupe",
        "id_brut_bv",
    ]
]

df_correspondance.rename(columns={"identifiant_groupe": "id_adresse"}, inplace=True)

df_correspondance.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/table_correspondance_id_groups.parquet",
    index=False,
)
df_correspondance.to_csv(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/table_correspondance_id_groups.csv",
    index=False,
)

# Save the full table with the pivoted addresses and our new columns
df.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/cleaned_addresses_long.parquet",
    index=False,
)
df.head(1000).to_csv(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/extract_cleaned_addresses_long.csv",
    index=False,
)

df_representants = df[df["representant_groupe"]]
# A terme, retirer aussi identifiant_ligne et address_type dans df_representants
df_representants.drop(["representant_groupe"], axis=1, inplace=True)
df_representants.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/deduplicated_cleaned_addresses_long.parquet",
    index=False,
)
df_representants.head(1000).to_csv(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/extract_deduplicated_cleaned_addresses_long.csv",
    index=False,
)
