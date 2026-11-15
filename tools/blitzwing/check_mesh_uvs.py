import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
mesh_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"

env = UnityPy.load(str(mesh_bundle))
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if m['m_Name'] == 'cha_blitzwing_gs_00':
            print("Checking UV channels in cha_blitzwing_gs_00:")
            # In UnityPy, vertex data channels
            ch = m['m_VertexData']['m_Channels']
            for i, c in enumerate(ch):
                if c['dimension'] > 0:
                    print(f"  Channel {i}: stream={c['stream']}, offset={c['offset']}, fmt={c['format']}, dim={c['dimension']}")
