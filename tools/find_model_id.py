# -*- coding: utf-8 -*-
import sys
import glob

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob("Server/*.py"):
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        for i, line in enumerate(fp):
            if any(k in line for k in ['"mdl"', "'mdl'", '"model"', "'model'", 'ModelID', 'getBaseHeroData', 'bot_id']):
                if any(x in line for x in ['optimus', 'ironhide', 'demolishor', 'star_saber', 'deadend']):
                    print(f"{f}:{i+1}: {line.strip()}")
