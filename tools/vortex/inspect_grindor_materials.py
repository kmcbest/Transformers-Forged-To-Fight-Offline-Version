import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

print("=== Materials in Grindor Bundle ===")
for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        print(f"Material PID={obj.path_id}: '{name}'")
        for k, v in tree.get("m_SavedProperties", {}).get("m_TexEnvs", []):
            tex_pid = v.get("m_Texture", {}).get("m_PathID")
            scale = v.get("m_Scale")
            offset = v.get("m_Offset")
            print(f"    TexEnv '{k}': PID={tex_pid}, scale={scale}, offset={offset}")

print("\n=== Textures in Grindor Bundle ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        print(f"Texture PID={obj.path_id}: '{name}'")

print("\n=== Root Prefabs in Grindor Bundle ===")
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if "grindor" in name.lower() or name.startswith("cha_"):
            print(f"GameObject PID={obj.path_id}: '{name}'")

ab_obj = [o for o in env.objects if o.type.name == "AssetBundle"][0]
ab = ab_obj.read_typetree()
print("\n=== AssetBundle Container ===")
for c in ab.get("m_Container", []):
    print(f"  Container: '{c[0]}' -> PathID={c[1].get('asset', {}).get('m_PathID')}")
