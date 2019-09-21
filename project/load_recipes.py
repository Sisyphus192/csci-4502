from collections import Counter
import pandas as pd
import numpy as np
import re
import string

UNITS = {"cup": ["cups", "cup", "c.", "c"], "fluid_ounce": ["fl. oz.", "fl oz", "fluid ounce", "fluid ounces"],
         "gallon": ["gal", "gal.", "gallon", "gallons"], "ounce": ["oz", "oz.", "ounce", "ounces"],
         "pint": ["pt", "pt.", "pint", "pints"], "pound": ["lb", "lb.", "pound", "pounds"],
         "quart": ["qt", "qt.", "qts", "qts.", "quart", "quarts"],
         "tablespoon": ["tbsp.", "tbsp", "T", "T.", "tablespoon", "tablespoons", "tbs.", "tbs"],
         "teaspoon": ["tsp.", "tsp", "t", "t.", "teaspoon", "teaspoons"],
         "gram": ["g", "g.", "gr", "gr.", "gram", "grams"], "kilogram": ["kg", "kg.", "kilogram", "kilograms"],
         "liter": ["l", "l.", "liter", "liters"], "milligram": ["mg", "mg.", "milligram", "milligrams"],
         "milliliter": ["ml", "ml.", "milliliter", "milliliters"], "pinch": ["pinch", "pinches"],
         "dash": ["dash", "dashes"], "touch": ["touch", "touches"], "handful": ["handful", "handfuls"],
         "stick": ["stick", "sticks"], "clove": ["cloves", "clove"], "can": ["cans", "can"], "large": ["large"],
         "small": ["small"], "scoop": ["scoop", "scoops"], "filets": ["filet", "filets"], "sprig": ["sprigs", "sprig"]}
units = [item for sublist in UNITS.values() for item in sublist]

counts = []
df = pd.read_json("recipes_raw_nosource_ar.json")


df = df.transpose()
print(df.head())
"""
cnt = 0
for index, row in df.iterrows():
    #print(row["ingredients"])
    if isinstance(row["ingredients"], list):
        for i in row["ingredients"]:
            words = i.lower()
            words = words.replace("\u00ae", "")
            groups = re.search(r"([0-9]+)\s\(([0-9a-zA-Z\s]+)\)", words)
            if groups is not None:
                new_amount = groups.group(2).split()
                print(words)
                words = re.sub(r"[0-9]+\s\([0-9a-zA-Z\s]+\)", "{} {}".format(int(groups.group(1))*int(new_amount[0]), new_amount[1]), words)
                print(words)
            words = words.split()
            for idx, j in enumerate(words):
                if re.match(r"[0-9\/]+", j):
                    j = "#AMOUNT"
                if idx >= len(counts):
                    counts.append(Counter([j]))
                else:
                    counts[idx].update([j])


for idx, i in enumerate(counts):
    with open("counts_{}.txt".format(idx), "w+") as f:
        for k, v in i.most_common():
            f.write("{} {}\n".format(k,v))

"""
