#!/usr/bin/env python3
"""Set up gacha definitions in account data JSON files based on TFTF 2.0.2 whitebox C# specifications."""

import json
from pathlib import Path

def get_boxes():
    return [
        {
            "name": "crystal_uber_01",
            "group": "base",
            "set": "base",
            "version": "1.0",
            "displayname": "高级水晶",
            "desc": "包含 2星至 4星 变形金刚汽车人与霸天虎",
            "token": "crystal_uber_01",
            "tokenmdl": "crystal_uber_01",
            "tokenimg": "gacha/crystals/crystal_uber_bot",
            "closedimg": "gacha/crystals/crystal_uber_bot",
            "openimg": "gacha/crystals/crystal_uber_bot",
            "bg": "gacha/banners/MOTDL_24HrCrystal",
            "tokenc": {"cost": 1},
            "vinb": True,
            "caren": True,
            "carcount": 10,
            "end": 2147483647,
            "ppl": ["cat_bots"],
            "featured": [
                {"type": "hero", "data": "optimusprime_cin_tf", "quantity": 1},
                {"type": "hero", "data": "megatron_gs_leader2015", "quantity": 1},
                {"type": "hero", "data": "bumblebee_cin_dotm", "quantity": 1}
            ],
            "gamespecific": {"tab": "Crystals"}
        },
        {
            "name": "crystal_generations",
            "group": "base",
            "set": "base",
            "version": "1.0",
            "displayname": "经典水晶",
            "desc": "包含 2星至 4星 G1经典变形金刚",
            "token": "crystal_generations",
            "tokenmdl": "crystal_generations",
            "tokenimg": "gacha/crystals/crystal_generation",
            "closedimg": "gacha/crystals/crystal_generation",
            "openimg": "gacha/crystals/crystal_generation",
            "bg": "gacha/banners/CrystalGen_placeholder",
            "tokenc": {"cost": 1},
            "vinb": True,
            "caren": True,
            "carcount": 10,
            "end": 2147483647,
            "ppl": ["cat_bots"],
            "featured": [
                {"type": "hero", "data": "grimlock_gs_mp08", "quantity": 1},
                {"type": "hero", "data": "starscream_gs", "quantity": 1}
            ],
            "gamespecific": {"tab": "Crystals"}
        },
        {
            "name": "crystal_spec_01",
            "group": "base",
            "set": "base",
            "version": "1.0",
            "displayname": "特别水晶",
            "desc": "包含 3星至 5星 特别典藏变形金刚",
            "token": "crystal_spec_01",
            "tokenmdl": "crystal_spec_01",
            "tokenimg": "gacha/crystals/crystal_spec_bot_premium",
            "closedimg": "gacha/crystals/crystal_spec_bot_premium",
            "openimg": "gacha/crystals/crystal_spec_bot_premium",
            "bg": "gacha/banners/CrystalGen_placeholder",
            "tokenc": {"cost": 1},
            "vinb": True,
            "caren": True,
            "carcount": 10,
            "end": 2147483647,
            "ppl": ["cat_bots"],
            "featured": [
                {"type": "hero", "data": "windblade_gs", "quantity": 1},
                {"type": "hero", "data": "drift_cin_aoe", "quantity": 1}
            ],
            "gamespecific": {"tab": "Crystals"}
        },
        {
            "name": "crystal_shards_premium",
            "group": "base",
            "set": "base",
            "version": "1.0",
            "displayname": "高级碎片水晶",
            "desc": "收集 2000 个碎片兑换一个高级水晶",
            "token": "crystal_shards_premium",
            "tokenmdl": "crystal_uber_01",
            "tokenimg": "gacha/crystals/crystal_uber_bot",
            "closedimg": "gacha/crystals/crystal_uber_bot",
            "openimg": "gacha/crystals/crystal_uber_bot",
            "bg": "gacha/banners/MOTDL_24HrCrystal",
            "fragmentname": "高级水晶碎片",
            "fragmentimg": "gacha/crystals/crystal_uber_bot",
            "tokenc": {"cost": 1},
            "vinb": True,
            "caren": False,
            "carcount": 1,
            "end": 2147483647,
            "ppl": ["cat_bots"],
            "featured": [
                {"type": "hero", "data": "optimusprime_cin_tf", "quantity": 1}
            ],
            "gamespecific": {"tab": "Shards"}
        },
        {
            "name": "crystal_shards_3star",
            "group": "base",
            "set": "base",
            "version": "1.0",
            "displayname": "三星碎片水晶",
            "desc": "收集 1000 个碎片兑换一个三星水晶",
            "token": "crystal_shards_3star",
            "tokenmdl": "crystal_generations",
            "tokenimg": "gacha/crystals/crystal_spec_bot_3star",
            "closedimg": "gacha/crystals/crystal_spec_bot_3star",
            "openimg": "gacha/crystals/crystal_spec_bot_3star",
            "bg": "gacha/banners/CrystalGen_placeholder",
            "fragmentname": "三星水晶碎片",
            "fragmentimg": "gacha/crystals/crystal_spec_bot_3star",
            "tokenc": {"cost": 1},
            "vinb": True,
            "caren": False,
            "carcount": 1,
            "end": 2147483647,
            "ppl": ["cat_bots"],
            "featured": [
                {"type": "hero", "data": "grimlock_gs_mp08", "quantity": 1}
            ],
            "gamespecific": {"tab": "Shards"}
        }
    ]

def get_gacha_data():
    boxes = get_boxes()
    return {
        "check": "gacha_offline_v1",
        "refresh": 2147483647,
        "cache": False,
        "gacha": {
            "groups": [
                {
                    "group": "base",
                    "set": {
                        "name": "base",
                        "version": "1.0",
                        "boxes": boxes
                    }
                },
                {
                    "group": "tutorial",
                    "set": {
                        "name": "tutorial",
                        "version": "1.0",
                        "boxes": boxes
                    }
                }
            ],
            "categories": {
                "CRYSTAL": {"name": "CRYSTAL"},
                "SHARDS": {"name": "SHARDS"},
                "cat_bots": {
                    "name": "cat_bots",
                    "items": [
                        {"type": "hero", "data": "optimusprime_cin_tf", "quantity": 1},
                        {"type": "hero", "data": "megatron_gs_leader2015", "quantity": 1},
                        {"type": "hero", "data": "bumblebee_cin_dotm", "quantity": 1},
                        {"type": "hero", "data": "grimlock_gs_mp08", "quantity": 1},
                        {"type": "hero", "data": "windblade_gs", "quantity": 1},
                        {"type": "hero", "data": "drift_cin_aoe", "quantity": 1}
                    ]
                }
            },
            "tokens": [
                {"token": "crystal_uber_01", "name": "crystal_uber_01", "count": 999},
                {"token": "crystal_generations", "name": "crystal_generations", "count": 999},
                {"token": "crystal_spec_01", "name": "crystal_spec_01", "count": 999},
                {"token": "crystal_shards_premium", "name": "crystal_shards_premium", "count": 999},
                {"token": "crystal_shards_3star", "name": "crystal_shards_3star", "count": 999}
            ],
            "fragments": [
                {"token": "crystal_shards_premium", "name": "crystal_shards_premium", "count": 2000},
                {"token": "crystal_shards_3star", "name": "crystal_shards_3star", "count": 1000}
            ],
            "maxspins": 10
        }
    }

def main():
    gacha_data = get_gacha_data()
    targets = [
        Path(r"e:\Agent\TFTF\Server\responses\GET__account_data.json"),
        Path(r"e:\Agent\TFTF\Server\responses\POST__account_data.json")
    ]
    for tf in targets:
        if not tf.exists():
            print(f"Target {tf} not found, skipping")
            continue
        data = json.loads(tf.read_text(encoding="utf-8"))
        if "result" in data:
            data["result"]["gacha"] = gacha_data
        tf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Successfully configured gacha in {tf.name}")

if __name__ == "__main__":
    main()
