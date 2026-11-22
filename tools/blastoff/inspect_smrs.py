import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))

for obj in env.objects:
    if obj.type.name in ["SkinnedMeshRenderer", "MeshRenderer", "MeshFilter"]:
        tt = obj.read_typetree()
        go_pptr = tt.get("m_GameObject", {})
        go_name = ""
        if go_pptr.get("m_PathID", 0) in env.objects:
            try:
                go_tt = env.objects[go_pptr["m_PathID"]].read_typetree()
                go_name = go_tt.get("m_Name", "")
            except Exception:
                pass
        mesh_pptr = tt.get("m_Mesh", {})
        mats = tt.get("m_Materials", [])
        mat_names = []
        for m in mats:
            mpid = m.get("m_PathID", 0)
            if mpid in env.objects:
                try:
                    mat_tt = env.objects[mpid].read_typetree()
                    mat_names.append(f"{mat_tt.get('m_Name', '')}(PID={mpid})")
                except Exception:
                    mat_names.append(str(mpid))
            else:
                mat_names.append(str(mpid))
        print(f"[{obj.type.name}] PID={obj.path_id} GO='{go_name}' MeshPID={mesh_pptr.get('m_PathID')} Mats={mat_names}")
