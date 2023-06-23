import sys
import pandas as pd

sys.path.insert(1, "/2_cleaning")
from functions_cleaner import requires_anonymization, requires_cleaning

BANdatapath = "X:/HAB-Adresses-REU/rawdata/Adresses_BAN/Adresses_csv"

# Same suspicious entries detection as in functions_cleaner.py

liste_variantes_chez = [
    "hébergée",
    "héberge",
    "hebergee",
    "heberge",
    "chez",
    "sous couvert",
    "au bon soin",
    "ches",
    "che",
    "cz",
    "c 0",
    "c0",
    "c o",
    "co",
    "c",
]
# These ones are considered as "chez" only if they are the first word of the string
liste_variantes_chez_au_debut = [
    "chef",
    "cher",
    "boîte",
    "boite",
    "bàl",
    "bal",
    "monsieur",
    "madame",
    "mademoiselle",
    "mr",
    "mme",
    "mlle",
    "melle",
    "me",
    "m",
]
# Format these lists into the format required for the different tests
liste_all_variantes_chez = liste_variantes_chez + liste_variantes_chez_au_debut
str_variantes_chez = "|".join(
    [space + chez + " " for chez in liste_variantes_chez for space in [" ", "-"]]
)
str_all_variantes_chez = "|".join(
    [space + chez + " " for chez in liste_all_variantes_chez for space in [" ", "-"]]
)
tuple_all_variantes_chez = tuple([chez + " " for chez in liste_all_variantes_chez])

# List all the other words that might be the sign of the presence of nominative data
liste_denominations = [
    "monsieur",
    "madame",
    "mademoiselle",
    "mr",
    "mme",
    "mlle",
    "melle",
    "me",
    "m",
]
liste_prepositions = [
    "derrière",
    "derriere",
    "devant",
    "entre",
    "dans",
    "contre",
    "côté",
    "cote",
    "gauche",
    "droite",
    "loin",
    "par",
]
str_all_patterns = "|".join(
    [
        space + chez + " "
        for chez in liste_denominations + liste_prepositions
        for space in [" ", "-"]
    ]
)

# List all of the words that as been observed as extra descriptions of apartments (room number, stairs, ...)
# We will want to remove this information from the "general" address
liste_specifications = [
    "appartement",
    "apartement",
    "appartment",
    "apartment",
    "appart",
    "appt",
    "apt",
    "app",
    "apprt",
    "aprt",
    "artement",
    "bâtiment",
    "batiment",
    "bât",
    "bat",
    "bt",
    "lgt",
    "log",
    "logement",
    "logt",
    "numéro",
    "numero",
    "num",
    "n0",
    "n",
    # "ème", "eme", "er", "ième",  # Too often used in street names to be removed
    "étage",
    "etage",
    "etg",
    "étag",
    "etag",
    "rez-de-chaussée",
    "rez-de-chaussee",
    "rez de chaussée",
    "rez de chaussée",
    "rdc",
    "esc",
    "couloir",
    "pte",  # Words like "porte" are too often used in street names to be removed
    "entrée",
    "entree",
    "ent",
    "boîte aux lettres",
    "boite aux lettres",
    "bàl",
    "bal",
    "boîte",
    "boite",
]
str_specifications = "|".join(
    [space + chez + " " for chez in liste_specifications for space in [" ", "-"]]
)


df_adresses = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/adressesBAN_brutes.parquet"
)
df_lieux_dits = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/lieuxditsBAN_brutes.parquet"
)

# Concatenate into a single table

df_adresses.rename(columns={"nom_voie": "nom_BAN"}, inplace=True)
df_adresses_narrow = df_adresses[["nom_BAN", "code_postal", "nom_commune"]]

df_lieux_dits.rename(columns={"nom_lieu_dit": "nom_BAN"}, inplace=True)
df_lieux_dits_narrow = df_lieux_dits[["nom_BAN", "code_postal", "nom_commune"]]

df_BAN = pd.concat([df_adresses_narrow, df_lieux_dits_narrow])

print("### Dataset ready - Beginning of treatment")

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


# Now filter the rows
df_BAN["nom_BAN"] = df_BAN["nom_BAN"].str.lower()
df_BAN["nom_BAN"] = df_BAN["nom_BAN"].apply(lambda x: remove_punctuation(str(x)))
df_BAN.drop_duplicates(inplace=True)
df_BAN["flag_anonymization"] = df_BAN["nom_BAN"].apply(
    requires_anonymization,
    str_variantes_chez=str_variantes_chez,
    tuple_all_variantes_chez=tuple_all_variantes_chez,
    str_all_patterns=str_all_patterns,
)
df_BAN["flag_cleaning"] = df_BAN["nom_BAN"].apply(
    requires_cleaning, str_specifications=str_specifications
)
df_BAN = df_BAN[df_BAN["flag_anonymization"] + df_BAN["flag_cleaning"] > 0]

print("### Treatment completed")
df_BAN.sort_values(by="code_postal", inplace=True)

# And export

df_BAN.to_parquet(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses_BAN.parquet",
    index=False,
)
df_BAN.to_csv(
    "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/suspicious_addresses_analysis/suspicious_addresses_BAN.csv",
    index=False,
)
