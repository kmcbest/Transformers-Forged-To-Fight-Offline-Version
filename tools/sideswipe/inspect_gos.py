import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        go_name = getattr(data, 'm_Name', 'unnamed')
        # check components
        comp_types = []
        for c in data.m_Components:
            try:
                comp = c.read()
                comp_types.append(comp.type.name)
                if comp.type.name == "SkinnedMeshRenderer":
                    mesh_name = comp.m_Mesh.read().m_Name if comp.m_Mesh else "None"
                    mats = [m.read().m_Name if m else "None" for m in comp.m_Materials]
                    print(f"GO '{go_name}' has SkinnedMeshRenderer: Mesh='{mesh_name}', Mats={mats}")
            except Exception:
                pass
