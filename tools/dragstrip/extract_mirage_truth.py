import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json, numpy as np
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
DS_DIR = ROOT / "3rd-party-models" / "DragStrip"
DS_DIR.mkdir(parents=True, exist_ok=True)
MIRAGE_B = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\mirage_gs_deluxe2016_odr\mirage_gs_deluxe2016.assetbundle")

env = UnityPy.load(str(MIRAGE_B))
sf = list(env.assets)[0]

# 1. Avatar TOS
avatars = {}
for o in env.objects:
    if o.type.name == "Avatar":
        tt = o.read_typetree()
        avatars[tt["m_Name"]] = dict(tt.get("m_TOS", []))
        print(f"Avatar: {tt['m_Name']} PID={o.path_id} TOS_len={len(avatars[tt['m_Name']])}")

# 2. Meshes & BindPoses -> extract OBJs and bone JSONs
print("\n=== Mirage Meshes ===")
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read()
        tt = o.read_typetree()
        mn = tt["m_Name"]
        hashes = tt["m_BoneNameHashes"]
        bps = tt["m_BindPose"]
        print(f"  Mesh PID={o.path_id:22d} name='{mn}' verts={tt['m_VertexData']['m_VertexCount']} submeshes={len(tt['m_SubMeshes'])} bones={len(bps)}")

        # Save OBJ for character/veh/weapons
        if any(k in mn.lower() for k in ("_00", "_01", "wpns")):
            out_obj = DS_DIR / f"mirage_{mn}.obj"
            out_obj.write_text(m.export(), encoding="utf-8")
            xs, ys, zs = [], [], []
            for line in out_obj.read_text(encoding="utf-8").splitlines():
                if line.startswith("v "):
                    _, x, y, z = line.split()[:4]
                    xs.append(float(x)); ys.append(float(y)); zs.append(float(z))
            if xs:
                print(f"    OBJ bounds: X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}]")

            if len(bps) > 0:
                # Find matching avatar TOS
                best_tos = {}
                best_hits = -1
                for avn, tos in avatars.items():
                    hits = sum(1 for h in hashes if h in tos)
                    if hits > best_hits:
                        best_hits = hits; best_tos = tos
                bones_info = []
                for h, bp in zip(hashes, bps):
                    bname = best_tos.get(h, f"h_{h}").split("/")[-1]
                    mat = np.array([
                        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
                        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
                        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
                        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
                    ])
                    inv = np.linalg.inv(mat)
                    upos = [float(inv[0, 3]), float(inv[1, 3]), float(inv[2, 3])]
                    bones_info.append({"name": bname, "hash": int(h), "unity_pos": upos})
                if "_00" in mn and "wpns" not in mn:
                    (DS_DIR / "mirage_00_bones.json").write_text(json.dumps({"mesh": mn, "bones": bones_info}, indent=2), encoding="utf-8")
                    print(f"    Saved mirage_00_bones.json ({len(bones_info)} bones, resolved={best_hits})")
                elif "_01" in mn:
                    (DS_DIR / "mirage_01_bones.json").write_text(json.dumps({"mesh": mn, "bones": bones_info}, indent=2), encoding="utf-8")
                    print(f"    Saved mirage_01_bones.json ({len(bones_info)} bones, resolved={best_hits})")

# 3. SMRs
print("\n=== Mirage SMRs ===")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        go = sf.objects[tt["m_GameObject"]["m_PathID"]].read()
        print(f"  SMR PID={o.path_id:22d} go='{go.m_Name}' goPID={tt['m_GameObject']['m_PathID']} meshPID={tt['m_Mesh']['m_PathID']} mats={[m['m_PathID'] for m in tt['m_Materials']]} en={tt['m_Enabled']}")

# 4. Materials & Textures
print("\n=== Mirage Materials ===")
for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        envs = {k: (v["m_Texture"]["m_PathID"], v["m_Scale"], v["m_Offset"]) for k, v in tt["m_SavedProperties"]["m_TexEnvs"] if v["m_Texture"]["m_PathID"] != 0}
        cols = {k: (round(v["r"],3), round(v["g"],3), round(v["b"],3), round(v["a"],3)) for k, v in tt["m_SavedProperties"]["m_Colors"]}
        print(f"  Mat PID={o.path_id:22d} name='{tt['m_Name']}' tex={envs} em={cols.get('_emissive_intensity_col')} col={cols.get('_Color')}")

print("\n=== Mirage Texture2Ds ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        print(f"  Tex PID={o.path_id:22d} name='{t.m_Name}' {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat} stream={getattr(t.m_StreamData,'size',0)}")

print("\n=== Mirage PropsController ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        try:
            tt = o.read_typetree()
        except Exception:
            continue
        if "_props" in tt:
            for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                print(f"  Prop '{k}': Root='{v.get('RootPath')}' Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} Scl={v.get('Scale')} rend={v.get('_renderers')}")
            break
