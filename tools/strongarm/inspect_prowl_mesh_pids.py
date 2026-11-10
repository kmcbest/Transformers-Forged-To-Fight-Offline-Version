import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

prowl_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(prowl_bundle))

mesh_pids = {}
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        mesh_pids[obj.path_id] = tree.get("m_Name")
        print(f"Mesh PID {obj.path_id}: {tree.get('m_Name')}")

go_names = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        go_names[obj.path_id] = tree.get("m_Name")

print("\n--- SkinnedMeshRenderers ---")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        m_pid = tree.get("m_Mesh", {}).get("m_PathID")
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        mats = [m.get("m_PathID") for m in tree.get("m_Materials", [])]
        print(f"SMR PID {obj.path_id}: GO='{go_names.get(go_id)}' Mesh='{mesh_pids.get(m_pid)}' (PID {m_pid}) Bones={len(tree.get('m_Bones', []))} Mats={mats}")

print("\n--- Materials & TexEnvs ---")
for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        props = tree.get("m_SavedProperties", {})
        tex_envs = props.get("m_TexEnvs", [])
        tex_names = []
        for name, tex in tex_envs:
            t_pid = tex.get("m_Texture", {}).get("m_PathID")
            if t_pid != 0:
                tex_names.append(f"{name}->{t_pid}")
        print(f"Material PID {obj.path_id}: Name='{tree.get('m_Name')}' Tex={tex_names}")
