import sys
sys.path.insert(0, "Server")
import gamedata

mods = gamedata._load_mods()
mod_map = {m["id"]: m for m in mods}

towers = [
    "mods_laserguidance_01",
    "mods_harmaccelerator_01",
    "mods_strangerefractor_01",
    "mods_primemodule_01",
    "mods_superconductor_01",
    "mods_tacticianstrick_02",
    "mods_immobilizer_01",
    "mods_brawlersfury_01",
]

for tid in towers:
    if tid in mod_map:
        print(f"OK tower: {tid} -> {mod_map[tid].get('model_id')}")
    else:
        print(f"MISSING tower: {tid}")
