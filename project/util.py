"""
This module contains a variety of utility functions as well as lookup lists and
tables. Some code adapted from https://github.com/kbrohkahn/recipe-parser.
"""

import re


def equal_checking_plurals(string, plural_string):
    """
    Checks whether the first argument is the same word as a plural string, checking plurals
    """
    # only check plurals if first 3 letters match
    if string[0] != plural_string[0]:
        return None

    if len(string) > 1 and len(plural_string) > 1 and string[1] != plural_string[1]:
        return None

    if len(string) > 2 and len(plural_string) > 2 and string[2] != plural_string[2]:
        return None

    # check all possible plurals of string
    if plural_string in [
        string,
        string + "s",
        string + "es",
        string + "es",
        string[:-1] + "ies",
        string[:-1] + "ves",
    ]:
        return plural_string

    return None


def in_checking_plurals(string, plural_list):
    """
    Checks whether the first argument matches a string in a list of plurals, checking plurals
    """
    for plural_string in plural_list:
        if equal_checking_plurals(string, plural_string):
            return plural_string

    return None


def is_number(string):
    """
    Checks if argument is a number or not, because python's builtin
    .isnumeric() does not identify floats
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


# transform amount to cups based on amount and original unit
def transformToCups(amount, unit):
    if unit == "cups":
        return amount
    elif unit == "quarts":
        return amount / 16
    elif unit == "quarts":
        return amount / 4
    elif unit == "pints":
        return amount / 2
    elif unit == "ounces":
        return amount * 8
    elif unit == "tablespoons":
        return amount * 16
    elif unit == "teaspoons":
        return amount * 48
    else:
        return amount


def is_seperator(ingredient_string):
    return (
        ingredient_string.find("For ") == 0
        or " " not in ingredient_string
        or (":" in ingredient_string and "eg:" not in ingredient_string)
    )


def get_ingredient_amount(parsed_ingredient, ingredient):
    ingredient["amount"] = 0
    while parsed_ingredient:
        # check if current word is number of inches, not amount
        if len(parsed_ingredient) > 1 and parsed_ingredient[1] == "inch":
            break

        # get first word

        # if first word is digit or fraction, eval
        # "x" not multiplier, "%" used as modulo
        try:
            ingredient["amount"] += eval(parsed_ingredient[0])
            del parsed_ingredient[0]
        except (SyntaxError, NameError, TypeError):
            break
    return ingredient, parsed_ingredient


def get_ingredient_unit(parsed_ingredient, ingredient):
    # check words for unit
    unit_string = ""
    for i in range(0, len(parsed_ingredient)):
        plural_unit = in_checking_plurals(parsed_ingredient[i], MEASUREMENT_UNITS)
        if plural_unit:
            unit_string = plural_unit
            del parsed_ingredient[i]

            if i < len(parsed_ingredient) and parsed_ingredient[i] == "+":
                while "+" in parsed_ingredient:
                    index = parsed_ingredient.index("+")
                    del parsed_ingredient[index]
                    ingredient["amount"] += transformToCups(
                        eval(parsed_ingredient[index]), parsed_ingredient[index + 1]
                    )
                    del parsed_ingredient[index]
                    del parsed_ingredient[index + 1]

            break

    # check for "cake" as unit, but only if "yeast" somewhere in ingredient
    if "yeast" in parsed_ingredient:
        for word in parsed_ingredient:
            if equal_checking_plurals(word, "cakes"):
                unit_string = "cakes"
                parsed_ingredient.remove(word)
                break

    try:
        # check if first word in array is "or", then ingredient has 2 possible units
        if parsed_ingredient[0] == "or":
            plural_unit = in_checking_plurals(parsed_ingredient[1], MEASUREMENT_UNITS)
            if plural_unit:
                unit_string += " " + parsed_ingredient[0] + " " + plural_unit
                parsed_ingredient = parsed_ingredient[2:]
    except IndexError:
        print("Parsing error with: ", ingredient["index"], ingredient["title"])
        return ingredient, parsed_ingredient

    # delete "of" at first index, ie "1 cup of milk" -> "1 cup milk"
    if parsed_ingredient[0] == "of":
        del parsed_ingredient[0]

    ingredient["unit"] = unit_string
    return ingredient, parsed_ingredient


def get_ingredient_descriptions(parsed_ingredient, ingredient):
    # remove useless words
    for word in parsed_ingredient:
        if word in UNNECESSARY_DESCRIPTIONS:
            parsed_ingredient.remove(word)

    index = 0
    while index < len(parsed_ingredient):
        description_string = ""
        word = parsed_ingredient[index]

        # search through descriptions (adjectives)
        if word in DESCRIPTIONS:
            description_string = word

            # check previous word
            if index > 0:
                previous_word = parsed_ingredient[index - 1]
                if previous_word in PRECEDING_ADVERBS or previous_word[-2:] == "ly":
                    description_string = previous_word + " " + word
                    parsed_ingredient.remove(previous_word)

            # check next word
            elif index + 1 < len(parsed_ingredient):
                next_word = parsed_ingredient[index + 1]
                if next_word in SUCCEEDING_ADVERBS or next_word[-2:] == "ly":
                    description_string = word + " " + next_word
                    parsed_ingredient.remove(next_word)

        # word not in descriptions, check if description with predecessor
        elif word in DESCRIPTIONS_WITH_PREDECESSOR and index > 0:
            description_string = parsed_ingredient[index - 1] + " " + word
            del parsed_ingredient[index - 1]

        # either add description string to descriptions or check next word
        if description_string == "":
            index += 1
        else:
            ingredient["descriptions"].append(description_string)
            parsed_ingredient.remove(word)

    # remove "and"
    while "and" in parsed_ingredient:
        parsed_ingredient.remove("and")

    # remove "style"
    while "style" in parsed_ingredient:
        parsed_ingredient.remove("style")

    try:
        # remove "or" if last word
        if parsed_ingredient[-1] == "or":
            del parsed_ingredient[-1]
    except IndexError:
        print("Parsing error with: ", ingredient["index"], ingredient["title"])
        return ingredient, parsed_ingredient
    # replace hyphenated prefixes and suffixes
    for word in parsed_ingredient:
        for hypenated_suffix in HYPENATED_SUFFIXES:
            if hypenated_suffix in word:
                word = word.replace(hypenated_suffix, "-" + hypenated_suffix)

        for hypenated_prefix in HYPENATED_PREFIXES:
            if word.find(hypenated_prefix) == 0:
                word = word.replace(hypenated_prefix, hypenated_prefix + "-")

    # move various nouns to description
    if "powder" in parsed_ingredient and (
        "coffee" in parsed_ingredient
        or "espresso" in parsed_ingredient
        or "tea" in parsed_ingredient
    ):
        parsed_ingredient.remove("powder")
        ingredient["descriptions"].append("unbrewed")

    return ingredient, parsed_ingredient


def get_ingredient(parsed_ingredient, ingredient):
    ingredient_string = " ".join(parsed_ingredient)

    # remove "*", add footnote to description
    if "*" in ingredient_string:
        ingredient["descriptions"].append("* see footnote")
        ingredient_string = ingredient_string.replace("*", "")

    # standardize "-" styling
    ingredient_string = ingredient_string.replace("- ", "-")
    ingredient_string = ingredient_string.replace(" -", "-")
    ingredient_string = ingredient_string.replace("Jell O", "Jell-O")
    ingredient_string = ingredient_string.replace("half half", "half-and-half")

    # remove unnecessary punctuation
    ingredient_string = ingredient_string.replace(".", "")
    ingredient_string = ingredient_string.replace(";", "")

    # fix spelling errors
    ingredient_string = ingredient_string.replace("linguini", "linguine")
    ingredient_string = ingredient_string.replace("filets", "fillets")
    ingredient_string = ingredient_string.replace("chile", "chili")
    ingredient_string = ingredient_string.replace("chiles", "chilis")
    ingredient_string = ingredient_string.replace("chilies", "chilis")
    ingredient_string = ingredient_string.replace("won ton", "wonton")
    ingredient_string = ingredient_string.replace("liquer", "liqueur")
    ingredient_string = ingredient_string.replace("confectioners ", "confectioners' ")
    ingredient_string = ingredient_string.replace("creme de cacao", "chocolate liquer")
    ingredient_string = ingredient_string.replace("pepperjack", "Pepper Jack")
    ingredient_string = ingredient_string.replace("Pepper jack", "Pepper Jack")

    # standardize ingredient styling
    ingredient_string = ingredient_string.replace("dressing mix", "dressing")
    ingredient_string = ingredient_string.replace("salad dressing", "dressing")
    ingredient_string = ingredient_string.replace("bourbon whiskey", "bourbon")
    ingredient_string = ingredient_string.replace("pudding mix", "pudding")

    ingredient["ingredient"] = ingredient_string
    return ingredient


def parse_ingredient_list(recipe_index, recipe_title, ingredient_list):
    if isinstance(ingredient_list, list):
        ingredients = []
        for ingredient_string in ingredient_list:
            # check if not ingredient, but separator
            # e.g. "For Bread:"
            if is_seperator(ingredient_string):
                continue

            ingredient = {}
            ingredient["title"] = recipe_title
            ingredient["descriptions"] = []
            ingredient["index"] = recipe_index

            # remove trademark symbol
            ingredient_string = ingredient_string.replace("\u00ae", "")
            ingredient_string = ingredient_string.replace("(TM)", "")
            ingredient_string = ingredient_string.replace("fluid ounce", "fluid_ounce")

            # move parentheses to description
            while True:
                parentheses = PARENTHESES_REGEX.search(ingredient_string)
                if not parentheses:
                    break
                search_string = parentheses.group()
                ingredient_string = ingredient_string.replace(search_string, "")
                ingredient["descriptions"].append(search_string[1:-1])

            # remove "," and "-" then split ingredient into words
            ingredient_string = ingredient_string.replace(",", " and ")
            ingredient_string = ingredient_string.replace("-", " ")
            parsed_ingredient = ingredient_string.split(" ")

            # remove "", caused by extra spaces
            while "" in parsed_ingredient:
                parsed_ingredient.remove("")

            # move prepositions to description
            for index in range(0, len(parsed_ingredient)):
                if parsed_ingredient[index] in PREPOSITIONS:
                    if (
                        index + 1 < len(parsed_ingredient)
                        and parsed_ingredient[index + 1] == "use"
                    ) or (
                        index > 0
                        and parsed_ingredient[index - 1] == "bone"
                        and parsed_ingredient[index] == "in"
                    ):
                        continue

                    parsed_prepositional_phrase = parsed_ingredient[index:]
                    ingredient["descriptions"].append(
                        " ".join(parsed_prepositional_phrase)
                    )
                    parsed_ingredient = parsed_ingredient[:index]
                    break

            # get ingredient amount
            ingredient, parsed_ingredient = get_ingredient_amount(
                parsed_ingredient, ingredient
            )

            # get ingredient unit
            ingredient, parsed_ingredient = get_ingredient_unit(
                parsed_ingredient, ingredient
            )

            # get ingredient descriptions
            ingredient, parsed_ingredient = get_ingredient_descriptions(
                parsed_ingredient, ingredient
            )

            # get ingredient
            ingredient = get_ingredient(parsed_ingredient, ingredient)
            ingredients.append(ingredient)
        return ingredients
    else:
        return recipe_index, recipe_title, None


# LOOKUP TALBES:

# list of measurement units for parsing ingredient, these are always plurals
MEASUREMENT_UNITS = [
    "teaspoons",
    "dessertspoons",
    "tablespoons",
    "fluid_ounces",
    "cups",
    "pints",
    "quarts",
    "gallons",
    "milligrams",
    "grams",
    "kilograms",
    "milliliters",
    "liters",
    "containers",
    "packets",
    "bags",
    "pounds",
    "cans",
    "bottles",
    "cloves",
    "packages",
    "ounces",
    "jars",
    "heads",
    "drops",
    "envelopes",
    "bars",
    "boxes",
    "pinches",
    "dashes",
    "bunches",
    "recipes",
    "layers",
    "slices",
    "links",
    "bulbs",
    "stalks",
    "squares",
    "sprigs",
    "fillets",
    "pieces",
    "legs",
    "thighs",
    "cubes",
    "granules",
    "strips",
    "trays",
    "leaves",
    "loaves",
    "halves",
    "scoops",
    "inches",
]

# Dict to lookup common abreviations of measurements
UNIT_ABREVIATIONS = {
    "cup": ["cups", "cup", "c.", "c"],
    "fluid_ounce": ["fl. oz.", "fl oz", "fluid ounce", "fluid ounces"],
    "gallon": ["gal", "gal.", "gallon", "gallons"],
    "ounce": ["oz", "oz.", "ounce", "ounces"],
    "pint": ["pt", "pt.", "pint", "pints"],
    "pound": ["lb", "lb.", "pound", "pounds"],
    "quart": ["qt", "qt.", "qts", "qts.", "quart", "quarts"],
    "tablespoon": [
        "tbsp.",
        "tbsp",
        "T",
        "T.",
        "tablespoon",
        "tablespoons",
        "tbs.",
        "tbs",
    ],
    "teaspoon": ["tsp.", "tsp", "t", "t.", "teaspoon", "teaspoons"],
    "gram": ["g", "g.", "gr", "gr.", "gram", "grams"],
    "kilogram": ["kg", "kg.", "kilogram", "kilograms"],
    "liter": ["l", "l.", "liter", "liters"],
    "milligram": ["mg", "mg.", "milligram", "milligrams"],
    "milliliter": ["ml", "ml.", "milliliter", "milliliters"],
}

CONTAINERS = [
    "cans",
    "packages",
    "boxes",
    "containers",
    "jars",
    "bags",
    "cans or bottles",
    "scoops",
    "bottles",
    "fillets",
    "envelopes",
    "bags",
    "heads",
    "bunches",
    "slices",
    "loaves",
    "bars",
    "packets",
    "squares",
    "links",
]


# strings indicating ingredient as optional
OPTIONAL_STRINGS = ["optional", "to taste", "as needed", "if desired"]

# list of adjectives and participles used to describe ingredients
DESCRIPTIONS = [
    "baked",
    "beaten",
    "blanched",
    "boiled",
    "boiling",
    "boned",
    "breaded",
    "brewed",
    "broken",
    "chilled",
    "chopped",
    "cleaned",
    "coarse",
    "cold",
    "cooked",
    "cool",
    "cooled",
    "cored",
    "creamed",
    "crisp",
    "crumbled",
    "crushed",
    "cubed",
    "cut",
    "deboned",
    "deseeded",
    "diced",
    "dissolved",
    "divided",
    "drained",
    "dried",
    "dry",
    "fine",
    "firm",
    "fluid",
    "fresh",
    "frozen",
    "grated",
    "grilled",
    "ground",
    "halved",
    "hard",
    "hardened",
    "heated",
    "heavy",
    "juiced",
    "julienned",
    "jumbo",
    "large",
    "lean",
    "light",
    "lukewarm",
    "marinated",
    "mashed",
    "medium",
    "melted",
    "minced",
    "near",
    "opened",
    "optional",
    "packed",
    "peeled",
    "pitted",
    "popped",
    "pounded",
    "prepared",
    "pressed",
    "pureed",
    "quartered",
    "refrigerated",
    "rinsed",
    "ripe",
    "roasted",
    "roasted",
    "rolled",
    "rough",
    "scalded",
    "scrubbed",
    "seasoned",
    "seeded",
    "segmented",
    "separated",
    "shredded",
    "sifted",
    "skinless",
    "boneless",
    "sliced",
    "slight",
    "slivered",
    "small",
    "soaked",
    "soft",
    "softened",
    "split",
    "squeezed",
    "stemmed",
    "stewed",
    "stiff",
    "strained",
    "strong",
    "thawed",
    "thick",
    "thin",
    "tied",
    "toasted",
    "torn",
    "trimmed",
    "wrapped",
    "vained",
    "warm",
    "washed",
    "weak",
    "zested",
    "wedged",
    "skinned",
    "gutted",
    "browned",
    "patted",
    "raw",
    "flaked",
    "deveined",
    "shelled",
    "shucked",
    "crumbs",
    "halves",
    "squares",
    "zest",
    "peel",
    "uncooked",
    "butterflied",
    "unwrapped",
    "unbaked",
    "warmed",
]

# list of adverbs used before or after description
PRECEDING_ADVERBS = ["well", "very", "super"]
SUCCEEDING_ADVERBS = ["diagonally", "lengthwise", "overnight"]

# list of prepositions used after ingredient name
PREPOSITIONS = [
    "as",
    "such",
    "for",
    "with",
    "without",
    "if",
    "about",
    "e.g.",
    "in",
    "into",
    "at",
    "until",
]

# only used as <something> removed, <something> reserved, <x> inches, <x> old, <some> temperature
DESCRIPTIONS_WITH_PREDECESSOR = [
    "removed",
    "discarded",
    "reserved",
    "included",
    "inch",
    "inches",
    "old",
    "temperature",
    "up",
]

# descriptions that can be removed from ingredient, i.e. candied pineapple chunks
UNNECESSARY_DESCRIPTIONS = ["chunks", "pieces", "rings", "spears"]

# list of prefixes and suffixes that should be hyphenated
HYPENATED_PREFIXES = ["non", "reduced", "semi", "low"]
HYPENATED_SUFFIXES = ["coated", "free", "flavored"]

PARENTHESES_REGEX = re.compile(r"\([^()]*\)")

