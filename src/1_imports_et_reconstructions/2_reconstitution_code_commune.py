import numpy as np
import os
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import re

# Quelques réglages pour l'affichage des dataframes dans la console
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 200)


rawdatapath = "X:/HAB-Adresses-REU/rawdata/Adresses_REU_brutes/"
datapath = "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/"

#########################################################
# Charger les données
#########################################################

print("Charger les données")
# Charger les données et le COG
COG2022 = pl.read_csv(
    "X:/HAB-Adresses-REU/rawdata/" + "commune_2022.csv", infer_schema_length=20000
)
historique_communes = pl.read_csv(
    "X:/HAB-Adresses-REU/rawdata/" + "communes1943_2022.csv", infer_schema_length=20000
)
historique_communes.filter(pl.col("NCC") == "TRONCHOY")
df = pl.from_arrow(pq.read_table(datapath + "adressesREU_brutes.parquet"))

#########################################################
# Préparer les adresses
#########################################################

print("Préparer les adresses")
df = df.with_columns(
    [
    pl.when(pl.col("code_commune_ref").str.lengths() <= 4).then("0" + pl.col("code_commune_ref")).otherwise(
        pl.col("code_commune_ref")).alias("code_commune_ref"),
        pl.when(pl.col("r_cp").str.lengths() <= 4).then("0" + pl.col("r_cp")).otherwise(
            pl.col("r_cp")).alias("r_cp"),
        pl.when(pl.col("c_cp").str.lengths() <= 4).then("0" + pl.col("c_cp")).otherwise(
            pl.col("c_cp")).alias("c_cp")
    ]
).with_columns(
    [
        pl.when(pl.col("code_commune_ref").str.slice(0, 2) == "97").then(pl.col("code_commune_ref").str.slice(0, 3)).otherwise(pl.col("code_commune_ref").str.slice(0, 2)).alias("dep_ref"),
        pl.when(pl.col("r_cp").str.slice(0, 2) == "97").then(
            pl.col("r_cp").str.slice(0, 3)).otherwise(pl.col("r_cp").str.slice(0, 2)).alias(
            "r_dep"),
        pl.when(pl.col("c_cp").str.slice(0, 2) == "97").then(
            pl.col("c_cp").str.slice(0, 3)).otherwise(pl.col("c_cp").str.slice(0, 2)).alias(
            "c_dep")
    ]
)

#########################################################
# Conserver uniquement les informations sur les libellés de commune
#########################################################

print("Conserver uniquement les informations sur les libellés de commune")
var_groupe = [
    "code_bv",
    "code_commune_ref",
    "dep_ref",
    "commune_bv",
    "r_commune",
    "r_cp",
    "c_commune",
    "r_dep",
]

# Résumer les données par var_groupe
df1 = df.groupby(pl.col(var_groupe)).agg(
    pl.col(["code_commune_ref"]).count().alias("nb_lignes")
).with_columns(
    [
        pl.when(pl.col("r_commune").str.contains("Marseille ")).then("Marseille").otherwise(
            pl.when(pl.col("r_commune").str.contains("Lyon ")).then("Lyon").otherwise(
                pl.when(pl.col("r_commune").str.contains("Paris ")).then("Paris").otherwise(pl.col("r_commune"))
            )
        ).alias("r_commune2")
    ]
)

print("Ajouter les noms de commune du COG")
df1 = df1.join(
    COG2022.select(pl.col(["DEP", "COM", "NCC", "NCCENR", "LIBELLE"])).with_columns(pl.lit(1).alias("dans_cog2022")).with_columns(
        pl.when(pl.col("NCC").str.contains("MARSEILLE ")).then("MARSEILLE").otherwise(
        pl.when(pl.col("NCC").str.contains("LYON ")).then("LYON").otherwise(
        pl.when(pl.col("NCC").str.contains("PARIS ")).then("PARIS").otherwise(pl.col("NCC"))
        )
    ).alias("NCC")),
    left_on  = "code_commune_ref",
    right_on = "COM",
    how = "left"
).unique(subset = var_groupe)

#########################################################
# Nettoyer les noms de communes
#########################################################

print("Nettoyer les noms de communes")

df2 = df1.with_columns(
    [
        (
            pl.col("commune_bv")
            .str.to_lowercase()
            .str.strip()
            .str.replace_all(r"[-_'’]", " ", literal=False)
            .str.replace_all(r"[(+*/&)]", " ", literal=False)
            .str.replace_all("saint", "st", literal=True)
            .str.replace_all(r"[éèêë]", "e", literal=False)
            .str.replace_all(r"[àâ]", "a", literal=False)
            .str.replace_all(r"[îï]", "i", literal=False)
            .str.replace_all(r"[ÿ]", "y", literal=False)
            .str.replace_all(r"[œ]", "oe", literal=False)
            .str.replace_all(r"[ô]", "o", literal=False)
            .str.replace_all(r"[ûü]", "u", literal=False)
            .str.replace_all(r"[ç]", "c", literal=False)
            .str.replace_all(r"\s{2,10}", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
            .str.replace_all(r"( la | les | le | l )", " ", literal=False)
            .str.replace_all(
                r"^(les |los |la |le |l |a la |au |aux )", "", literal=False
            )
        ).alias("commune_bv_clean"),
        (
            pl.col("r_commune2")
            .str.to_lowercase()
            .str.strip()
            .str.replace_all(r"[-_'’]", " ", literal=False)
            .str.replace_all(r"[(+*/&)]", " ", literal=False)
            .str.replace_all("saint", "st", literal=True)
            .str.replace_all(r"[éèêë]", "e", literal=False)
            .str.replace_all(r"[àâ]", "a", literal=False)
            .str.replace_all(r"[îï]", "i", literal=False)
            .str.replace_all(r"[ÿ]", "y", literal=False)
            .str.replace_all(r"[œ]", "oe", literal=False)
            .str.replace_all(r"[ô]", "o", literal=False)
            .str.replace_all(r"[ûü]", "u", literal=False)
            .str.replace_all(r"[ç]", "c", literal=False)
            .str.replace_all(r"\s{2,10}", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
            .str.replace_all(r"( la | les | le | l )", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
        ).alias("r_commune_clean"),
        (
            pl.col("c_commune")
            .str.to_lowercase()
            .str.strip()
            .str.replace_all(r"[-_'’]", " ", literal=False)
            .str.replace_all(r"[(+*/&)]", " ", literal=False)
            .str.replace_all("saint", "st", literal=True)
            .str.replace_all(r"[éèêë]", "e", literal=False)
            .str.replace_all(r"[àâ]", "a", literal=False)
            .str.replace_all(r"[îï]", "i", literal=False)
            .str.replace_all(r"[ÿ]", "y", literal=False)
            .str.replace_all(r"[œ]", "oe", literal=False)
            .str.replace_all(r"[ô]", "o", literal=False)
            .str.replace_all(r"[ûü]", "u", literal=False)
            .str.replace_all(r"[ç]", "c", literal=False)
            .str.replace_all(r"\s{2,10}", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
            .str.replace_all(r"( la | les | le | l )", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
        ).alias("c_commune_clean"),
        (
            pl.col("NCC")
            .str.to_lowercase()
            .str.strip()
            .str.replace_all(r"[-_'’]", " ", literal=False)
            .str.replace_all(r"[(+*/&)]", " ", literal=False)
            .str.replace_all("saint", "st", literal=True)
            .str.replace_all(r"[éèêë]", "e", literal=False)
            .str.replace_all(r"[àâ]", "a", literal=False)
            .str.replace_all(r"[îï]", "i", literal=False)
            .str.replace_all(r"[ÿ]", "y", literal=False)
            .str.replace_all(r"[œ]", "oe", literal=False)
            .str.replace_all(r"[ô]", "o", literal=False)
            .str.replace_all(r"[ûü]", "u", literal=False)
            .str.replace_all(r"[ç]", "c", literal=False)
            .str.replace_all(r"\s{2,10}", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
            .str.replace_all(r"( la | les | le | l )", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
        ).alias("NCC_clean"),
        (
            pl.col("NCCENR")
            .str.to_lowercase()
            .str.strip()
            .str.replace_all(r"[-_'’]", " ", literal=False)
            .str.replace_all(r"[(+*/&)]", " ", literal=False)
            .str.replace_all("saint", "st", literal=True)
            .str.replace_all(r"[éèêë]", "e", literal=False)
            .str.replace_all(r"[àâ]", "a", literal=False)
            .str.replace_all(r"[îï]", "i", literal=False)
            .str.replace_all(r"[ÿ]", "y", literal=False)
            .str.replace_all(r"[œ]", "oe", literal=False)
            .str.replace_all(r"[ô]", "o", literal=False)
            .str.replace_all(r"[ûü]", "u", literal=False)
            .str.replace_all(r"[ç]", "c", literal=False)
            .str.replace_all(r"\s{2,10}", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
            .str.replace_all(r"( la | les | le | l )", " ", literal=False)
            .str.replace_all(
                r"( de la | des | du | au | a la | aux | sur | sous | en )",
                " ",
                literal=False,
            )
        ).alias("NCCENR_clean"),
    ]
)

#########################################################
# Étape 1: Repérer les cas où les noms de communes sont identiques
#########################################################

print("Étape 1: Repérer les cas où les noms de communes sont identiques")

# Repérer les cas où les noms de communes sont identiques
df2 = df2.with_columns(
    (
        (
            (~pl.col("r_commune_clean").is_null())
            & (~(pl.col("r_commune_clean").str.lengths() < 3))
            & (pl.col("NCC_clean") == pl.col("r_commune_clean"))
        )
        | (
            (~pl.col("r_commune_clean").is_null())
            & (~(pl.col("r_commune_clean").str.lengths() < 3))
            & (pl.col("commune_bv_clean") == pl.col("r_commune_clean"))
        )
    )
    .cast(pl.Int8)
    .alias("nom_commune_identique")
)

#########################################################
# Étape 2: Repérer les cas où les noms de communes sont contenus l'un dans l'autre
#########################################################

print(
    "Étape 2: Repérer les cas où les noms de communes sont contenus l'un dans l'autre"
)


# Repérer les cas où les noms de communes sont contenus l'un dans l'autre
def is_match(regex, text):
    if regex is None:
        return False
    if text is None:
        return False
    try:
        pattern = re.compile(regex)
    except:
        print(regex)
    return pattern.search(text) is not None


df3 = df2.filter(pl.col("nom_commune_identique") == 0).to_pandas()
df3.loc[:, "nom_commune_approchant"] = [
    (is_match(df3["NCC_clean"][i], df3["r_commune_clean"][i]))
    | (is_match(df3["r_commune_clean"][i], df3["NCC_clean"][i]))
    for i in range(len(df3))
]

#########################################################
# Rassembler les résultats des étapes 1 et 2
#########################################################

print("Rassembler les résultats des étapes 1 et 2")


# Rassembler les infos par ["code_bv", "code_commune_ref", "commune_bv", "r_commune", "c_commune"]
df4 = pl.concat(
    [
        df2.filter(pl.col("nom_commune_identique") == 1).with_columns(pl.lit(0).cast(pl.Int32).alias("nom_commune_approchant")),
        pl.from_pandas(df3).select(pl.col(df2.columns + ["nom_commune_approchant"])).with_columns(
            [
                pl.col("dans_cog2022").cast(pl.Int32),
                pl.col("nom_commune_approchant").cast(pl.Int32),
            ]
        ),
    ],
    how="vertical",
)

#########################################################
# Étape 3: Repérer les noms de communes commençant par les mêmes lettres ou fréquemment associés
#########################################################

print(
    "Étape 3: Repérer les noms de communes commençant par les mêmes lettres ou fréquemment associés"
)

df4 = df4.with_columns(
    [
        pl.col("r_commune_clean").str.slice(0, 5).alias("r_commune_clean5"),
        pl.col("NCC_clean").str.slice(0, 5).alias("NCC_clean5"),
        pl.col("commune_bv_clean").str.slice(0, 5).alias("commune_bv_clean5")
    ]
).with_columns(
    (
            ((~pl.col("r_commune_clean5").is_null()) & (pl.col("r_commune_clean5") == pl.col("NCC_clean5"))) |
            ((~pl.col("r_commune_clean5").is_null()) & (pl.col("r_commune_clean5") == pl.col("commune_bv_clean5")))
    ).cast(pl.Int8).alias("nom_commune_approchant2")
).with_columns(
    [
        pl.when(pl.col("nb_lignes") > 20).then(1).otherwise(0).alias("noms_frequemment_associes")
    ]
)

#########################################################
# Synthèse des résultats: construction de la variable commune_identique
#########################################################

print("Synthèse des résultats: construction de la variable commune_identique")

df5 = df4.with_columns(
    [
        pl.when(pl.col("nom_commune_identique") == 1).then('1').otherwise(
            pl.when(pl.col("nom_commune_approchant") == 1).then('2').otherwise(
                pl.when(pl.col("nom_commune_approchant2") == 1).then('3').otherwise(
                    pl.when(pl.col("noms_frequemment_associes") == 1).then('4').otherwise('0')
                )
            )
        ).cast(pl.Utf8).alias("reconstitution_code_commune")
    ]
).with_columns(
    [
        pl.when(pl.col("reconstitution_code_commune") != '0').then(pl.lit('1')).otherwise(pl.lit('0')).cast(pl.Utf8).alias("commune_identique"),
    ]
)

#########################################################
# Finaliser la table des adresses
#########################################################

print("Construire la table finale des adresses")
df_final = df.join(
    df5.select(
        pl.col(var_groupe + ["reconstitution_code_commune", "commune_identique"])
    ),
    on=var_groupe,
    how="left",
)

#########################################################
# Sauvegarder la table finale
#########################################################

print("Sauvegarder la table finale")
pq.write_table(df_final.to_arrow(), datapath + "adressesREU_brutes2.parquet")
