import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))

for obj in env.objects:
    if obj.type.name == "Material":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        tex_envs = tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        print(f"\n[Material] PID={obj.path_id} name='{name}'")
        for item in tex_envs:
            if isinstance(item, tuple) and len(item) == 2:
                prop_name, prop_data = item
                tex_pid = prop_data.get("m_Texture", {}).get("m_PathID", 0)
                tex_name = ""
                if tex_pid in env.objects:
                    try:
                        tex_name = env.objects[tex_pid].read_typetree().get("m_Name", "")
                    except Exception:
                        pass
                print(f"   Prop '{prop_name}': PID={tex_pid} ({tex_name})")
