import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json, zipfile, struct
from pathlib import Path
import numpy as np
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
for sub in ["source", "textures", "01_aligned_mesh", "02_textures", "03_fbx_exports", "04_unity_bundles"]:
    (WR_DIR / sub).mkdir(parents=True, exist_ok=True)

# 1. Unzip o:\agent\transformers-alliance-wildrider.zip cleanly into 3rd-party-models/WildRider/
ZIP_PATH = Path(r"o:\agent\transformers-alliance-wildrider.zip")
with zipfile.ZipFile(ZIP_PATH, "r") as z:
    for info in z.infolist():
        if info.is_dir():
            continue
        target = WR_DIR / info.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(info.filename))
        print(f"  Extracted: {target}")

# 2. Extract Prowl donor Ground Truth
PROWL_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(PROWL_BUNDLE))

gos = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "GameObject"}
trs = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "Transform"}
meshes = {o.path_id: o for o in env.objects if o.type.name == "Mesh"}
mats = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "Material"}
texs = {o.path_id: o.read_typetree().get("m_Name", "") for o in env.objects if o.type.name == "Texture2D"}

def go_name_from_tr(tr_pid):
    gp = trs.get(tr_pid, {}).get("m_GameObject", {}).get("m_PathID")
    return gos.get(gp, {}).get("m_Name", f"PID:{tr_pid}")

# Dump Material texture bindings & PBR params
print("\n=== Prowl Material Bindings ===")
for pid, mtt in mats.items():
    mname = mtt.get("m_Name", "")
    if mname.startswith("fx_"):
        continue
    sp = mtt.get("m_SavedProperties", {})
    tex_map = {}
    for k, v in sp.get("m_TexEnvs", []):
        tpid = v.get("m_Texture", {}).get("m_PathID", 0)
        if tpid:
            tex_map[k] = (tpid, texs.get(tpid, "?"), v.get("m_Scale"), v.get("m_Offset"))
    floats = {k: round(val, 4) for k, val in sp.get("m_Floats", []) if any(x in k for x in ["emissive", "metallic", "roughness", "clearcoat", "base_col"])}
    cols = {k: val for k, val in sp.get("m_Colors", []) if any(x in k for x in ["Color", "emissive"])}
    print(f"  Mat '{mname}' (PID={pid}):")
    for tk, tv in tex_map.items():
        print(f"    {tk}: {tv}")
    print(f"    floats={floats}")
    print(f"    cols={cols}")

# Dump 50-bone Robot BindPose, 26-bone Vehicle BindPose, and export Reference OBJs
def export_mesh_obj(mesh_obj, out_obj_path):
    m = mesh_obj.read()
    # Read typetree or UnityPy mesh export
    obj_txt = m.export()
    out_obj_path.write_text(obj_txt, encoding="utf-8")
    print(f"  Exported Ref OBJ: {out_obj_path} ({out_obj_path.stat().st_size:,} bytes)")

def dump_smr_truth(target_mesh_name, json_name, obj_name):
    for o in env.objects:
        if o.type.name == "SkinnedMeshRenderer":
            tt = o.read_typetree()
            mpid = tt.get("m_Mesh", {}).get("m_PathID")
            m_reader = meshes.get(mpid)
            if not m_reader:
                continue
            m_tt = m_reader.read_typetree()
            if m_tt.get("m_Name") == target_mesh_name:
                bps = m_tt.get("m_BindPose", [])
                hashes = m_tt.get("m_BoneNameHashes", [])
                bones = tt.get("m_Bones", [])
                out_data = {"mesh_name": target_mesh_name, "mesh_pid": mpid, "bones": []}
                for idx, (b_pptr, bp) in enumerate(zip(bones, bps)):
                    tr_pid = b_pptr.get("m_PathID")
                    bname = go_name_from_tr(tr_pid)
                    mat = np.array([
                        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
                        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
                        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
                        [bp['e30'], bp['e31'], bp['e32'], bp['e33']],
                    ])
                    inv = np.linalg.inv(mat)
                    # Convert Unity (x, y, z) -> Blender (-x, z, y) or keep raw Unity pos & Blender pos
                    upos = inv[:3, 3]
                    out_data["bones"].append({
                        "index": idx,
                        "name": bname,
                        "hash": hashes[idx] if idx < len(hashes) else None,
                        "unity_pos": [float(upos[0]), float(upos[1]), float(upos[2])],
                        "blender_pos": [float(-upos[0]), float(upos[2]), float(upos[1])],
                        "bindpose": bp,
                        "inv_bindpose": inv.tolist(),
                    })
                out_json = WR_DIR / json_name
                out_json.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
                print(f"  Saved truth JSON: {out_json} ({len(out_data['bones'])} bones)")
                export_mesh_obj(m_reader, WR_DIR / obj_name)
                return

dump_smr_truth("cha_prowl_gs_deluxe2016_00", "prowl_50_bones.json", "prowl_robot_ref.obj")
dump_smr_truth("cha_prowl_gs_deluxe2016_01", "prowl_26_vehicle_bones.json", "prowl_veh_ref.obj")
export_mesh_obj(meshes[-7947891575776091319], WR_DIR / "prowl_shotgun_ref.obj")

# Also inspect shotgun Transform hierarchy in Prowl both prefabs
print("\n=== Prowl Gun / Shotgun Transforms ===")
for tr_pid, tr in trs.items():
    gn = go_name_from_tr(tr_pid)
    if gn in ("gun", "Shutgun", "cha_prowl_gs_deluxe2016_wpns_shotgun", "RightHand", "LeftHand", "Prowl_GS_Deluxe2016", "Prowl_GS_Deluxe2016_lw"):
        par_pid = tr.get("m_Father", {}).get("m_PathID", 0)
        par_name = go_name_from_tr(par_pid) if par_pid else "ROOT"
        print(f"  {gn} (TR={tr_pid}, GO={tr.get('m_GameObject',{}).get('m_PathID')}) parent='{par_name}'({par_pid}) pos={tr.get('m_LocalPosition')} rot={tr.get('m_LocalRotation')} scale={tr.get('m_LocalScale')}")
