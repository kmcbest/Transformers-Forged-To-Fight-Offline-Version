import UnityPy
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
print(f"Loading Grindor bundle: {bundle_path}")
env = UnityPy.load(bundle_path)

out_dir = r"E:\Agent\TFTF-blender\tools\vortex"
os.makedirs(out_dir, exist_ok=True)

for obj in env.objects:
    if obj.type.name == "Mesh":
        d = obj.read_typetree()
        mname = d.get("m_Name", "")
        if mname == "cha_grindor_cin_rotf_00":
            bp = d.get("m_BindPose", [])
            bnh = d.get("m_BoneNameHashes", [])
            print(f"Found cha_grindor_cin_rotf_00: BindPoses={len(bp)}, Hashes={len(bnh)}")
            with open(os.path.join(out_dir, "grindor_00_bindposes.json"), "w", encoding="utf-8") as f:
                json.dump({"m_BindPose": bp, "m_BoneNameHashes": bnh}, f, indent=2)
            print("Saved grindor_00_bindposes.json")
            
        elif mname == "cha_grindor_cin_rotf_01":
            bp = d.get("m_BindPose", [])
            bnh = d.get("m_BoneNameHashes", [])
            print(f"Found cha_grindor_cin_rotf_01: BindPoses={len(bp)}, Hashes={len(bnh)}")
            with open(os.path.join(out_dir, "grindor_01_bindposes.json"), "w", encoding="utf-8") as f:
                json.dump({"m_BindPose": bp, "m_BoneNameHashes": bnh}, f, indent=2)
            print("Saved grindor_01_bindposes.json")

    elif obj.type.name == "Material":
        d = obj.read_typetree()
        print(f"Material: {d.get('m_Name')}")
        tex_envs = d.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        for te in tex_envs:
            prop = list(te.keys())[0] if isinstance(te, dict) else str(te)
            val = te[prop] if isinstance(te, dict) else None
            tex_ptr = val.get("m_Texture", {}) if val else {}
            scale = val.get("m_Scale", {}) if val else {}
            offset = val.get("m_Offset", {}) if val else {}
            print(f"    {prop}: ptr={tex_ptr}, scale=({scale.get('x')},{scale.get('y')}), offset=({offset.get('x')},{offset.get('y')})")
