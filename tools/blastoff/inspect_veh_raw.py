import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import UnityPy

ab_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle"
env = UnityPy.load(ab_path)
for obj in env.objects:
    if obj.type.name == "Mesh" and "01" in obj.peek_name():
        tt = obj.read_typetree()
        from tools.validate_port_gates import parse_unity_mesh_streams
        vp, vuv, vws, vbi = parse_unity_mesh_streams(tt)
        print("Vehicle mesh in blastoff_mesh.assetbundle:")
        print(f"  X: [{vp[:,0].min():.3f}, {vp[:,0].max():.3f}]")
        print(f"  Y: [{vp[:,1].min():.3f}, {vp[:,1].max():.3f}]")
        print(f"  Z: [{vp[:,2].min():.3f}, {vp[:,2].max():.3f}]")
