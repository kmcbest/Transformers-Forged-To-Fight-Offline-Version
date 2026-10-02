import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(BUNDLE))

tex_dict = {}
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tex_dict[obj.path_id] = obj.read_typetree().get("m_Name")

for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        print(f"=== Material: {tree.get('m_Name')} (PathID {obj.path_id}) ===")
        saved_props = tree.get("m_SavedProperties", {})
        for tex in saved_props.get("m_TexEnvs", []):
            tex_pid = tex[1].get('m_Texture', {}).get('m_PathID')
            tex_name = tex_dict.get(tex_pid, "None")
            print(f"    {tex[0]}: {tex_name} (pid {tex_pid})")
