import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

print("--- INSPECTING GAMEOBJECTS IN MEGATRON ROTF BUNDLE ---")
for obj in env.objects:
    if obj.type.name == "GameObject":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if "hand" in name.lower() or "arm" in name.lower() or "right" in name.lower():
            print(f"GameObject: {name} (path_id={obj.path_id})")
