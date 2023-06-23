### Imports

# Import packages
import pandas as pd


# Imports données
rawdatapath = "X:/HAB-Adresses-REU/rawdata/"
bureaux_vote_insee = pd.read_csv(
    rawdatapath + "2022-bureaux_vote_30032022.csv",
    dtype=str,
    sep="\t",
    keep_default_na=False,
)


### Sélection des colonnes intéressantes
bureaux_vote_insee = bureaux_vote_insee[
    [
        "code_normalise_complet",
        "Libelle-2",
        "num_voie",
        "voie",
        "complement1",
        "complement2",
        "lieu_dit",
        "code_postal",
        "commune_code",
        "commune",
    ]
]
bureaux_vote_insee.rename(
    columns={
        "code_normalise_complet": "code",
        "Libelle-2": "libelle",
        "code_postal": "cp",
        "commune_code": "code_commune",
    },
    inplace=True,
)

bureaux_vote_insee.fillna(" ", inplace=True)
bureaux_vote_insee.replace(to_replace=[None], value=" ", inplace=True)
bureaux_vote_insee.replace(to_replace=["none"], value=" ", inplace=True)

### Enregistrer la table
bureaux_vote_insee.to_parquet(
    "X:/HAB-Adresses-REU/data/4_Bureaux_de_vote/bureaux_de_vote_insee.parquet",
    index=False,
)
