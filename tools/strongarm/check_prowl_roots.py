import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

prowl_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(prowl_bundle))

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        for c in tree.get("m_Container", []):
            print(f"Container: {c[0]} -> PID {c[1].get('asset', {}).get('m_PathID')}")

for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        # Find if it's a root
        parent_tr = None
        for comp in tree.get("m_Components", []):
            comp_id = comp.get("component", {}).get("m_PathID")
            # We'll check transforms later
        name = tree.get("m_Name", "")
        if "prowl" in name.lower():
            print(f"GO PID {obj.path_id}: '{name}'")
