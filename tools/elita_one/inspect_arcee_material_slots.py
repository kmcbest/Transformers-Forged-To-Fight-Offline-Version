import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        tex_envs = tree.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        print(f"\nMaterial: {name} (PID: {obj.path_id})")
        for te in tex_envs:
            tex_name = te[0]
            tex_ptr = te[1].get("m_Texture", {}).get("m_PathID")
            if tex_ptr:
                # find texture name
                t_name = "unknown"
                for o in env.objects:
                    if o.path_id == tex_ptr:
                        t_name = o.read_typetree().get("m_Name", "")
                        break
                print(f"  Slot '{tex_name}': PID {tex_ptr} ({t_name})")
