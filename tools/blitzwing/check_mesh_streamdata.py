import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

for label, p in [
    ("MESH_BUNDLE", Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")),
    ("BW_BUNDLE", Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")),
]:
    env = UnityPy.load(str(p))
    print(f"\n=== {label}: {p.name} files={list(env.file.files.keys())} ===")
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            print(f"  Mesh '{tt['m_Name']}' PID={o.path_id}: vc={tt['m_VertexData']['m_VertexCount']} datasize={len(tt['m_VertexData']['m_DataSize'])} idx={len(tt['m_IndexBuffer'])} stream={tt.get('m_StreamData')}")
