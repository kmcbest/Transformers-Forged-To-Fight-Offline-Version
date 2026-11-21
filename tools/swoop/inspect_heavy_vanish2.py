import sys
import os
import zlib
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

b_path = r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle"
env = UnityPy.load(b_path)
objs = {o.path_id: o for o in env.objects}

# 1. Check all 29 bone hashes
smr = objs[4450385079657545705].read()
mesh = objs[smr.m_Mesh.m_PathID].read()
mesh_hashes = [int(h) & 0xffffffff for h in mesh.m_BoneNameHashes]
print(f"=== Vehicle SMR 4450385079657545705 vs Mesh '{mesh.m_Name}' ({len(smr.m_Bones)} bones) ===")
for i, b in enumerate(smr.m_Bones):
    tr = objs[b.m_PathID].read()
    go = objs[tr.m_GameObject.m_PathID].read()
    print(f"  [{i:2d}] {go.m_Name:30s} hash={mesh_hashes[i]:10d}")

# 2. Check Fight AOC and Jet AOC all clips
for aoc_pid in (6432204470035570307, -6340484879223379266):
    aoc = objs[aoc_pid].read_typetree()
    print(f"\n=== AOC '{aoc.get('m_Name')}' ({aoc_pid}) ===")
    for idx, pair in enumerate(aoc.get("m_Clips", [])):
        orig = pair["m_OriginalClip"]["m_PathID"]
        over = pair["m_OverrideClip"]["m_PathID"]
        vname = objs[over].read().m_Name if over in objs else f"EXT({over})"
        if idx in (58, 12, 5, 16) or "heavy" in vname.lower() or "flap" in vname.lower() or "transform" in vname.lower():
            print(f"  [{idx:2d}] orig={orig} -> over=({over}: {vname})")
            if over in objs:
                ctt = objs[over].read_typetree()
                m_cl = ctt.get("m_ClipBindingConstant", {})
                gc = m_cl.get("genericBindings", [])
                muscle = ctt.get("m_MuscleClip", {})
                clip = muscle.get("m_Clip", {})
                print(f"       clip keys={list(clip.keys())}, stopTime={muscle.get('m_StopTime')}, bindings={len(gc)}")
                for ck, cv in clip.items():
                    if isinstance(cv, dict):
                        data = cv.get("data") or cv.get("m_CurveArray") or cv.get("m_DataArray") or cv.get("m_Data")
                        print(f"         {ck}: keys={list(cv.keys())} len_data={len(data) if hasattr(data,'__len__') else 'N/A'} frameCount={cv.get('m_FrameCount')}")
                for bi, b in enumerate(gc[:15]):
                    print(f"         binding[{bi}]: path={b.get('path')} attr={b.get('attribute')} typeID={b.get('typeID')}")

# 3. Inspect Moves
m_path = r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle"
menv = UnityPy.load(m_path)
print("\n=== Moves in assets_redeco/moves.assetbundle ===")
for o in menv.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        name = tt.get("m_Name", "")
        if "heavy" in name and any(k in name for k in ("swoop", "starscream", "ramjet", "skywarp", "thundercracker", "grimlock")):
            print(f"\nMove '{name}' keys={list(tt.keys())}")
            for k in ("ClipName", "PropClipName", "Duration", "m_AnimationClip", "m_ClipName", "_animation", "_clipName"):
                if k in tt:
                    print(f"  {k}: {tt[k]}")
            for ev_key in ("MoveEvents", "_events", "Events"):
                if ev_key in tt:
                    evs = tt[ev_key]
                    print(f"  {ev_key} ({len(evs)}):")
                    for ev in evs:
                        # Handle if ev is dict or PPtr
                        if isinstance(ev, dict) and "m_PathID" in ev:
                            eo = menv.objects
                            print(f"    PPtr {ev}")
                        else:
                            print(f"    {ev}")
