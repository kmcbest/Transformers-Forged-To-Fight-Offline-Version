import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import UnityPy
from tools.validate_port_gates import parse_unity_mesh_streams

donor_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle"
bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle"

print("--- Donor Megatronus ---")
env_d = UnityPy.load(donor_path)
for obj in env_d.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
        if pts is not None:
            print(f"Mesh: {tt['m_Name']}")
            print(f"  X: [{pts[:,0].min():.3f}, {pts[:,0].max():.3f}]")
            print(f"  Y: [{pts[:,1].min():.3f}, {pts[:,1].max():.3f}]")
            print(f"  Z: [{pts[:,2].min():.3f}, {pts[:,2].max():.3f}]")

print("\n--- Grafted Blast Off ---")
env_b = UnityPy.load(bundle_path)
for obj in env_b.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
        if pts is not None:
            print(f"Mesh: {tt['m_Name']}")
            print(f"  X: [{pts[:,0].min():.3f}, {pts[:,0].max():.3f}]")
            print(f"  Y: [{pts[:,1].min():.3f}, {pts[:,1].max():.3f}]")
            print(f"  Z: [{pts[:,2].min():.3f}, {pts[:,2].max():.3f}]")
