import pandas as pd
from tqdm import tqdm
import sys

sys.path.insert(1, "/2_cleaning")
from functions_cleaner import complete_postal_code

datapath = "X:/HAB-Adresses-REU/data/"

df_suspicious_BAN = pd.read_parquet(
    datapath + "2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses_BAN.parquet"
)
df_suspicious_BAN = df_suspicious_BAN[
    (df_suspicious_BAN.flag_anonymization == 2) | (df_suspicious_BAN.flag_cleaning == 1)
].sort_values(by="code_postal")
print("### Dataset BAN Loaded!")
print(len(df_suspicious_BAN), "rows")

df_adresses = pd.read_parquet(
    datapath + "2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses.parquet"
)
df_adresses = df_adresses[
    df_adresses.was_anonymized | df_adresses.was_cleaned
].drop_duplicates(subset=["r_adresse_pre_treated"])
print("### Dataset adresses Loaded!")
print(len(df_adresses), "rows")

list_chars = [
    "(",
    ")",
    "[",
    "]",
    ".",
    ",",
    ";",
    ":",
    "/",
    "#",
    "°",
    "*",
    '"',
    "  ",
]  # Undesirable punctuation


def remove_punctuation(x: str) -> str:
    # Remove all unuseful punctuation

    clean_x = str(x)
    for character in list_chars:
        clean_x = clean_x.replace(character, " ")
    clean_x = clean_x.replace("&", " et ").replace("  ", " ").lower()
    return clean_x.strip()


df_suspicious_BAN["in_adresses_brutes"] = 0
df_suspicious_BAN["match_adresse_brute"] = ""
df_suspicious_BAN["in_adresses_clean"] = 0
df_suspicious_BAN["match_adresse_clean"] = ""
df_suspicious_BAN["code_postal"] = (
    df_suspicious_BAN["code_postal"]
    .apply(remove_punctuation)
    .apply(complete_postal_code)
)

df_adresses["r_cp_clean"] = (
    df_adresses["r_cp_clean"].apply(remove_punctuation).apply(complete_postal_code)
)
set_postal_codes = set(df_adresses["r_cp_clean"])

print("### Datasets ready - Beginning of comparison")

for postal_code in tqdm(set_postal_codes):
    df_adresses_in_cp = df_adresses[df_adresses["r_cp_clean"] == postal_code]
    for index, row in df_suspicious_BAN.iterrows():
        if row["code_postal"] > postal_code:
            break
        if row["code_postal"] == postal_code:
            for index_adresse, row_adresse in df_adresses_in_cp.iterrows():
                if row["nom_BAN"] in row_adresse["r_adresse_pre_treated"]:
                    df_suspicious_BAN["in_adresses_brutes"][index] = 1
                    df_suspicious_BAN["match_adresse_brute"][index] = row_adresse[
                        "r_adresse_pre_treated"
                    ]
                    if row["nom_BAN"] in row_adresse["r_adresse_complete"]:
                        df_suspicious_BAN["in_adresses_clean"][index] = 1
                    df_suspicious_BAN["match_adresse_clean"][index] = row_adresse[
                        "r_adresse_complete"
                    ]
                    break

print("### Comparison completed")

df_suspicious_BAN.to_parquet(
    datapath + "2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/comparison_suspicious_addresses.parquet",
    index=False,
)
df_suspicious_BAN.to_csv(
    datapath + "2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/comparison_suspicious_addresses.csv",
    index=False,
)
