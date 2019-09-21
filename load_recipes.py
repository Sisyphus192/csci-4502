
from ingredient_parser import parse

import pandas as pd

df = pd.read_json("recipes_raw_nosource_ar.json")
df = df.transpose()
cnt = 0
for index, row in df.iterrows():
    for i in row["ingredients"]:
        print(i)
    cnt+=1
    if cnt > 3:
        break
