import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        name = tt["m_Name"]
        if "01" in name or "02" in name or "tank" in name or "jet" in name:
            skin = tt.get("m_Skin", [])
            bones = tt.get("m_BoneNameHashes", [])
            root = tt.get("m_RootBoneNameHash")
            vd = tt.get("m_VertexData", {})
            channels = vd.get("m_Channels", [])
            print(f"\nMesh: {name} (PID {o.path_id})")
            print(f"  BoneNameHashes: {bones} (len={len(bones)})")
            print(f"  RootBone: {root}")
            print(f"  Skin len: {len(skin)}")
            if skin:
                print(f"  Skin[0]: {skin[0]}")
            for i, ch in enumerate(channels):
                if ch['dimension'] > 0:
                    print(f"  Ch {i}: stream={ch['stream']}, offset={ch['offset']}, fmt={ch['format']}, dim={ch['dimension']}")

    elif o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones = tt.get("m_Bones", [])
        root = tt.get("m_RootBone", {}).get("m_PathID")
        print(f"\nSMR PID {o.path_id}:")
        print(f"  m_Mesh PathID: {mesh_pid}")
        print(f"  m_Bones count: {len(bones)}")
        print(f"  m_RootBone: {root}")
