import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path

gamedata_path = Path(r"E:\Agent\TFTF-blender\Server\gamedata.py")
with open(gamedata_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. BASE_ROSTER
target_1 = '"starsaber_gs_leader2014":      ("autobot",    "tact", 5),'
insert_1 = target_1 + '\n    "swoop_gs_deluxe2008":          ("autobot",    "tech", 5),'
assert target_1 in content, "target_1 not found in gamedata.py"
if '"swoop_gs_deluxe2008":          ("autobot",    "tech", 5),' not in content:
    content = content.replace(target_1, insert_1)
    print("1. Added swoop_gs_deluxe2008 to BASE_ROSTER")

# 2. BASE_STATS
target_2 = '"starsaber_gs_leader2014": (37900, 2775),'
insert_2 = target_2 + '\n    "swoop_gs_deluxe2008": (39200, 2980),'
assert target_2 in content, "target_2 not found in gamedata.py"
if '"swoop_gs_deluxe2008": (39200, 2980),' not in content:
    content = content.replace(target_2, insert_2)
    print("2. Added swoop_gs_deluxe2008 to BASE_STATS")

# 3. MODEL_MAPPING
target_3 = '"starsaber_gs_leader2014": "starsaber",'
insert_3 = target_3 + '\n    "swoop_gs_deluxe2008": "swoop",'
assert target_3 in content, "target_3 not found in gamedata.py"
if '"swoop_gs_deluxe2008": "swoop",' not in content:
    content = content.replace(target_3, insert_3)
    print("3. Added swoop_gs_deluxe2008 to MODEL_MAPPING")

# 4. DISPLAY_NAMES
target_4 = '"starsaber_gs_leader2014": "Star Saber",'
insert_4 = target_4 + '\n    "swoop_gs_deluxe2008": "Swoop",'
assert target_4 in content, "target_4 not found in gamedata.py"
if '"swoop_gs_deluxe2008": "Swoop",' not in content:
    content = content.replace(target_4, insert_4)
    print("4. Added swoop_gs_deluxe2008 to DISPLAY_NAMES")

# 5. ROSTER_BY_CLASS: Tech class
target_5 = '"shockwave_gs",\n    ],'
insert_5 = '"shockwave_gs",\n        "swoop_gs_deluxe2008",\n    ],'
assert target_5 in content, "target_5 not found in gamedata.py"
if '"swoop_gs_deluxe2008",\n    ],' not in content:
    content = content.replace(target_5, insert_5)
    print("5. Added swoop_gs_deluxe2008 to ROSTER_BY_CLASS Tech")

with open(gamedata_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated Server/gamedata.py successfully!")
