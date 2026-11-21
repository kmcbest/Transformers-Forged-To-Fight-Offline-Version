import sys
import os
import json
import zlib
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def crc32_signed(s):
    h = zlib.crc32(s.encode("utf-8"))
    return h - 0x100000000 if h >= 0x80000000 else h

def inspect_bundle():
    b_path = r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle"
    d_path = r"E:\Agent\TFTF-blender\tools\swoop\ramjet_gs_deluxe2008.assetbundle"
    if not os.path.exists(d_path):
        d_path = r"E:\Agent\TFTF\assets_netflix\ramjet_gs_deluxe2008.assetbundle"
    if not os.path.exists(d_path):
        d_path = r"E:\Agent\TFTF\assets_redeco\ramjet_gs_deluxe2008.assetbundle"

    env = UnityPy.load(b_path)
    objs = {o.path_id: o for o in env.objects}

    # Check Vehicle SMR & Mesh hashes
    for pid in (-1331665652208216405, 4450385079657545705):
        smr = objs[pid].read()
        mesh = objs[smr.m_Mesh.m_PathID].read()
        bones = []
        for b in smr.m_Bones:
            tr = objs[b.m_PathID].read()
            go = objs[tr.m_GameObject.m_PathID].read()
            bones.append(go.m_Name)
        mesh_hashes = list(getattr(mesh, "m_BoneNameHashes", []))
        print(f"Vehicle SMR {pid}: len(m_Bones)={len(bones)}, len(mesh.m_BoneNameHashes)={len(mesh_hashes)}, m_RootBoneNameHash={getattr(mesh, 'm_RootBoneNameHash', None)}")
        # Check if Unity/CRC hashes match bones
        mismatches = 0
        for i, name in enumerate(bones[:10]):
            print(f"  [{i}] {name} | mesh_hash={mesh_hashes[i] if i < len(mesh_hashes) else 'NONE'}")

    # Check PropsController on Main & LW
    for root_pid, tag in ((1529847556182042256, "Main"), (-4280993829309278178, "LW")):
        root_go = objs[root_pid].read()
        print(f"\n=== {tag} Root '{root_go.m_Name}' components ===")
        for comp_ref in root_go.m_Component:
            c = objs[comp_ref.component.m_PathID]
            if c.type.name == "MonoBehaviour":
                try:
                    t = c.read_typetree()
                    if "_defaultTransformedScaleFactor" in t or "_props" in t or "_transformedTransform" in t:
                        print(f"  MonoBehaviour {c.path_id}: keys={list(t.keys())}")
                        for k in ("_defaultTransformedScaleFactor", "_transformedScaleFactor", "_hidePropsDuringTransformed", "_transformedTransform", "_props"):
                            if k in t:
                                print(f"    {k} = {t[k]}")
                except Exception as e:
                    pass

    # Check transformed bone hierarchy & AnimatorController overrides
    print("\n=== AOC & Heavy Clips ===")
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            aoc = o.read_typetree()
            print(f"AOC {o.path_id} name={aoc.get('m_Name')} clips={len(aoc.get('m_Clips', []))}")
            for idx, pair in enumerate(aoc.get("m_Clips", [])):
                orig = pair["m_OriginalClip"]["m_PathID"]
                over = pair["m_OverrideClip"]["m_PathID"]
                oname = objs[orig].read().m_Name if orig in objs else str(orig)
                vname = objs[over].read().m_Name if over in objs else str(over)
                if "heavy" in oname.lower() or "heavy" in vname.lower() or "flap" in vname.lower() or "transformed" in oname.lower():
                    print(f"  [{idx}] orig=({orig}:{oname}) -> over=({over}:{vname})")

def inspect_clips():
    b_path = r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle"
    env = UnityPy.load(b_path)
    for o in env.objects:
        if o.type.name == "AnimationClip":
            name = o.read().m_Name
            if any(k in name.lower() for k in ("attackheavy", "wingflap")):
                tt = o.read_typetree()
                m_cl = tt.get("m_ClipBindingConstant", {})
                gc = m_cl.get("genericBindings", [])
                muscle = tt.get("m_MuscleClip", {})
                clip = muscle.get("m_Clip", {})
                const_cnt = clip.get("m_ConstantClip", {}).get("data", [])
                stream_cnt = len(clip.get("m_StreamedClip", {}).get("data", []))
                dense_cnt = clip.get("m_DenseClip", {}).get("m_FrameCount", 0)
                print(f"\nClip '{name}' (pid={o.path_id}): length={muscle.get('m_StopTime')}, bindings={len(gc)}, const={len(const_cnt)}, stream={stream_cnt}, denseFrames={dense_cnt}")
                # Decode bindings paths if present in m_PositionCurves / etc or genericBindings
                pos_c = tt.get("m_PositionCurves", [])
                rot_c = tt.get("m_RotationCurves", [])
                scl_c = tt.get("m_ScaleCurves", [])
                flt_c = tt.get("m_FloatCurves", [])
                print(f"  legacy curves: pos={len(pos_c)}, rot={len(rot_c)}, scl={len(scl_c)}, flt={len(flt_c)}")
                if scl_c:
                    for sc in scl_c[:10]:
                        print(f"    scl path='{sc.get('path')}' k0={sc.get('curve',{}).get('m_Curve',[{}])[0].get('value')}")
                if pos_c:
                    for pc in pos_c[:10]:
                        vals = [k.get('value') for k in pc.get('curve',{}).get('m_Curve',[])]
                        print(f"    pos path='{pc.get('path')}' k0={vals[0] if vals else None} kmid={vals[len(vals)//2] if vals else None}")
                if flt_c:
                    for fc in flt_c[:10]:
                        print(f"    flt path='{fc.get('path')}' attr='{fc.get('attribute')}' keys={[(k.get('time'), k.get('value')) for k in fc.get('curve',{}).get('m_Curve',[])]}")

def inspect_moves():
    m_path = r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle"
    env = UnityPy.load(m_path)
    targets = {"move_heavy_swoop", "move_heavy_starscream_shoot", "move_heavy_ramjet_donut", "move_heavy_skywarp_shoot", "move_heavy_thundercracker_shoot", "move_heavy_grimlock"}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            if name in targets or (name.startswith("move_heavy_") and ("starscream" in name or "ramjet" in name or "seeker" in name or "swoop" in name)):
                print(f"\n=== Move '{name}' (pid={o.path_id}) ===")
                for k in ("ClipName", "PropClipName", "Duration", "MoveEvents"):
                    if k == "MoveEvents":
                        evs = tt.get("MoveEvents", [])
                        print(f"  MoveEvents ({len(evs)}):")
                        for ev in evs:
                            tname = ev.get("$Type") or ev.get("m_Script") or ""
                            # print all keys cleanly
                            summary = {ek: ev[ek] for ek in ev if ek not in ("m_GameObject", "m_Enabled", "m_Script")}
                            print(f"    {summary}")
                    elif k in tt:
                        print(f"  {k}: {tt[k]}")

if __name__ == "__main__":
    inspect_bundle()
    inspect_clips()
    inspect_moves()
