import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

MESH_BUNDLE = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env = UnityPy.load(MESH_BUNDLE)

for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        print(f"Mesh '{m['m_Name']}':")
        print(f"  bones: {len(m.get('m_BoneNameHashes', []))}")
        print(f"  rootBone: {m.get('m_RootBoneNameHash')}")
        print(f"  submeshes: {len(m.get('m_SubMeshes', []))}")
        bp = m.get("m_BindPose", [])
        print(f"  bindposes: {len(bp)}")
        # Check bone weights format
        vd = m.get("m_VertexData", {})
        print(f"  channels: {len(vd.get('m_Channels', []))}")
        for i, ch in enumerate(vd.get("m_Channels", [])):
            if ch["dimension"] > 0:
                print(f"    ch {i}: stream={ch['stream']} off={ch['offset']} fmt={ch['format']} dim={ch['dimension']}")
