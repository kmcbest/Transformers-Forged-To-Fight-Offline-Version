import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle")

for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        if data.m_Name in ("move_heavy_megatron_gs_shoot", "move_heavy_ramjet_donut"):
            print(f"=== {data.m_Name} ===")
            text = data.m_Script
            print(text[:500])
            print("...\n")
