import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import struct
import UnityPy
from inspect_sword_space_and_fx import tr_to_m4, bp_to_m4, m4_mul, m4_pt

ROOT_GM = Path(r"E:\Agent\TFTF")

def export_donor_mesh_in_hand_space(bundle_path, tr_ids, mesh_pid, out_obj):
    env = UnityPy.load(str(bundle_path))
    m = {o.path_id: o for o in env.objects}
    M = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    for tid in tr_ids:
        M = m4_mul(M, tr_to_m4(m[tid].read_typetree()))
    mesh_tt = m[mesh_pid].read_typetree()
    M = m4_mul(M, bp_to_m4(mesh_tt["m_BindPose"][0]))
    # Read vertex stream via UnityPy Mesh.read()
    mesh_obj = m[mesh_pid].read()
    # Read positions using export or raw data
    obj_txt = mesh_obj.export()
    out_obj.parent.mkdir(parents=True, exist_ok=True)
    # Transform all 'v x y z' lines in exported OBJ by M!
    lines = []
    xs, ys, zs = [], [], []
    for line in obj_txt.splitlines():
        if line.startswith("v "):
            parts = line.split()
            p = (-float(parts[1]), float(parts[2]), float(parts[3])) # UnityPy obj flips X! Wait check obj export convention!
            lines.append((line, p))
        else:
            lines.append((line, None))
    # Instead of guessing UnityPy OBJ X-flip, check M * v_raw directly vs obj export!
    print(f"Loaded {mesh_tt['m_Name']}: verts={mesh_tt['m_VertexData']['m_VertexCount']}")
    return mesh_obj, M

mm_path = ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle"
wb_path = ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle"

# Wait: inspect Mesh m_VertexData directly OR print m_LocalAABB + StarSaber gun_fbx in Unity!
ss_fbx_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles")
print("Existing AssetBundles:", list(ss_fbx_mesh.glob("*.assetbundle")))
for ab in ss_fbx_mesh.glob("*.assetbundle"):
    e = UnityPy.load(str(ab))
    for o in e.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            print(f"  [{ab.name}] Mesh '{tt['m_Name']}' PID={o.path_id} verts={tt['m_VertexData']['m_VertexCount']} bp0={[round(tt['m_BindPose'][0][k],3) for k in ('e00','e01','e02','e03','e10','e11','e12','e13','e20','e21','e22','e23')] if tt['m_BindPose'] else 'none'}")
