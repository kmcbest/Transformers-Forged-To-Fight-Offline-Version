import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(BUNDLE))
sf = list(env.assets)[0]

mat_obj = sf.objects[6327179545371057975]
mat_tree = mat_obj.read_typetree()
print("Material Name:", mat_tree.get("m_Name"))
print("Shader:", mat_tree.get("m_Shader"))
for item in mat_tree.get("m_SavedProperties", {}).get("m_TexEnvs", []):
    if isinstance(item, tuple):
        t_name, t_info = item
    else:
        t_name = item.get("first")
        t_info = item.get("second", {})
    t_ref = t_info.get("m_Texture", {})
    t_pid = t_ref.get("m_PathID")
    to = sf.objects.get(t_pid)
    to_name = to.read_typetree().get("m_Name") if to else "External/Missing"
    print(f"  Tex '{t_name}': {to_name} (FileID={t_ref.get('m_FileID')}, PID={t_pid})")
