import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

FBX = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_tank.fbx"
env = UnityPy.load(FBX)
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        print(f"Tank FBX Mesh: '{m.get('m_Name')}'")
        print(f"  verts: {m.get('m_VertexData', {}).get('m_VertexCount')}")
        print(f"  bones: {len(m.get('m_BoneNameHashes', []))}")
        print(f"  bindposes: {len(m.get('m_BindPose', []))}")
