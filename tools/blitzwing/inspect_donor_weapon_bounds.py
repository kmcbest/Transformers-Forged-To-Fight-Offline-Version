import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import struct
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

def get_mesh_bounds(m_tt):
    vd = m_tt["m_VertexData"]
    vc = vd["m_VertexCount"]
    raw = bytes(vd["m_DataSize"])
    # channel 0 is position float3
    ch0 = vd["m_Channels"][0]
    stream = ch0["stream"]
    offset = ch0["offset"]
    # compute stream strides from channels
    strides = {}
    for ch in vd["m_Channels"]:
        if ch["dimension"] > 0:
            s = ch["stream"]
            end = ch["offset"] + ch["dimension"] * (4 if ch["format"] == 0 else (2 if ch["format"] == 1 else 1))
            # Check format size: 0=F32(4), 1=F16(2), 2=UNorm8(4 bytes total if dim=4), 11=UInt8(1)? Actually format 2/4 UNorm8 is 1 byte per dim, Int32/UInt32=4
            fmt = ch["format"]
            bpc = 4 if fmt in (0, 6, 7, 10, 11) else (2 if fmt in (1, 8, 9) else 1)
            end = ch["offset"] + ch["dimension"] * bpc
            strides[s] = max(strides.get(s, 0), end)
    # Use stream 0 offset
    s0_stride = strides.get(0, 12)
    pts = []
    for i in range(vc):
        base = i * s0_stride + offset
        if base + 12 <= len(raw):
            x, y, z = struct.unpack_from("<fff", raw, base)
            pts.append((x, y, z))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    return vc, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)), len(m_tt.get("m_BindPose", []))

# 1. Check Megatron textures
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
omap = {o.path_id: o for o in meg_env.objects}
print("=== Megatron All Texture2Ds ===")
for o in meg_env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        print(f"  {o.path_id:<22} '{t.m_Name}' {t.m_Width}x{t.m_Height}")

mat_wpn = omap[-9117353815363826346].read_typetree()
print(f"\nMegatron Weapon Mat -9117353815363826346 ('{mat_wpn['m_Name']}'):")
for k, v in mat_wpn["m_SavedProperties"]["m_TexEnvs"]:
    pid = v["m_Texture"]["m_PathID"]
    nm = omap[pid].read().m_Name if pid in omap else pid
    print(f"  {k}: {pid} ('{nm}')")

# 2. Check donor weapon meshes & local bounds
for label, bpath, mesh_kw, prop_key in [
    ("Motormaster Gun", ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle", "wpns_rifle", "gun"),
    ("Bludgeon Sword", ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle", "wpns_sword", "sword"),
    ("Windblade Sword", ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle", "wpns_sword", "Sword"),
]:
    env = UnityPy.load(str(bpath))
    m = {o.path_id: o for o in env.objects}
    print(f"\n=== {label} ===")
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            if mesh_kw in tt.get("m_Name", "").lower():
                try:
                    vc, bx, by, bz, nb = get_mesh_bounds(tt)
                    print(f"  Mesh '{tt['m_Name']}' ({o.path_id}): verts={vc} bones={nb} X=[{bx[0]:.3f},{bx[1]:.3f}] Y=[{by[0]:.3f},{by[1]:.3f}] Z=[{bz[0]:.3f},{bz[1]:.3f}] localAABB={tt['m_LocalAABB']}")
                except Exception as ex:
                    print(f"  Mesh '{tt['m_Name']}': localAABB={tt['m_LocalAABB']} (err={ex})")
        elif o.type.name == "GameObject":
            go = o.read_typetree()
            if go["m_Name"] in ("RightProp", "LeftProp"):
                tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if m[c["component"]["m_PathID"]].type.name == "Transform")
                tr = m[tr_pid].read_typetree()
                print(f"  PropAnchor '{go['m_Name']}': pos={tr['m_LocalPosition']} rot={tr['m_LocalRotation']}")
                break
        elif o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_props" in tt:
                for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                    if k == prop_key:
                        print(f"  PropsCtrl '{k}': AOC={v.get('OverrideController')} InitFlags={v.get('InitFlags')} Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')}")
        elif o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            if "sword" in tt.get("m_Name", "").lower() or "gun" in tt.get("m_Name", "").lower():
                print(f"  Prop AOC '{tt['m_Name']}' ({o.path_id}): ctrl={tt.get('m_Controller')} clips={len(tt.get('m_Clips', []))}")
                for i, c in enumerate(tt.get("m_Clips", [])):
                    ovr = c["m_OverrideClip"]
                    if ovr["m_PathID"] != 0:
                        nm = m[ovr["m_PathID"]].read_typetree().get("m_Name", "") if (ovr["m_FileID"]==0 and ovr["m_PathID"] in m) else ""
                        print(f"    [{i}] orig=({c['m_OriginalClip']['m_FileID']},{c['m_OriginalClip']['m_PathID']}) -> ovr=({ovr['m_FileID']},{ovr['m_PathID']}) '{nm}'")
