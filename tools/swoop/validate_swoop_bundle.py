import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
MOVES_PATH = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")


def validate():
    print(f"=== Validating {BUNDLE_PATH} ===")
    assert BUNDLE_PATH.is_file(), f"Bundle file missing: {BUNDLE_PATH}"
    env = UnityPy.load(str(BUNDLE_PATH))
    sf = list(env.assets)[0]
    obj_map = {o.path_id: o for o in sf.objects.values()}

    # 1. Check script_types sorting
    st_entries = [(st.local_serialized_file_index, st.local_identifier_in_file) for st in sf.script_types]
    assert st_entries == sorted(st_entries), f"script_types are NOT sorted ascending! {st_entries}"
    print(f"  [PASS] script_types count = {len(st_entries)}, strictly sorted ascending.")

    # 2. Check all MonoBehaviours
    mb_count = 0
    for obj in sf.objects.values():
        if obj.type.name == "MonoBehaviour":
            mb_count += 1
            tt = obj.read_typetree()
            m_script = tt.get("m_Script", {})
            fid = m_script.get("m_FileID", 0)
            pid = m_script.get("m_PathID", 0)

            st_idx = sf.types[obj.type_id].script_type_index
            assert 0 <= st_idx < len(sf.script_types), f"Invalid script_type_index {st_idx} for MB {obj.path_id}"
            st = sf.script_types[st_idx]
            assert st.local_serialized_file_index == fid and st.local_identifier_in_file == pid, (
                f"Mismatch: MB {obj.path_id} m_Script=({fid},{pid}) != script_types[{st_idx}]=({st.local_serialized_file_index},{st.local_identifier_in_file})"
            )
    print(f"  [PASS] {mb_count} MonoBehaviours validated: all m_Script match script_types[sti] 100%.")

    # 3. Check AssetBundle container and m_PreloadTable
    ab_obj = next(o for o in sf.objects.values() if o.type.name == "AssetBundle")
    ab_tt = ab_obj.read_typetree()
    pt = ab_tt["m_PreloadTable"]
    container = ab_tt["m_Container"]
    assert len(container) == 2, f"Expected 2 container items, got {len(container)}"
    assert "swoop_gs_deluxe2008" in ab_tt.get("m_Name", "").lower(), f"Unrenamed m_Name: {ab_tt.get('m_Name')}"
    assert "swoop_gs_deluxe2008" in container[0][0].lower(), f"Unrenamed main container key: {container[0][0]}"
    assert "swoop_gs_deluxe2008" in container[1][0].lower(), f"Unrenamed lw container key: {container[1][0]}"

    p0 = container[0][1]["preloadIndex"]
    s0 = container[0][1]["preloadSize"]
    p1 = container[1][1]["preloadIndex"]
    s1 = container[1][1]["preloadSize"]
    assert p0 == 0, f"First preloadIndex must be 0, got {p0}"
    assert p1 == s0, f"Second preloadIndex {p1} must match first preloadSize {s0}"
    assert s0 + s1 == len(pt), f"Sum of preload sizes {s0}+{s1} != PreloadTable len {len(pt)}"
    print(f"  [PASS] Container keys & slices strictly contiguous: [0:{s0}] + [{s0}:{s0+s1}] == {len(pt)} items.")

    # 4. Check Meshes & BoneNameHashes
    mesh_robot = obj_map[8801638638334271379].read_typetree()
    mesh_veh = obj_map[733405694182770835].read_typetree()
    assert mesh_robot["m_Name"] == "cha_swoop_gs_00"
    assert len(mesh_robot["m_BoneNameHashes"]) == 78 and mesh_robot["m_RootBoneNameHash"] != 0
    assert mesh_veh["m_Name"] == "cha_swoop_gs_01"
    assert len(mesh_veh["m_BoneNameHashes"]) == 29 and mesh_veh["m_RootBoneNameHash"] != 0
    print(f"  [PASS] Robot and Vehicle meshes & BoneNameHashes (78 / 29) validated.")

    # 5. Check Swoop Textures (non-clobbered, 2048x2048, unstreamed, RGBA32 / RGB24)
    expected_texs = {
        7894975478666169647: ("cha_swoop_main_Diffuse", 4),
        -4178640796595132748: ("cha_swoop_main_Normal", 4),
        4783134961327542118: ("cha_swoop_main_RAOE", 3),
        8532584703776603498: ("cha_swoop_vh_Diffuse", 4),
        5290645072316765759: ("cha_swoop_vh_Normal", 4),
    }
    for tpid, (tname, tfmt) in expected_texs.items():
        tt = obj_map[tpid].read_typetree()
        assert tt["m_Name"] == tname, f"Texture {tpid} name={tt['m_Name']} != {tname}!"
        assert tt["m_Width"] == 2048 and tt["m_Height"] == 2048, f"Texture {tname} size {tt['m_Width']}x{tt['m_Height']} != 2048x2048!"
        assert tt["m_TextureFormat"] == tfmt, f"Texture {tname} fmt={tt['m_TextureFormat']} != {tfmt}!"
        assert tt["m_StreamData"]["path"] == "", f"Texture {tname} still streamed: {tt['m_StreamData']}"
    print(f"  [PASS] All 5 Swoop 2048x2048 PBR Textures verified unstreamed & un-clobbered.")

    # 6. Check Materials m_Scale=(1,1) and m_Offset=(0,0) + SMR materials (2 slots on Robot, 1 slot on Vehicle)
    for mpid in (1469909421462177924, 3595971348910711679, 3520121911555544087):
        mtt = obj_map[mpid].read_typetree()
        for k, v in mtt["m_SavedProperties"]["m_TexEnvs"]:
            assert v["m_Scale"] == {"x": 1.0, "y": 1.0}, f"Mat {mpid} {k} bad m_Scale={v['m_Scale']}"
            assert v["m_Offset"] == {"x": 0.0, "y": 0.0}, f"Mat {mpid} {k} bad m_Offset={v['m_Offset']}"
    for spid in (-3606013326717668247, 8363741050498555038):
        assert [m["m_PathID"] for m in obj_map[spid].read_typetree()["m_Materials"]] == [1469909421462177924, 3595971348910711679]
    for spid in (-1331665652208216405, 4450385079657545705):
        assert [m["m_PathID"] for m in obj_map[spid].read_typetree()["m_Materials"]] == [3520121911555544087]
    print(f"  [PASS] Robot (2-mat Blue/Red) & Vehicle Materials UV Scale=(1,1) Offset=(0,0) and SMR materials verified.")

    # 7. Check ZERO active _wpns_ renderers under Main/LW Prefabs
    for root_pid in (1529847556182042256, -4280993829309278178):
        stack = [root_pid]
        seen = set()
        while stack:
            gpid = stack.pop()
            if gpid in seen or gpid not in obj_map:
                continue
            seen.add(gpid)
            gtt = obj_map[gpid].read_typetree()
            gname = gtt.get("m_Name", "")
            if "_wpns_" in gname.lower():
                assert not gtt["m_IsActive"], f"Legacy wpns GO still active: {gname} ({gpid})"
            for c in gtt["m_Component"]:
                co = obj_map.get(c["component"]["m_PathID"])
                if not co:
                    continue
                if "_wpns_" in gname.lower() and co.type.name in ("SkinnedMeshRenderer", "MeshRenderer"):
                    assert not co.read_typetree()["m_Enabled"], f"Legacy wpns SMR still enabled: {gname}"
                if co.type.name == "Transform":
                    tr_tt = co.read_typetree()
                    for ch in tr_tt["m_Children"]:
                        ch_tr = obj_map.get(ch["m_PathID"])
                        if ch_tr:
                            stack.append(ch_tr.read_typetree()["m_GameObject"]["m_PathID"])
    print(f"  [PASS] ZERO active/enabled legacy Ramjet _wpns_ renderers on Main and LW prefabs.")

    # 8. Check Controllers (Starscream airborne Heavy + WingFlap) & Fireball GO & PreloadTable external check
    fight_aoc = obj_map[6432204470035570307].read_typetree()
    assert fight_aoc["m_Clips"][58]["m_OverrideClip"] == {"m_FileID": 5, "m_PathID": 7645321843667068633}
    assert any(p["m_FileID"] == 5 and p["m_PathID"] == 7645321843667068633 for p in pt), "Missing (5, StarScream_Normal_attackHeavy) in PreloadTable!"
    assert not any(p["m_FileID"] == 3 and p["m_PathID"] == 7645321843667068633 for p in pt), "Broken (3, 7645321843667068633) still in PreloadTable!"
    jet_aoc = obj_map[-6340484879223379266].read_typetree()
    for slot in (5, 12, 16):
        assert jet_aoc["m_Clips"][slot]["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": 7111222233334444555}
    for slot, expected_pid in ((4, 7111222233334444556), (10, 7111222233334444557), (11, 7111222233334444558), (13, 7111222233334444559), (14, 7111222233334444560), (15, 7111222233334444561), (17, 7111222233334444562)):
        assert jet_aoc["m_Clips"][slot]["m_OverrideClip"] == {"m_FileID": 0, "m_PathID": expected_pid}, (
            f"Jet AOC slot[{slot}] not wrapped: {jet_aoc['m_Clips'][slot]['m_OverrideClip']}"
        )
        assert any(p["m_FileID"] == 0 and p["m_PathID"] == expected_pid for p in pt), f"Wrapped clip {expected_pid} missing from PreloadTable!"
    go_names = {o.read_typetree().get("m_Name") for o in sf.objects.values() if o.type.name == "GameObject"}
    assert "projectile_grimlock_fireball" in go_names, "projectile_grimlock_fireball missing from GameObjects!"
    for tr_pid in (-6891910190203298850, -6726056130619506655):
        scl = obj_map[tr_pid].read_typetree()["m_LocalScale"]
        assert abs(scl["x"] - 1.53) < 0.01 and abs(scl["y"] - 1.53) < 0.01 and abs(scl["z"] - 1.53) < 0.01, (
            f"Vehicle Reference {tr_pid} scale {scl} != 1.53!"
        )
    print(f"  [PASS] Fight AOC [58]=(5, StarScream_Normal_attackHeavy), Jet AOC [5,12,16]=WingFlap, 1.53x Pteranodon scale, Fireball cloned.")

    # 9. Check moves.assetbundle
    print(f"\n=== Validating {MOVES_PATH} ===")
    env_m = UnityPy.load(str(MOVES_PATH))
    moves = [o for o in env_m.objects if o.type.name == "TextAsset"]
    print(f"  Total moves count: {len(moves)}")
    assert len(moves) >= 945, f"CRITICAL: moves count {len(moves)} < 945!"

    move_names = [o.read_typetree().get("m_Name") for o in moves]
    assert "move_heavy_swoop" in move_names, "move_heavy_swoop missing from moves.assetbundle!"
    assert any("chromia" in n.lower() for n in move_names), "Chromia moves missing!"
    assert any("deadend" in n.lower() or "dead_end" in n.lower() for n in move_names), "Dead End moves missing!"
    swoop_mv = next(o.read_typetree() for o in moves if o.read_typetree().get("m_Name") == "move_heavy_swoop")
    scr = json.loads(swoop_mv["m_Script"])
    projs = [e for e in scr["moves"]["events"] if e.get("type") == "ProjectileMoveEvent"]
    assert projs and projs[0]["pn"] == "projectile_grimlock_fireball" and projs[0]["po"]["o"]["y"] >= 11.0
    print(f"  [PASS] moves.assetbundle validated: {len(moves)} moves, move_heavy_swoop fires fireball at {projs[0]['po']['o']}.")

    print("\n🎉 ALL GATE CHECKS PASSED WITH 0 ERRORS!")


if __name__ == "__main__":
    validate()
