import numpy as np
import os
import pandas as pd

rawdatapath_reu = "X:/HAB-Adresses-REU/rawdata/Adresses_REU_brutes/"
datapath_init = "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/"

# Faire la liste des CSV à importer
csv_files = list(filter(lambda f: f.endswith(".csv"), os.listdir(rawdatapath_reu)))

# Importer tous les CSV
list_df = [
    pd.read_csv(rawdatapath_reu + file, on_bad_lines="skip", header=0, dtype=str, sep=",")
    for file in csv_files
]

# Enlever les lignes qui comportent plus de 24 colonnes (car il y a des virgules dans les adresses...)
# Enlever les colonnes surnuméraires
# Certains fichiers ont bien 24 colonnes (pas de retraitement), d'autres en ont plus
list_df2 = [df for df in list_df if df.shape[1] == 24] + [
    df.loc[df.iloc[:, 24].isna(),].iloc[:, 0:24] for df in list_df if df.shape[1] > 24
]

# Harmoniser les noms de colonnes
for i in range(len(list_df)):
    list_df2[i].columns = [
        "r_num_voie",
        "r_voie",
        "r_complément1",
        "r_complément2",
        "r_lieu_dit",
        "r_cp",
        "r_commune",
        "r_pays",
        "c_num_voie",
        "c_voie",
        "c_complément1",
        "c_complément2",
        "c_lieu_dit",
        "c_cp",
        "c_commune",
        "c_pays",
        "code_bv",
        "libelle_bv",
        "num_voie_bv",
        "voie_bv",
        "cp_bv",
        "commune_bv",
        "code_commune_ref",
        "libelle_commune_ref",
    ]
    # Créer un identifiant de ligne non signifiant
    list_df2[i]["identifiant_ligne"] = [
        "{:03d}".format(i) + "_" + str(position)
        for position in np.arange(len(list_df2[i]))
    ]


# Concaténer les CSV
df = pd.concat(list_df2).reset_index()

# # Créer un identifiant de ligne non signifiant
# df["identifiant_ligne"] = np.arange(len(df))

# Ordonner les colonnes
df = df[
    ["identifiant_ligne"]
    + [
        "r_num_voie",
        "r_voie",
        "r_complément1",
        "r_complément2",
        "r_lieu_dit",
        "r_cp",
        "r_commune",
        "r_pays",
        "c_num_voie",
        "c_voie",
        "c_complément1",
        "c_complément2",
        "c_lieu_dit",
        "c_cp",
        "c_commune",
        "c_pays",
        "code_bv",
        "libelle_bv",
        "num_voie_bv",
        "voie_bv",
        "cp_bv",
        "commune_bv",
        "code_commune_ref",
        "libelle_commune_ref",
    ]
]

# Sauvegarder la table complète en parquet
df.to_parquet(datapath_init + "adressesREU_brutes.parquet", compression="gzip")


BANdatapath = "X:/HAB-Adresses-REU/rawdata/Adresses_BAN/Adresses_csv"

# # Faire la liste des CSV à importer
# csv_files_BAN = []
# for dirpath, dirnames, filenames in os.walk(BANdatapath):
#     for file in filenames:
#         csv_files_BAN += [os.path.join(os.path.relpath(dirpath, BANdatapath), file)]
#
# csv_files_BAN_adresses = list(filter(lambda f: f.startswith('adresses'), csv_files_BAN))
#
# # Importer tous les csv
# list_df_BAN_adresses = []
# for file in csv_files_BAN_adresses:
#     print(file)
#     list_df_BAN_adresses += [pd.read_csv(BANdatapath + file, on_bad_lines = 'skip', header=0, dtype=str, sep = ";")]

# Importer les adresses
df_BAN_adresses = pd.read_csv(
    BANdatapath + "adresses-france.csv/adresses-france.csv",
    on_bad_lines="skip",
    header=0,
    dtype=str,
    sep=";",
)

# Sauvegarder la table complète en parquet
df_BAN_adresses.to_parquet(datapath_init + "adressesBAN_brutes.parquet", compression="gzip")


# Faire la liste des CSV à importer
csv_files_BAN_lieuxdits = []
for dirpath, dirnames, filenames in os.walk(BANdatapath):
    for file in filenames:
        csv_files_BAN_lieuxdits += [
            os.path.join(os.path.relpath(dirpath, BANdatapath), file)
        ]

csv_files_BAN_lieuxdits = list(
    filter(lambda f: f.startswith("lieux"), csv_files_BAN_lieuxdits)
)

# Importer tous les csv
list_df_BAN_lieuxdits = []
for file in csv_files_BAN_lieuxdits:
    print(file)
    try:
        list_df_BAN_lieuxdits += [
            pd.read_csv(
                BANdatapath + file, on_bad_lines="skip", header=0, dtype=str, sep=";"
            )
        ]
    except:
        pass

df_BAN_lieuxdits = pd.concat(list_df_BAN_lieuxdits)

# Sauvegarder la table des lieux-dits en parquet
df_BAN_lieuxdits.to_parquet(
    datapath_init + "lieuxditsBAN_brutes.parquet", compression="gzip"
)
