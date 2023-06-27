import polars as pl
import pyarrow.parquet as pq

# Les chemins
datacleanpath = "X:/HAB-Adresses-REU/data/2_Nettoyage_manuel_adresses/"
dataBVpath = "X:/HAB-Adresses-REU/data/4_Bureaux_de_vote/"
retourBANpath = "X:/HAB-Adresses-REU/data/5_Retours_BAN/"
outputpath = "X:/HAB-Adresses-REU/data/6_Tables_finales/"

# Les variables de la table finale des adresses
variables_table_adresses = [
    "code_commune_ref",
    "reconstitution_code_commune",
    "id_brut_bv",
    "id",
    "geo_adresse",
    "geo_type",
    "geo_score",
    "longitude",
    "latitude",
    "api_line",
    "nb_bv_commune",
    "nb_adresses",
]

# les variables de la table finale des bureaux de vote
variables_table_bv = [
    "id_brut_reu",
    "id_brut_insee",
    "code_commune",
    "code",
    "libelle_reu",
    "num_voie_reu",
    "voie_reu",
    "cp_reu",
    "commune_reu",
    "nb_adresses_initial",
    "nb_adresses_final",
]

# les principales communes absentes de la BAN
communes_a_retirer = ["97801", "97701"]  # Saint-Martin  # Saint-Barthélémy

###################################################################
# Charger les données
###################################################################

# Cette table contient toutes les adresses brutes avec un identifiant non signifiant
table_adresses = pl.from_arrow(
    pq.read_table(datacleanpath + "cleaned_addresses_large.parquet")
)

# Cette table contient le passage entre identifiant non signifiant et identifiant d'adresse nettoyée dédoublonnée
table_passage = pl.from_arrow(
    pq.read_table(datacleanpath + "table_correspondance_id_groups.parquet")
)

# Cette table contient les bureaux de vote
table_bv = pl.from_arrow(
    pq.read_table(dataBVpath + "table_correspondance_bv_simplifiee.parquet")
)

# Cette table contient les retours de la géolocalisation
table_geolocalisation_BAN = pl.from_arrow(
    pq.read_table(retourBANpath + "sorties_BAN_20230207.parquet")
).with_columns(pl.col("id_adresse").cast(pl.Int64).alias("id_adresse"))

###################################################################
# Construire les tables finales
###################################################################

# Ajouter l'identifiant de groupe d'adresses puis les résultats de la géolocalisation sur la table des adresses
table_adresses2 = (
    table_adresses.join(
        table_passage.select(["identifiant_ligne", "id_adresse"]),
        on="identifiant_ligne",
        how="left",
    )
    .join(
        table_geolocalisation_BAN.select(
            [
                "id_adresse",
                "id",
                "geo_adresse",
                "geo_type",
                "geo_score",
                "longitude",
                "latitude",
                "api_line",
            ]
        ),
        on="id_adresse",
        how="left",
    )
    .select(
        # Compter le nombre de bureaux de vote par commune
        [
            pl.col("*"),
            pl.col("id_brut_bv")
            .n_unique()
            .over("code_commune_ref")
            .alias("nb_bv_commune"),
        ]
    )
)
print(table_adresses2.shape[0])

# Compter le nombre initial d'adresses par bureau de vote
nb_initial_adresses_bv = (
    table_adresses2.groupby(["id_brut_bv"])
    .agg(pl.count().alias("nb_adresses_initial"))
    .sort(["id_brut_bv"])
)

# On conserve les adresses qui valident les trois conditions suivantes:
# - Elles ont pu être géolocalisées avec la BAN
# - Elles sont situées dans la commune du bureau de vote: commune_identique == "1"
# - Elles sont géolocalisées plus finement que la commune ou elles sont situées dans une commune avec un seul bureau de vote
table_adresses3 = table_adresses2.filter(
    (pl.col("id") != None)
    & (pl.col("commune_identique") == "1")
    & ((pl.col("geo_type") != "municipality") | (pl.col("nb_bv_commune") == 1))
)

# Compter le nombre final d'adresses par bureau de vote
nb_final_adresses_bv = (
    table_adresses3.groupby(["id_brut_bv"])
    .agg(pl.count().alias("nb_adresses_final"))
    .sort(["id_brut_bv"])
)

print(table_adresses3.shape[0])

# Construire la table finale des adresses, en ajoutant le nombre d'adresses regroupées sur chaque ligne
table_adresses_final = (
    table_adresses3.unique(subset=["code_commune_ref", "id_brut_bv", "id"])
    .join(
        table_adresses3.groupby(["code_commune_ref", "id_brut_bv", "id"]).agg(
            pl.count().alias("nb_adresses")
        ),
        on=["code_commune_ref", "id_brut_bv", "id"],
        how="left",
    )
    .select(variables_table_adresses)
    .sort(["code_commune_ref", "id_brut_bv"])
)

# Construire la table finale des bureaux de vote, en ajoutant le nombre d'adresses regroupées sur chaque ligne
# On ne garde que les "vrais" bureaux de vote, ie avec un code commune cohérent
table_bv_final = (
    table_bv.filter(~pl.col("code_commune").str.starts_with("00"))
    .join(
        nb_initial_adresses_bv, left_on="id_brut_reu", right_on="id_brut_bv", how="left"
    )
    .join(
        nb_final_adresses_bv, left_on="id_brut_reu", right_on="id_brut_bv", how="left"
    )
    .select(variables_table_bv)
    .sort("id_brut_reu")
)

###################################################################
# Retirer les communes absentes de la BAN
###################################################################

table_adresses_final = table_adresses_final.filter(
    ~pl.col("code_commune_ref").is_in(communes_a_retirer)
)
table_bv_final = table_bv_final.filter(
    ~pl.col("code_commune").is_in(communes_a_retirer)
)

###################################################################
# Sauvegarder les tables finales
###################################################################

# La table des adresses
table_adresses_final = table_adresses_final.rename({"id_brut_bv": "id_brut_bv_reu"})
pq.write_table(table_adresses_final.to_arrow(), outputpath + "table_adresses.parquet")

# La table des bureaux de vote
pq.write_table(table_bv_final.to_arrow(), outputpath + "table_bv.parquet")
