import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

prowl_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(prowl_bundle))

tex_dict = {}
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        tex_dict[obj.path_id] = tree.get("m_Name")

for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        mat_name = tree.get("m_Name")
        props = tree.get("m_SavedProperties", {})
        for name, tex in props.get("m_TexEnvs", []):
            t_pid = tex.get("m_Texture", {}).get("m_PathID")
            if t_pid != 0:
                print(f"Material '{mat_name}' (PID {obj.path_id}) -> property '{name}' -> Texture '{tex_dict.get(t_pid)}' (PID {t_pid})")
