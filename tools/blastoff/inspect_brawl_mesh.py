import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
from pathlib import Path
import UnityPy
from tools.validate_port_gates import parse_unity_mesh_streams

brawl_bundle = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle"
if Path(brawl_bundle).exists():
    env = UnityPy.load(brawl_bundle)
    for obj in env.objects:
        if obj.type.name == "Mesh" and "00" in obj.peek_name():
            tt = obj.read_typetree()
            pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
            print("Brawl Robot Mesh:")
            print(f"  Y: [{pts[:,1].min():.3f}, {pts[:,1].max():.3f}]")
else:
    print("No brawl bundle found")
