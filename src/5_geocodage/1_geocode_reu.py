#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Credits to Christian QUEST
# Le code ci-dessous reprend ses scripts écrits pour géocoder la base Sirene
# (voir https://github.com/cquest/geocodage-sirene)

import os
import sys
import csv
import requests
import json
import re

score_min = 0.30

# URL à appeler pour géocodage BAN, BANO
addok_url = {}
addok_url["ban"] = "http://addok-ban.projet-addok/search"
addok_url["bano"] = "http://addok-bano.projet-addok/search"


# Ouverture de sessions pour requests en keep-alive
s = {}
for url in addok_url.values():
    s[url] = requests.Session()


# req. sur l'API de géocodage
def geocode(api, params, l4):
    params["autocomplete"] = 0
    params["q"] = params["q"].strip()
    params["limit"] = 1
    if (
        depcom != ""
        and depcom is not None
        and re.match(r"^[0-9][0-9AabB][0-9]{3}$", depcom)
    ):
        params["citycode"] = depcom
    try:
        r = s[api].get(api, params=params)
        j = json.loads(r.text)
        global geocode_count
        geocode_count += 1
        if "features" in j and len(j["features"]) > 0:
            j["features"][0]["l4"] = l4
            j["features"][0]["geo_l4"] = ""
            j["features"][0]["geo_l5"] = ""
            # regénération lignes 4 et 5 normalisées
            name = j["features"][0]["properties"]["name"]
            ligne4 = re.sub(r"\(.*$", "", name).strip()
            ligne4 = re.sub(r",.*$", "", ligne4).strip()
            ligne5 = ""
            j["features"][0]["geo_l4"] = ligne4
            if "(" in name:
                ligne5 = re.sub(r".*\((.*)\)", r"\1", name).strip()
                j["features"][0]["geo_l5"] = ligne5
            if "," in name:
                ligne5 = re.sub(r".*,(.*)", r"\1", name).strip()
                j["features"][0]["geo_l5"] = ligne5
            # ligne 4 et 5 identiques ? on supprime la 5
            if j["features"][0]["geo_l5"] == j["features"][0]["geo_l4"]:
                j["features"][0]["geo_l5"] = ""
            return j["features"][0]
        else:
            return None
    except:
        global error_count
        error_count += 1
        print(
            json.dumps(
                {"action": "erreur", "api": api, "params": params, "l4": l4},
                ensure_ascii=False,
            )
        )
        return None


def trace(txt):
    if False:
        # if True:
        print(txt)


# def des csv
file = sys.argv[1]
dir = "data/"


geocode_count = 0
error_count = 0
ok = 0
total = 0

numbers = re.compile("(^[0-9]*)")

stats = {
    "action": "progress",
    "housenumber": 0,
    "interpolation": 0,
    "street": 0,
    "locality": 0,
    "municipality": 0,
    "vide": 0,
    "manque": 0,
    "townhall": 0,
    "poi": 0,
    "etranger": 0,
    "erreur": 0,
    "fichier": file,
}

empty_result = ["", "", 0, "", "", "", "", "", "", "", ""]

with open(dir + file, "r", encoding="utf-8") as f_in, open(
    dir + "geo-" + file, "w", newline=""
) as f_out:
    file_in = csv.reader(f_in, delimiter=",")
    file_geo = csv.writer(f_out, delimiter=",")
    header = next(file_in)
    file_geo.writerow(
        [
            "id_adresse",
            "longitude",
            "latitude",
            "geo_score",
            "geo_type",
            "geo_adresse",
            "id",
            "api_line",
            "code_commune_ref",
            "reconstitution_code_commune",
            "commune_identique",
            "id_brut_bv",
        ]
    )

    for et in file_in:
        total = total + 1
        # mapping des champs de file_in
        #
        id_adresse = [et[2]]
        numvoie = numbers.match(et[3]).group(0).lstrip("0")
        cut_numvoie = et[3].split(" ")
        indrep = ""
        if len(cut_numvoie) > 1:
            indrep = cut_numvoie[-1]
        typvoie = ""
        libvoie = re.sub(r"^NA$", "", et[4].strip())
        # compladr=compl+lieudit et on enlève les blancs en trop
        compladr = re.sub(r"^NA$", "", (et[5] + " " + et[6]).strip())
        # si libvoie est vide et compladr non alors adresse = le complément d'adresse
        if libvoie == "" and compladr != "":
            libvoie = compladr
            compladr = ""

        # lecture code INSEE/nom de la commune
        depcom = re.sub(r"^NA$", "", et[10])
        # si le depcom est formé de 4 chiffres on ajoute un 0 devant (perte du 0 si le depcom a été lu en numérique dans une phase
        # de traitement antérieure
        if len(depcom) == 4:
            depcom = "0" + depcom
        ville = re.sub(r"^NA$", "", et[9])
        pays = re.sub(r"^NA$", "", et[12])
        cp = re.sub(r"^NA$", "", et[7])
        if len(cp) == 4:
            cp = "0" + cp
        dep = et[11]

        reconstitution_code_commune = et[18]
        commune_identique = et[19]
        id_brut_bv = et[20]

        ### condition pour éliminer si pays != FRANCE ou france ...
        if dep not in ["99"]:
            # Travail du numvoie
            if numvoie == "" and numbers.match(libvoie).group(0):
                numvoie = numbers.match(libvoie).group(0)
                libvoie = libvoie[len(numvoie) :]

            # Travail du typvoie
            # voir si on peut l'extraire de libvoie
            typ_abrege = {
                "ALL": "Allée",
                "AV": "Avenue",
                "BD": "Boulevard",
                "CAR": "Carrefour",
                "CD": "Chemin départemental",
                "CHE": "Chemin",
                "CHS": "Chaussée",
                "CITE": "Cité",
                "CIT": "Cité",
                "COR": "Corniche",
                "CRS": "Cours",
                "CR": "Chemin rural",
                "DOM": "Domaine",
                "DSC": "Descente",
                "ECA": "Ecart",
                "ESP": "Esplanade",
                "FG": "Faubourg",
                "GR": "Grande Rue",
                "HAM": "Hameau",
                "HLE": "Halle",
                "IMP": "Impasse",
                "LD": "Lieu-dit",
                "LOT": "Lotissement",
                "MAR": "Marché",
                "MTE": "Montée",
                "PAS": "Passage",
                "PLN": "Plaine",
                "PLT": "Plateau",
                "PL": "Place",
                "PRO": "Promenade",
                "PRV": "Parvis",
                "QUAI": "Quai",
                "QUA": "Quartier",
                "QU": "Quai",
                "RES": "Résidence",
                "RLE": "Ruelle",
                "ROC": "Rocade",
                "RPT": "Rond-point",
                "RTE": "Route",
                "RN": "Route nationale",
                "R": "Rue",
                "RUE": "Rue",
                "SEN": "Sentier",
                "SQ": "Square",
                "TPL": "Terre-plein",
                "TRA": "Traverse",
                "VC": "Chemin vicinal",
                "VLA": "Villa",
                "VLGE": "Village",
            }
            if typvoie in typ_abrege:
                typvoie = typ_abrege[typvoie]

            # Travail sur le libvoie
            # libvoie = re.sub(r'^LD ', '', libvoie)
            # libvoie = re.sub(r'^LIEU(.|)DIT ', '', libvoie)
            libvoie = re.sub(r"^ADRESSE INCOMPLETE.*", "", libvoie)
            libvoie = re.sub(r"^SANS DOMICILE FIXE", "", libvoie)
            libvoie = re.sub(r"^COMMUNE DE RATTACHEMENT", "", libvoie)

            ligne4G = ("%s%s %s %s %s" % (numvoie, indrep, libvoie, cp, ville)).strip()
            ligne4D = ligne4G
            if compladr != "" and compladr is not None:
                ligne4D = (
                    "%s%s %s %s %s %s" % (numvoie, indrep, libvoie, compladr, cp, ville)
                ).strip()

            trace("%s" % (ligne4G))
            trace("%s" % (ligne4D))

            # géocodage BAN (ligne4 géo, déclarée ou normalisée si pas trouvé ou score insuffisant)
            ban = None
            if ligne4G != "":
                ban = geocode(addok_url["ban"], {"q": ligne4G}, "BANG")
                trace("%s" % ("BANG"))
            if (
                ban is None
                or ban["properties"]["score"] < score_min
                and ligne4D != ligne4G
                and ligne4D != ""
            ):
                ban = geocode(addok_url["ban"], {"q": ligne4D}, "BAND")
                trace("%s" % ("BAND"))
            # géocodage BANO (ligne4 géo, déclarée ou normalisée si pas trouvé ou score insuffisant)
            bano = None
            if ban is None or ban["properties"]["score"] < 0.9:
                if ligne4G != "":
                    bano = geocode(addok_url["bano"], {"q": ligne4G}, "BANOG")
                    trace("%s" % ("BANOG"))
                if (
                    bano is None
                    or bano["properties"]["score"] < score_min
                    and ligne4D != ligne4G
                    and ligne4D != ""
                ):
                    bano = geocode(addok_url["bano"], {"q": ligne4D}, "BANOD")
                    trace("%s" % ("BANOD"))

            if ban is not None:
                ban_score = ban["properties"]["score"]
                trace(ban_score)
                ban_type = ban["properties"]["type"]
                if ["village", "town", "city"].count(ban_type) > 0:
                    ban_type = "municipality"
            else:
                ban_score = 0
                ban_type = ""

            if bano is not None:
                bano_score = bano["properties"]["score"]
                trace(bano_score)
                if bano["properties"]["type"] == "place":
                    bano["properties"]["type"] = "locality"
                bano["properties"]["id"] = "BANO_" + bano["properties"]["id"]
                if bano["properties"]["type"] == "housenumber":
                    bano["properties"]["id"] = "%s_%s" % (
                        bano["properties"]["id"],
                        bano["properties"]["housenumber"],
                    )
                bano_type = bano["properties"]["type"]
                if ["village", "town", "city"].count(bano_type) > 0:
                    bano_type = "municipality"
            else:
                bano_score = 0
                bano_type = ""

            # choix de la source
            source = None
            score = 0

            # on a un numéro... on cherche dessus
            if numvoie != "":
                # numéro trouvé dans les deux bases, on prend BAN
                # sauf si score inférieur de 20% à BANO
                if (
                    ban_type == "housenumber"
                    and bano_type == "housenumber"
                    and ban_score > score_min
                    and ban_score >= bano_score / 1.2
                ):
                    source = ban
                    score = ban["properties"]["score"]
                elif ban_type == "housenumber" and ban_score > score_min:
                    source = ban
                    score = ban["properties"]["score"]
                elif bano_type == "housenumber" and bano_score > score_min:
                    source = bano
                    score = bano["properties"]["score"]
                # on cherche une interpollation dans BAN
                elif ban is None or ban_type == "street" and int(numvoie) > 2:
                    ban_avant = geocode(
                        addok_url["ban"],
                        {
                            "q": "%s %s %s %s"
                            % (int(numvoie) - 2, typvoie, libvoie, ville)
                        },
                        "BANI",
                    )
                    ban_apres = geocode(
                        addok_url["ban"],
                        {
                            "q": "%s %s %s %s"
                            % (int(numvoie) + 2, typvoie, libvoie, ville)
                        },
                        "BANI",
                    )
                    if ban_avant is not None and ban_apres is not None:
                        if (
                            ban_avant["properties"]["type"] == "housenumber"
                            and ban_apres["properties"]["type"] == "housenumber"
                            and ban_avant["properties"]["score"] > 0.5
                            and ban_apres["properties"]["score"] > score_min
                        ):
                            source = ban_avant
                            score = ban_avant["properties"]["score"] / 2
                            source["geometry"]["coordinates"][0] = round(
                                (
                                    ban_avant["geometry"]["coordinates"][0]
                                    + ban_apres["geometry"]["coordinates"][0]
                                )
                                / 2,
                                6,
                            )
                            source["geometry"]["coordinates"][1] = round(
                                (
                                    ban_avant["geometry"]["coordinates"][1]
                                    + ban_apres["geometry"]["coordinates"][1]
                                )
                                / 2,
                                6,
                            )
                            source["properties"]["score"] = (
                                ban_avant["properties"]["score"]
                                + ban_apres["properties"]["score"]
                            ) / 2
                            source["properties"]["type"] = "interpolation"
                            source["properties"]["id"] = ""
                            source["properties"]["label"] = (
                                numvoie
                                + ban_avant["properties"]["label"][
                                    len(ban_avant["properties"]["housenumber"]) :
                                ]
                            )

            # on essaye sans l'indice de répétition (BIS, TER qui ne correspond pas ou qui manque en base)
            if source is None and ban is None and indrep != "":
                addok = geocode(
                    addok_url["ban"],
                    {"q": "%s %s %s %s" % (numvoie, typvoie, libvoie, ville)},
                    "BANR",
                )
                if (
                    addok is not None
                    and addok["properties"]["type"] == "housenumber"
                    and addok["properties"]["score"] > score_min
                ):
                    addok["properties"]["type"] = "interpolation"
                    source = addok
            if source is None and bano is None and indrep != "":
                addok = geocode(
                    addok_url["bano"],
                    {"q": "%s %s %s %s" % (numvoie, typvoie, libvoie, ville)},
                    "BANOR",
                )
                if (
                    addok is not None
                    and addok["properties"]["type"] == "housenumber"
                    and addok["properties"]["score"] > score_min
                ):
                    addok["properties"]["type"] = "interpolation"
                    source = addok

            # pas trouvé ? on cherche une rue
            if source is None and typvoie != "":
                if (
                    ban_type == "street"
                    and bano_type == "street"
                    and ban_score > score_min
                    and ban_score >= bano_score / 1.2
                ):
                    source = ban
                    score = ban["properties"]["score"]
                elif ban_type == "street" and ban_score > score_min:
                    source = ban
                elif bano_type == "street" and bano_score > score_min:
                    source = bano

            # pas trouvé ? on cherche sans numvoie
            if source is None and numvoie != "":
                addok = geocode(
                    addok_url["ban"],
                    {"q": "%s %s %s" % (typvoie, libvoie, ville)},
                    "BANN",
                )
                if (
                    addok is not None
                    and addok["properties"]["type"] == "street"
                    and addok["properties"]["score"] > score_min
                ):
                    source = addok
            if source is None and numvoie != "":
                addok = geocode(
                    addok_url["bano"],
                    {"q": "%s %s %s" % (typvoie, libvoie, ville)},
                    "BANON",
                )
                if (
                    addok is not None
                    and addok["properties"]["type"] == "street"
                    and addok["properties"]["score"] > score_min
                ):
                    source = addok

            # toujours pas trouvé ? tout type accepté...
            if source is None:
                if ban_score > score_min and ban_score >= bano_score * 0.8:
                    source = ban
                elif ban_score > score_min:
                    source = ban
                elif bano_score > score_min:
                    source = bano

            if source is not None and score == 0:
                score = source["properties"]["score"]

            if source is None:
                row = id_adresse + empty_result
                if ligne4G.strip() != "":
                    stats["manque"] += 1
                    print(
                        json.dumps(
                            {
                                "action": "manque",
                                "et": et,
                                "adr_comm_insee": depcom,
                                "adr_short": ligne4G.strip(),
                                "adr_long": ligne4D.strip(),
                            },
                            sort_keys=True,
                            ensure_ascii=False,
                        )
                    )
                else:
                    stats["vide"] += 1
                file_geo.writerow(row)
            else:
                row = id_adresse + [
                    source["geometry"]["coordinates"][0],
                    source["geometry"]["coordinates"][1],
                    round(source["properties"]["score"], 2),
                    source["properties"]["type"],
                    source["properties"]["label"],
                    source["properties"]["id"],
                    source["l4"],
                    depcom,
                    reconstitution_code_commune,
                    commune_identique,
                    id_brut_bv,
                ]
                ok += 1
                if ["village", "town", "city"].count(source["properties"]["type"]) > 0:
                    source["properties"]["type"] = "municipality"
                stats[re.sub(r"\..*$", "", source["properties"]["type"])] += 1
                file_geo.writerow(row)
        else:
            stats["etranger"] += 1
            row = id_adresse + empty_result
            file_geo.writerow(row)

# final count
stats["count"] = total
stats["geocode_count"] = geocode_count
stats["erreur"] = error_count
stats["action"] = "final"
if total != 0:
    stats["efficacite"] = round(100 * ok / total, 2)
else:
    stats["efficacite"] = "NA"
print(json.dumps(stats, sort_keys=True, ensure_ascii=False))
