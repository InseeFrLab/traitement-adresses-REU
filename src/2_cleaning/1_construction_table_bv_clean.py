### Imports

# Import packages
import pandas as pd
import re
from unidecode import unidecode

# Import fonctions
from functions_cleaner import complete_postal_code

# Import data
df_adresses = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/1_Inputs_nettoyage_manuel_parquet/adressesREU_brutes2.parquet"
)
df_adresses["id_brut_bv"] = (
    df_adresses["code_commune_ref"].fillna("") + "_" + df_adresses["code_bv"].fillna("")
)
bureaux_vote_insee = pd.read_parquet(
    "X:/HAB-Adresses-REU/data/4_Bureaux_de_vote/bureaux_de_vote_insee.parquet"
)
bureaux_vote_insee = bureaux_vote_insee[
    bureaux_vote_insee["code_commune"].apply(
        lambda x: not (x.isdigit()) or int(x) < 98000
    )
]
bureaux_vote_insee["id_brut"] = (
    bureaux_vote_insee["code_commune"].fillna("")
    + "_"
    + bureaux_vote_insee["code"].fillna("")
)

### Fonctions

list_chars = [
    ".",
    ",",
    ";",
    ":",
    "#",
    "°",
    "*",
    '"',
    "-",
    "/",
    "'",
    "  ",
]  # Undesirable punctuation


def clean_place_name(x):
    """
    Removes what is between parenthesis or brackets, lowers the string and removes undesirable punctuation
    """
    x_clean = re.sub("[\(\[].*?[\)\]]", "", x)
    for character in list_chars:
        x_clean = x_clean.replace(character, " ")
    x_clean = " ".join(
        [
            str(int(i)) if i.isnumeric() else i.strip()
            for i in x_clean.split(" ")
            if len(i) > 0
        ]
    )
    return unidecode(x_clean).strip()


### Gather the bureaux de vote from the REU

df_bv_REU = df_adresses[
    [
        "code_bv",
        "libelle_bv",
        "num_voie_bv",
        "voie_bv",
        "cp_bv",
        "commune_bv",
        "code_commune_ref",
        "id_brut_bv",
    ]
].drop_duplicates()
df_bv_REU.columns = [col.rsplit("_", 1)[0] for col in df_bv_REU.columns]
df_bv_REU.fillna(" ", inplace=True)
df_bv_REU.replace(to_replace=[None], value=" ", inplace=True)
df_bv_REU.replace(to_replace=["none"], value=" ", inplace=True)

### Nettoyage des champs

tables = [bureaux_vote_insee, df_bv_REU]
codes = ["code_commune", "cp"]
a_nettoyer = ["code", "commune", "libelle"]
cols_to_keep = ["code", "code_commune", "id_bv"]

for table in tables:
    table[codes] = table[codes].applymap(complete_postal_code)
    table[a_nettoyer] = (
        table[a_nettoyer]
        .apply(lambda x: x.astype(str).str.lower())
        .applymap(clean_place_name)
    )
    # Création d'un index unique
    table["id_bv"] = table["code_commune"] + "_" + table["code"]
    table["id_secours_bv"] = table["code_commune"] + "_" + table["libelle"]
    table["id_secours_2_bv"] = (
        table["code_commune"] + "_" + table["voie"].apply(lambda x: x[-10:])
    )
    table.drop_duplicates(subset=cols_to_keep + ["libelle"], inplace=True)

# Renommer les colonnes des deux tables
bureaux_vote_insee.rename(
    columns={
        col: col + "_insee"
        for col in bureaux_vote_insee.columns
        if col not in cols_to_keep
    },
    inplace=True,
)
df_bv_REU.rename(
    columns={col: col + "_reu" for col in df_bv_REU.columns if col not in cols_to_keep},
    inplace=True,
)

### Jointure

print(f"Nombre de bureaux de votes dans la table INSEE : {len(bureaux_vote_insee)}")
print(f"Nombre de bureaux de votes dans la table REU : {len(df_bv_REU)}")

duplicates_reu = df_bv_REU[df_bv_REU["id_bv"].duplicated(keep=False)]
duplicates_insee = bureaux_vote_insee[
    bureaux_vote_insee["id_bv"].duplicated(keep=False)
]
# After careful analyis of the duplicates, they are actually the same bureaux de votes with slightly different names
bureaux_vote_insee.drop_duplicates(subset="id_bv", inplace=True)
df_bv_REU.drop_duplicates(subset="id_bv", inplace=True)

df_bureaux_vote = pd.merge(
    bureaux_vote_insee,
    df_bv_REU,
    on=[
        "id_bv",
        "code",
        "code_commune",  # Pas utile, simplement pour ne pas les faire renommer
    ],
    how="inner",
)
print(
    f"Nombre de bureaux de votes dans l'inner join des tables : {len(df_bureaux_vote)}"
)
df_bureaux_vote["match_id_bv"] = True

# Quid des libellés ?
df_bureaux_vote["libelles_differents"] = (
    df_bureaux_vote["libelle_reu"] != df_bureaux_vote["libelle_insee"]
)
print(
    f"Nombre de bv qui ne matchent pas au libellé exact: {len(df_bureaux_vote[df_bureaux_vote['libelles_differents']])}"
)

df_bureaux_vote["libelles_rien_a_voir"] = (
    df_bureaux_vote["libelle_reu"].apply(lambda x: x.split(" ", 1)[0])
    != df_bureaux_vote["libelle_insee"].apply(lambda x: x.split(" ", 1)[0])
) & (
    df_bureaux_vote["libelle_reu"].apply(lambda x: x.rsplit(" ", 1)[-1])
    != df_bureaux_vote["libelle_insee"].apply(lambda x: x.rsplit(" ", 1)[-1])
)
print(
    f"Nombre de bv qui ne matchent pas au 1er mot du libellé : {len(df_bureaux_vote[df_bureaux_vote['libelles_rien_a_voir']])}"
)

df_bv_libelles_suspicieux = df_bureaux_vote[df_bureaux_vote["libelles_rien_a_voir"]][
    cols_to_keep + ["libelle_reu", "libelle_insee", "cp_reu", "cp_insee"]
]

### Etude des rebuts

rebuts_reu = df_bv_REU[~df_bv_REU.id_bv.isin(df_bureaux_vote.id_bv)]
print(f"Nombre de rebuts REU : {len(rebuts_reu)}")

rebuts_insee = bureaux_vote_insee[~bureaux_vote_insee.id_bv.isin(df_bureaux_vote.id_bv)]
print(f"Nombre de rebuts INSEE (hors cp > 97) : {len(rebuts_insee)}")

etude_rebuts = pd.merge(rebuts_insee, rebuts_reu, on=["code_commune"], how="outer")

rebuts_a_sauver = etude_rebuts[
    (etude_rebuts["id_secours_bv_reu"] == etude_rebuts["id_secours_bv_insee"])
    | (etude_rebuts["id_secours_2_bv_reu"] == etude_rebuts["id_secours_2_bv_insee"])
]
# Eventuellement revoir cette partie : plusieurs bureaux de vote à la même adresse dans le REU pourraient matcher
# à une même entrée dans le répertoire INSEE
rebuts_a_sauver = rebuts_a_sauver.drop(columns=["code_x", "id_bv_x"]).rename(
    columns={"code_y": "code", "id_bv_y": "id_bv"}
)

rebuts_a_sauver["match_id_bv"] = False
rebuts_a_sauver["libelles_differents"] = (
    rebuts_a_sauver["libelle_reu"] != rebuts_a_sauver["libelle_insee"]
)
rebuts_a_sauver["libelles_rien_a_voir"] = (
    rebuts_a_sauver["libelle_reu"].apply(lambda x: x.split(" ", 1)[0])
    != rebuts_a_sauver["libelle_insee"].apply(lambda x: x.split(" ", 1)[0])
) & (
    rebuts_a_sauver["libelle_reu"].apply(lambda x: x.rsplit(" ", 1)[-1])
    != rebuts_a_sauver["libelle_insee"].apply(lambda x: x.rsplit(" ", 1)[-1])
)

df_bureaux_vote_avec_sauves = pd.concat([df_bureaux_vote, rebuts_a_sauver], axis=0)

df_bureaux_vote_avec_sauves["match"] = True
df_bureaux_vote_avec_sauves["in_REU"] = True
df_bureaux_vote_avec_sauves["in_INSEE"] = True

rebuts_reu["in_REU"] = True
rebuts_reu["in_INSEE"] = False
rebuts_insee["in_REU"] = False
rebuts_insee["in_INSEE"] = True

vrais_rebuts = pd.merge(
    rebuts_insee,
    rebuts_reu,
    on=[
        "id_bv",
        "code",
        "code_commune",  # Pas utile, simplement pour ne pas les faire renommer
        "in_REU",
        "in_INSEE",  # Pas utile, simplement pour ne pas les faire renommer
    ],
    how="outer",
)
vrais_rebuts = vrais_rebuts[~vrais_rebuts.id_bv.isin(rebuts_a_sauver.id_bv)][
    ~vrais_rebuts.id_secours_bv_insee.isin(rebuts_a_sauver.id_secours_bv_insee)
][~vrais_rebuts.id_secours_2_bv_insee.isin(rebuts_a_sauver.id_secours_2_bv_insee)]

vrais_rebuts["match"] = False
vrais_rebuts["match_id_bv"] = False
vrais_rebuts["libelles_differents"] = True
vrais_rebuts["libelles_rien_a_voir"] = True

### Combien de bureaux de vote par commune ?

nombre_bv_par_commune_reu = (
    df_bv_REU["code_commune"].value_counts().to_frame().reset_index()
)
nombre_bv_par_commune_reu.columns = ["code_commune", "count_reu"]

nombre_bv_par_commune_insee = (
    bureaux_vote_insee["code_commune"].value_counts().to_frame().reset_index()
)
nombre_bv_par_commune_insee.columns = ["code_commune", "count_insee"]

nombre_bv = pd.merge(
    nombre_bv_par_commune_reu,
    nombre_bv_par_commune_insee,
    on=["code_commune"],
    how="outer",
)
nombre_bv["diff"] = (
    nombre_bv["count_insee"].fillna(0) - nombre_bv["count_reu"].fillna(0)
).astype(int)
nombre_bv.sort_values(
    by=["diff", "count_insee", "count_reu"], ascending=False, inplace=True
)

nombre_bv_differents = nombre_bv[nombre_bv["diff"] != 0]
print(
    f"Nombre de communes avec un nombre différent de bv selon le répertoire : {len(nombre_bv_differents)}"
)

suspicieux_dans_grandes_communes = pd.merge(
    df_bv_libelles_suspicieux,
    nombre_bv[nombre_bv["count_reu"] > 1],
    on=["code_commune"],
    how="inner",
).sort_values(["diff", "code_commune"], ascending=True)
print(
    f"Parmi les {len(df_bureaux_vote[df_bureaux_vote['libelles_rien_a_voir']])} libellés de bv ayant matché mais différents, "
    f"{len(suspicieux_dans_grandes_communes)} sont dans des communes avec plus de 1 bureau de vote"
)

# Regardons les bv ayant matché avec des libellés complètement différents dans des communes avec des rebuts
# Simplement pour voir si les rebuts en question ne pourraient pas être un meilleur match
# Spoiler : en pratique ce n'est pas le cas
last_check_suspicieux_grandes_communes = pd.merge(
    df_bv_REU,
    suspicieux_dans_grandes_communes[suspicieux_dans_grandes_communes["diff"] != 0][
        ["code_commune"]
    ],
    on="code_commune",
    how="inner",
)
last_check_suspicieux_grandes_communes = last_check_suspicieux_grandes_communes[
    ~last_check_suspicieux_grandes_communes.id_bv.isin(
        df_bureaux_vote[~df_bureaux_vote["libelles_rien_a_voir"]].id_bv
    )
]
last_check_suspicieux_grandes_communes = pd.merge(
    last_check_suspicieux_grandes_communes,
    bureaux_vote_insee,
    on=["id_bv", "code", "code_commune"],
    how="left",
)

nombre_de_bv_dans_communes_rebuts = pd.merge(
    vrais_rebuts, nombre_bv, on=["code_commune"], how="left"
).sort_values("diff", ascending=True)
# Aucun rebut n'est dans une commune avec le même nombre de bv des 2 côtés

a_verifier_a_la_main = nombre_de_bv_dans_communes_rebuts.dropna(how="any")
# Tous les rebuts sont dans des communes différentes, donc pas d'association plus poussée possible

print(
    f"Somme des écarts du nombre de bureaux de vote : {nombre_bv_differents['diff'].abs().sum()}"
)
print(f"Nombre de rebuts à la toute fin : {len(vrais_rebuts)}")
# Ecart de 1 dû à un bv INSEE qui a matché à 2 bv à la même adresse dans le REU lors de la récup des rebuts

### Table finale de correspondance

table_bv_finale = pd.concat([df_bureaux_vote_avec_sauves, vrais_rebuts], axis=0)[
    [
        "id_bv",
        "code",
        "code_commune",
        "libelle_insee",
        "num_voie_insee",
        "voie_insee",
        "complement1_insee",
        "complement2_insee",
        "lieu_dit_insee",
        "cp_insee",
        "commune_insee",
        "id_brut_insee",
        "libelle_reu",
        "num_voie_reu",
        "voie_reu",
        "cp_reu",
        "commune_reu",
        "id_brut_reu",
        "match",
        "match_id_bv",
        "libelles_differents",
        "libelles_rien_a_voir",
        "in_REU",
        "in_INSEE",
    ]
]

### Ajout du nombre d'adresses par bureau de vote
# Attention, il faudra plutôt le faire après dédoublonnage !

nb_adresses_par_bv_reu = (
    df_adresses.groupby("id_brut_bv").size().reset_index(name="nb_adresses")
)
nb_adresses_par_bv_reu.rename(columns={"id_brut_bv": "id_brut_reu"}, inplace=True)

table_bv_finale = pd.merge(
    table_bv_finale, nb_adresses_par_bv_reu, on="id_brut_reu", how="left"
)
table_bv_finale["nb_adresses"] = table_bv_finale["nb_adresses"].fillna(0).astype(int)

table_bv_finale.sort_values(
    by=["in_REU", "in_INSEE", "nb_adresses", "id_bv"], ascending=False, inplace=True
)

table_bv_finale.to_parquet(
    "X:/HAB-Adresses-REU/data/4_Bureaux_de_vote/table_correspondance_bv_complete.parquet",
    index=False,
)

table_bv_finale_simplifiee = table_bv_finale[table_bv_finale["in_REU"]][
    [
        "id_brut_reu",
        "id_brut_insee",
        "code_commune",
        "code",
        "libelle_reu",
        "num_voie_reu",
        "voie_reu",
        "cp_reu",
        "commune_reu",
        "in_INSEE",
        "nb_adresses",
    ]
]

table_bv_finale_simplifiee.to_parquet(
    "X:/HAB-Adresses-REU/data/4_Bureaux_de_vote/table_correspondance_bv_simplifiee.parquet",
    index=False,
)
