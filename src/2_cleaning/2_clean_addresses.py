from functions_cleaner import clean_dataset

import pandas as pd
import re

generate_adresse_complete = True  # Ideally, remains True to get the complete addresses
# Can be set to False if we are short on time and do not need a unique field with the address

address_types = ["r", "c"]

print("### Loading datasets...")
df = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/adressesREU_brutes2.parquet"
)
df["id_brut_bv"] = df["code_commune_ref"].fillna("") + "_" + df["code_bv"].fillna("")
print("### Dataset Loaded!")
print(len(df), "rows")

list_chars = [".", ",", ";", ":", "#", "°", "*", '"', "  "]  # Undesirable punctuation


# Small cleaning on the "commune" and "pays" fields
def clean_place_name(x):
    """
    Removes what is between parenthesis or brackets, lowers the string and removes undesirable punctuation
    """
    x_clean = re.sub("[\(\[].*?[\)\]]", "", x)
    x_clean = "".join([i for i in x_clean if not i.isdigit()])
    for character in list_chars:
        x_clean = x_clean.replace(character, " ")
    return x_clean.strip()


for adresse in address_types:
    df[[adresse + "_" + field + "_clean" for field in ["commune", "pays"]]] = (
        df[[adresse + "_" + field for field in ["commune", "pays"]]]
        .apply(lambda x: x.astype(str).str.lower())
        .applymap(clean_place_name)
    )

# Big cleaning on the rest
df = clean_dataset(df, generate_adresse_complete)
df.sort_values(by="identifiant_ligne", inplace=True)

print("### Dataset Cleaned!")

df.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/cleaned_addresses_large_detailed.parquet",
    index=False,
)

# Keep only the columns that may be re-used later
df_narrow = df[
    ["identifiant_ligne"]
    + [
        address_type + field
        for field in [
            "adresse_originale",
            "adresse_complete",
            "adresse_tres_complete",
            "num_voie_clean",
            "voie_clean",
            "all_complements_clean",
            "lieu_dit_clean",
            "cp_clean",
            "commune_clean",
            "departement",
            "pays_clean",
            "flag_aggregation",
        ]
        for address_type in address_types
    ]
    + [
        "was_anonymized",
        "was_cleaned",
        "code_commune_ref",
        "reconstitution_code_commune",
        "commune_identique",
        "id_brut_bv",
    ]
]

df_narrow.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/cleaned_addresses_large.parquet",
    index=False,
)

# Keep aside the observations that were considered as suspicious in the first place
# To check if our treatment was efficient and exhaustive
df_suspicious = df[df["flag_anonymization"] + df["flag_cleaning"] > 0][
    ["identifiant_ligne"]
    + [
        address_type + field
        for field in [
            "adresse_originale",
            "adresse_complete",
            "flag_aggregation",
            "cp_clean",
            "commune_clean",
            "departement",
            "adresse_pre_treated",
        ]
        for address_type in address_types
    ]
    + [
        "flag_anonymization",
        "was_anonymized",
        "flag_cleaning",
        "was_cleaned",
        "reconstitution_code_commune",
        "commune_identique",
        "id_brut_bv",
        "code_commune_ref",
    ]
]

df_suspicious.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses.parquet",
    index=False,
)
df_suspicious.to_csv(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses.csv",
    index=False,
)
