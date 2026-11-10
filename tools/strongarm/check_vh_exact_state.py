import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from pathlib import Path

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# 1. Inspect raw strongarm_vehicle.obj dims
obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
vs = []
vts = []
for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("v "):
        p = line.split()
        vs.append([float(p[1]), float(p[2]), float(p[3])])
    elif line.startswith("vt "):
        p = line.split()
        vts.append([float(p[1]), float(p[2])])
vs = np.array(vs)
vts = np.array(vts)
print(f"Raw strongarm_vehicle.obj verts={len(vs)}: X=[{vs[:,0].min():.3f}, {vs[:,0].max():.3f}] (w={np.ptp(vs[:,0]):.3f}), "
      f"Y=[{vs[:,1].min():.3f}, {vs[:,1].max():.3f}] (h={np.ptp(vs[:,1]):.3f}), "
      f"Z=[{vs[:,2].min():.3f}, {vs[:,2].max():.3f}] (l={np.ptp(vs[:,2]):.3f})")
print(f"Raw UVs u=[{vts[:,0].min():.3f}, {vts[:,0].max():.3f}], v=[{vts[:,1].min():.3f}, {vts[:,1].max():.3f}]")

# 2. Check Prowl Official Vehicle Mesh + Material texenvs
env_p = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
for o in env_p.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        print(f"Prowl Vehicle Mesh LocalAABB: center={mt['m_LocalAABB']['m_Center']}, extent={mt['m_LocalAABB']['m_Extent']}, submeshes={len(mt['m_SubMeshes'])}")
    elif o.type.name == "Material" and o.path_id in (8471270994157717165, 7500203752916154549, -7118460493794104175):
        mt = o.read_typetree()
        print(f"Prowl Official Mat {o.path_id} ('{mt['m_Name']}'):")
        for k, v in mt["m_SavedProperties"]["m_TexEnvs"]:
            if v["m_Texture"]["m_PathID"] != 0:
                print(f"  {k}: PID={v['m_Texture']['m_PathID']} scale={v['m_Scale']} offset={v['m_Offset']}")

# 3. Check Strongarm Vehicle state in strongarm_gs.assetbundle + dump textures
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")
gos = {o.path_id: o.read_typetree().get("m_Name") for o in env_s.objects if o.type.name == "GameObject"}
trs = {o.path_id: o.read_typetree() for o in env_s.objects if o.type.name == "Transform"}
tr_to_go = {pid: t.get("m_GameObject", {}).get("m_PathID") for pid, t in trs.items()}

for o in env_s.objects:
    if o.type.name == "Material" and o.path_id == 8471270994157717165:
        mt = o.read_typetree()
        print("\nStrongarm Vehicle Material in bundle:")
        for k, v in mt["m_SavedProperties"]["m_TexEnvs"]:
            if v["m_Texture"]["m_PathID"] != 0:
                print(f"  {k}: PID={v['m_Texture']['m_PathID']} scale={v['m_Scale']} offset={v['m_Offset']}")
    elif o.type.name == "SkinnedMeshRenderer" and len(o.read_typetree().get("m_Bones", [])) == 26:
        s = o.read_typetree()
        print(f"\nStrongarm Vehicle SMR PID={o.path_id}: m_Enabled={s.get('m_Enabled')} m_Materials={s.get('m_Materials')} RootBone={gos.get(tr_to_go.get(s['m_RootBone']['m_PathID']))}")
        print(f"  m_AABB: {s['m_AABB']}")
    elif o.type.name == "Texture2D":
        t = o.read_typetree()
        nm = t.get("m_Name")
        if nm in ("tform_misc_A", "tform_misc_NM"):
            im = o.read().image
            im.save(SCRATCH / f"bundle_{nm}.png")
            print(f"Saved {nm} ({im.size}, {im.mode}, fmt={t.get('m_TextureFormat')}) -> scratch/bundle_{nm}.png")
    elif o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        mt = o.read_typetree()
        print(f"\nStrongarm Vehicle Mesh in bundle: LocalAABB={mt['m_LocalAABB']}, submeshes={len(mt['m_SubMeshes'])}")
        vd = mt.get("m_VertexData", {})
        print("  Vertex channels:", [(c.get("stream"), c.get("offset"), c.get("format"), c.get("dimension")) for c in vd.get("m_Channels", [])])
