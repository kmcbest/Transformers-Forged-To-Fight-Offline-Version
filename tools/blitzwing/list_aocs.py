import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        print(f"AOC: {tree.get('m_Name')} (PID: {obj.path_id})")
