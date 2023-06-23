import pandas as pd
import re
from tqdm import tqdm


def clean_dataset(df: pd.DataFrame, generate_adresse_complete=True) -> pd.DataFrame:
    """
    Puts fields in lowercase, remove the names of persons from the dataset and cleans the addresses for the BAN API

    Args:
        generate_adresse_complete:
        df (pd.DataFrame): the raw dataframe read from INSEE file

    Returns:
        pd.DataFrame: a dataframe with added cleaned fields
    """

    # We will treat both "adresses de rattachement" and "adresses de contact"
    # If one wants to add (or remove) a new type of address or remove an existing one, the list below can be changed
    # However clean_adresses.py will need to be adapted
    address_types = ["r", "c"]

    # We select the columns we will treat, ie the ones defining the address
    fields_to_check = ["num_voie", "voie", "complément1", "complément2", "lieu_dit"]
    columns_to_check = [
        address + "_" + field for address in address_types for field in fields_to_check
    ]

    original_columns = [column + "_original" for column in columns_to_check]
    anonymized_columns = [column + "_anonymized" for column in columns_to_check]
    cleaned_columns = [column + "_clean" for column in columns_to_check]

    df[original_columns] = df[columns_to_check].copy()

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

    def remove_punctuation(x):
        clean_x = str(x)
        for character in list_chars:
            clean_x = clean_x.replace(character, " ")
        clean_x = clean_x.replace("&", " et ").replace("  ", " ").lower()
        return clean_x.strip()

    # Remove all nans from dataset
    df.fillna("", inplace=True)
    df.replace(to_replace=[None], value="", inplace=True)
    df.replace(to_replace=["none"], value="", inplace=True)

    # Put all interesting columns in lowercase and remove punctuation
    df[columns_to_check] = df[columns_to_check].apply(
        lambda x: x.astype(str).str.lower()
    )
    df[columns_to_check] = df[columns_to_check].applymap(remove_punctuation)
    print("Lowercase + remove punctuation: OK")

    # List all the variations of "chez" people wrote in the dataset
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
        [
            space + chez + " "
            for chez in liste_all_variantes_chez
            for space in [" ", "-"]
        ]
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
        "esc",  # Words like "escalier" are too often used in street names to be removed
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

    # List of all the words that represent a street type
    liste_streets = [
        "allée",
        "allee",
        "anse",
        "avenue",
        "av",
        "boulevard",
        "bd",
        "section",
        "carrefour",
        "chaussée",
        "chaussee",
        "chemin",
        "cité",
        "cite",
        "clos",
        "côte",
        "cote",
        "cour",
        "cours",
        "degré",
        "degre",
        "descente",
        "drève",
        "dreve",
        "esplanade",
        "gaffe",
        "impasse",
        "liaison",
        "mail",
        "montée",
        "montee",
        "passage",
        "place",
        "placette",
        "pont",
        "promenade",
        "quai",
        "résidence",
        "residence",
        "rang",
        "rampe",
        "rond-point",
        "route",
        "rue",
        "r",
        "ruelle",
        "sente",
        "sentier",
        "square",
        "traboule",
        "traverse",
        "venelle",
        "villa",
        "voie",
        "bourg",
        "lieu",
        "lieu-dit",
    ] + liste_specifications
    str_streets = "|".join([" " + word + " " for word in liste_streets])

    # Words we accept before or after "chez", as they are part of a nominal group not referring to personal data
    okay_words_before_chez = [
        "le",
        "la",
        "les",
        "des",
        "du",
        "de",
        "vers",
        "st",
        "saint",
        "haut",
        "bas",
        "petite",
        "grande",
        "l",
    ] + liste_streets
    okay_words_after_chez = [
        "le",
        "la",
        "les",
        "des",
        "du",
        "de",
        "gros",
        "pere",
        "chantre",
        "lieu",
        "lieu-dit",
        "sud",
        "nord",
        "est",
        "ouest",
        "haut",
        "bas",
        "st",
        "saint",
        "rural",
        "tout",
        "zone",
        "petit",
        "grand",
        "beau",
        "c",
        "mal",
        "commercial",
        "joli",
        "frere",
        "bassin",
        "parc",
        "terre",
        "trois",
        "ligne",
        "canal",
        "lebon",
        "sainte",
        "ste",
        "leconte",
        "moulin",
        "chateau",
        "bebe",
    ]

    print("Prepare global variables for normalization: OK")

    # What are the addresses that need to be anonymized?
    df["flag_anonymization"] = (
        df[columns_to_check]
        .applymap(
            requires_anonymization,
            str_variantes_chez=str_variantes_chez,
            tuple_all_variantes_chez=tuple_all_variantes_chez,
            str_all_patterns=str_all_patterns,
        )
        .max(axis=1)
    )
    print("Find observations to be anonymized: OK")

    df[anonymized_columns] = df[columns_to_check].copy()
    df["was_anonymized"] = False

    # Separate the problematic addresses and the okay ones
    df_no_anonymization = df[df["flag_anonymization"] != 2]
    df_anonymization = df[df["flag_anonymization"] == 2]
    print("Nb of rows with possible names:", len(df_anonymization))

    # Cleaning!
    df_anonymization[anonymized_columns] = df_anonymization[
        anonymized_columns
    ].applymap(
        lambda x: remove_names(
            x,
            liste_variantes_chez=liste_variantes_chez,
            liste_all_variantes_chez=liste_all_variantes_chez,
            str_all_variantes_chez=str_all_variantes_chez,
            okay_words_before_chez=okay_words_before_chez,
            okay_words_after_chez=okay_words_after_chez,
            str_streets=str_streets,
        )
    )
    # Keep in mind which ones have been changed to check them later on
    df_anonymization["was_anonymized"] = df_anonymization[columns_to_check].agg(
        " ".join, axis=1
    ) != df_anonymization[anonymized_columns].agg(" ".join, axis=1)
    # Re-concatenate the dataset
    df = pd.concat([df_anonymization, df_no_anonymization])
    print("Anonymization step: OK")

    # Now same process with cleaning extra specifications and wrongly placed postal codes

    df["flag_cleaning"] = (
        df[anonymized_columns]
        .applymap(requires_cleaning, str_specifications=str_specifications)
        .max(axis=1)
    )
    print("Find observations to be cleaned: OK")

    df[cleaned_columns] = df[anonymized_columns].copy()
    df["was_cleaned"] = False

    df_no_cleaning = df[df["flag_cleaning"] != 1]
    df_cleaning = df[df["flag_cleaning"] == 1]
    print("Nb of rows with possible specifications to remove:", len(df_cleaning))

    df_cleaning[cleaned_columns] = df_cleaning[cleaned_columns].applymap(
        lambda x: remove_specifications(
            x,
            liste_specifications=liste_specifications,
            str_specifications=str_specifications,
            okay_words_before_chez=okay_words_before_chez,
            okay_words_after_chez=okay_words_after_chez,
        )
    )
    df_cleaning["was_cleaned"] = df_cleaning[cleaned_columns].agg(
        " ".join, axis=1
    ) != df_cleaning[anonymized_columns].agg(" ".join, axis=1)
    df = pd.concat([df_cleaning, df_no_cleaning])
    print("Cleaning step: OK")

    # The loop below is the longest step...
    for address in tqdm(address_types):
        # Specific cleaning for street numbers
        df[address + "_num_voie_clean"] = df[address + "_num_voie_clean"].apply(
            clear_num_voie
        )

        # Concatenate address complements
        df[address + "_all_complements_clean"] = df[
            [
                address + "_" + field + "_clean"
                for field in ["complément1", "complément2"]
            ]
        ].agg(" ".join, axis=1)

        # Reformat the postal codes in the standard way
        df[address + "_cp_clean"] = (
            df[address + "_cp"].apply(remove_punctuation).apply(complete_postal_code)
        )

        # Create the department variable from the postal code
        df[address + "_departement"] = df.apply(
            lambda row: get_departement(row, address), axis=1
        )

        # Create a unique field with the original addresses
        df[address + "_adresse_originale"] = df[
            [address + "_" + field + "_original" for field in fields_to_check]
        ].agg(" ".join, axis=1)
        # Create a unique field with the original addresses lowered and without punctuation
        df[address + "_adresse_pre_treated"] = df[
            [address + "_" + field for field in fields_to_check]
        ].agg(" ".join, axis=1)

        # If we are okay with an additional 2 hours in the execution time:
        if generate_adresse_complete:
            # Get the address in a unique field, checking for redundancies between the merged fields
            df[address + "_adresse_complete"] = df.apply(
                lambda row: get_address(row, address, "_clean"), axis=1
            ).apply(lambda x: re.sub(" +", " ", x))
            # Get the complete address + postal code + city, for a "really complete" address
            df[address + "_adresse_tres_complete"] = df[
                [
                    address + field
                    for field in ["_adresse_complete", "_cp_clean", "_commune_clean"]
                ]
            ].agg(" ".join, axis=1)
            # Check if there were redundancies or not when merging the columns to get the full address
            df[address + "_flag_aggregation"] = (
                df[[address + "_" + field + "_clean" for field in fields_to_check]]
                .agg(" ".join, axis=1)
                .apply(lambda x: re.sub(" +", " ", x).strip())
                != df[address + "_adresse_complete"]
            )
        else:
            df[address + "_adresse_complete"] = ""
            df[address + "_adresse_tres_complete"] = ""
            df[address + "_flag_aggregation"] = False
    print("Get full addresses: OK")

    return df  # The dataset is clean!


def requires_anonymization(
    x, tuple_all_variantes_chez, str_variantes_chez, str_all_patterns
) -> int:
    """
    Takes a string as input and checks if it requires an anonymization or not, by looking for some key words

    Args:
        x:
        tuple_all_variantes_chez:
        str_variantes_chez:
        str_all_patterns:

    Returns:

    """
    # x = str(x)
    if x.startswith(tuple_all_variantes_chez) or re.search(str_variantes_chez, x):
        return 2  # 2 means "Needs anonymization"

    if re.search(str_all_patterns, " " + x):
        return 1  # 1 means "Will not go through the anonymization process but is still suspicious"

    return 0  # 0 means "No anonymization required, we are safe"


def remove_names(
    x,
    liste_variantes_chez,
    liste_all_variantes_chez,
    str_all_variantes_chez,
    okay_words_before_chez,
    okay_words_after_chez,
    str_streets,
) -> str:
    """
    This function removes all nominative information from the dataset

    Args:
        liste_all_variantes_chez:
        liste_variantes_chez:
        str_all_variantes_chez:
        okay_words_before_chez:
        okay_words_after_chez:
        str_streets:
        x (str): a string  possibly containing names, following the conditions above

    Returns:
        str: a string where names have been removed
    """
    # x = str(x)
    if x in ["nan", "none", ""]:
        return ""

    if not re.search(str_all_variantes_chez, " " + x):
        return x

    # We need to find which variation of "chez" is present
    trouve = False
    for variante_chez in liste_all_variantes_chez:
        if x.startswith(variante_chez + " ") or re.search(
            "|".join([space + variante_chez + " " for space in [" ", "-"]]), x
        ):
            chez = variante_chez
            if " " + chez + " " in " " + x:
                space = " "
            else:
                space = "-"
            trouve = True
            break

    if not trouve:
        return (
            x  # If no variation of "chez" is found, but should not happen in practice
        )

    str_okay_expressions = "|".join(
        [" " + word + " " + chez + " " for word in okay_words_before_chez]
        + [space + chez + " " + word + " " for word in okay_words_after_chez]
    )

    if re.search(str_okay_expressions, " " + x + " "):
        return x  # If our allowed words before or after "chez" are detected, pass

    adr = (" " + x).split(space + chez + " ")[
        0
    ].strip() + " "  # What is before the "chez"
    after_chez = " ".join(
        (" " + x).split(space + chez + " ")[1:]
    )  # What is after the "chez"
    to_parse = after_chez.split(
        " "
    )  # What is after the "chez" but split into a list of words

    if (
        chez in liste_variantes_chez
        and len(
            [
                word
                for word in to_parse
                if not word.isnumeric() and (len(word) > 1 or word == "m")
            ]
        )
        <= 1
    ):
        # "Chez xxx", with xxx in one word, is generally a restaurant or other place's name, so pass
        return x

    if (
        len(to_parse[0]) > 1 and to_parse[0][1] == "'"
    ):  # ie if "chez" is followed by "d'" or "l'"
        return x

    if "-" in to_parse:
        # We are looking for a " - ", that represents the separation of two distinct pieces of info
        adr = adr + after_chez[after_chez.find("- ") :]
    elif bool(re.search(r"(?<!\d)\d{1,4}(?!\d)", after_chez)):
        # Numbers generally refer to the beginning of an address complement
        adr = adr + after_chez[re.search(r"(?<!\d)\d{1,4}(?!\d)", after_chez).start() :]
    elif bool(re.search(r"\d{5,}", after_chez)):
        # In this situation, 5-digits numbers or more generally refer to postal codes that we will remove
        adr = adr + after_chez[: re.search(r"\d{5,}", after_chez).start()]
    elif re.search(str_streets, " " + after_chez):
        # If a street type is detected, we want to keep the street name
        street = re.search(str_streets, " " + after_chez).group(0)[1:-1]
        adr = (
            adr
            + street
            + " "
            + " ".join((" " + after_chez).split(" " + street + " ")[1:])
        )

    if adr in ["nan", "none"] or len(adr) < 1:
        return ""
    while len(adr) > 0 and adr[-1] in ["-", " "]:
        adr = adr[:-1]
    return adr


def requires_cleaning(x, str_specifications) -> int:
    """
    Are there any extra specifications or postal codes that should be removed?

    Args:
        x:
        str_specifications:

    Returns:

    """
    # x = str(x)

    if re.search(str_specifications, " " + x + " ") or (
        not x.isnumeric() and bool(re.search(r"\d{5,}", x))
    ):
        return 1  # 1 means "Requires cleaning"

    return 0  # 0 means "Does not require cleaning"


def remove_specifications(
    x,
    liste_specifications,
    str_specifications,
    okay_words_before_chez,
    okay_words_after_chez,
) -> str:
    """
    Removes as much as possible of the extra spceifications (buildings, stairs, ...) and postal codes
    The function is not exhaustive, but we prefer keep superfluous specifications than removing
    street names that are not problematic

    Args:
        x:
        liste_specifications:
        str_specifications:
        okay_words_before_chez:
        okay_words_after_chez:

    Returns:

    """

    # x = str(x)

    def aux_remove_specifications(sentence):
        # Looks for one specification to remove, and if one is found removes it
        trouve = False
        for variante_specification in liste_specifications:
            if sentence.startswith(variante_specification + " ") or re.search(
                "|".join(
                    [space + variante_specification + " " for space in [" ", "-"]]
                ),
                sentence + " ",
            ):
                specification = variante_specification
                if (" " + specification + " ") in (" " + sentence + " "):
                    space = " "
                else:
                    space = "-"
                trouve = True
                break

        if not trouve:
            return sentence

        str_okay_expressions = "|".join(
            [
                " " + word + " " + specification + " "
                for word in okay_words_before_chez
            ]  # +
            # [space + specification + " " + word + " " for word in okay_words_after_chez]
        )
        # Is the specification preceded by a word than would exonerate it (ex: a street type or a pronoun)
        if re.search(str_okay_expressions, " " + sentence + " "):
            return sentence

        adr = (" " + sentence + " ").split(space + specification + " ")[
            0
        ].strip() + " "  # What is before the spec
        after_specification = " ".join(
            (" " + sentence + " ")
            .replace("-", " ")
            .split(" " + specification + " ")[1:]
        ).strip()  # What is after
        to_parse = after_specification.split(
            " "
        )  # What is after, but split in a list of words
        #  We will delete everything in the post-spec part until we find a word of at least 3 letters or a -
        for i in range(len(to_parse)):
            if (
                not bool(re.search(r"\d", to_parse[i])) and len(to_parse[i]) >= 3
            ) or to_parse[i] == "-":
                return adr + " ".join(to_parse[i:])

        return adr

    compteur = 0
    while re.search(str_specifications, " " + x + " "):
        # We can try and remove up to 3 specifications, then drop it (let's avoid infinite loops)
        if compteur > 3:
            break
        x = aux_remove_specifications(x)
        compteur += 1

    # Remove postal codes if the length of the string is big enough
    if len(x) > 10 and bool(re.search(r"\d{5,}", x)):
        x = x[: re.search(r"\d{5,}", x).start()]

    if x in ["nan", "none"] or len(x) < 1:
        return ""
    while len(x) > 0 and x[-1] in ["-", " "]:
        x = x[:-1]
    return x


def clear_num_voie(x):
    # For street numbers, only keep numbers possibly followed by 1 letter or bis/ter
    if x.isnumeric() or x == "":
        return x
    if not bool(re.search(r"\d+", x)):
        return ""
    number = re.search(r"\d+", x).group()
    word = x[re.search(r"\d+", x).end() :].replace("-", " ").strip()
    if len(word) == 1 or word in ["bis", "ter", "quater"]:
        return number + " " + word
    return number


def complete_postal_code(x):
    # The result shall be a 5-digits postal code
    x = str(x or "").strip()
    while len(x) > 0 and x[0] in ["-", "o"]:
        x = x[1:]
    nb_digits = min(len(x), 5)
    return ((5 - nb_digits) * "0" + x)[:5]


def get_departement(row, adresse):
    """
    From the postal_codes, retrieve the departement if we are in France. Otherwise, returns 99

    Args:
        row:
        adresse:

    Returns:

    """
    liste_france = ["france", "", "fr", "fra"]  # List of variations for "France"
    if (
        len(row["code_commune_ref"]) == 5
        or row[adresse + "_" + "pays"].strip() in liste_france
        or row[adresse + "_" + "pays"].strip()[:-1] == "franc"
    ):
        return row[adresse + "_" + "cp_clean"][:2]
    return "99"


def get_address(row, adresse, suffix) -> str:
    """
    Build a unique address string by combining several fields

    Args:
        suffix:
        row : a row of pd.DataFrame
        adresse : 'r' or 'c', depending on if we deal with adresses de rattachement ou de contact

    Returns:
        str: the address
    """

    address = (
        row[adresse + "_" + "num_voie" + suffix]
        + " "
        + row[adresse + "_" + "voie" + suffix].strip()
    )
    if len(address) < 5:
        address = ""

    complements = row[adresse + "_" + "all_complements" + suffix].strip()
    if (
        len(complements) >= 5
        and complements not in address
        and (len(address) < 5 or address not in complements)
    ):
        address += " " + complements

    lieu_dit = row[adresse + "_" + "lieu_dit" + suffix]
    if (
        len(lieu_dit) >= 5
        and lieu_dit not in address
        and (len(address) < 5 or address not in lieu_dit)
    ):
        address += " " + lieu_dit

    return address.strip()
