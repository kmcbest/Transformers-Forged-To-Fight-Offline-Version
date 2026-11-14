import os
import sys
import json
import math
import zlib
import numpy as np
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BUNDLE_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
OUT_DIR = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader"
os.makedirs(OUT_DIR, exist_ok=True)


def unity_crc32(s: str) -> int:
    # Unity m_BoneNameHashes uses standard CRC32 (wait - verify against dump!)
    return zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF


def mat4_from_dict(d):
    return np.array(
        [
            [d["e00"], d["e01"], d["e02"], d["e03"]],
            [d["e10"], d["e11"], d["e12"], d["e13"]],
            [d["e20"], d["e21"], d["e22"], d["e23"]],
            [d["e30"], d["e31"], d["e32"], d["e33"]],
        ],
        dtype=np.float64,
    )


def unity_trs_to_mat(pos, rot_xyzw, scl):
    x, y, z, w = rot_xyzw["x"], rot_xyzw["y"], rot_xyzw["z"], rot_xyzw["w"]
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    r = np.array(
        [
            [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy), pos["x"]],
            [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx), pos["y"]],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy), pos["z"]],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    s = np.diag([scl["x"], scl["y"], scl["z"], 1.0])
    return r @ s


def main():
    env = UnityPy.load(BUNDLE_PATH)

    go_map = {}
    tf_map = {}
    tf_by_go = {}
    smrs = []
    meshes = {}
    texs = {}

    for obj in env.objects:
        t = obj.type.name
        if t == "GameObject":
            go_map[obj.path_id] = obj.read_typetree()
        elif t == "Transform":
            tt = obj.read_typetree()
            tf_map[obj.path_id] = tt
            tf_by_go[tt["m_GameObject"]["m_PathID"]] = obj.path_id
        elif t == "SkinnedMeshRenderer":
            smrs.append((obj.path_id, obj.read_typetree()))
        elif t == "Mesh":
            meshes[obj.path_id] = obj
        elif t == "Texture2D":
            texs[obj.path_id] = obj

    def get_tf_name(tf_pid):
        tf = tf_map.get(tf_pid)
        if not tf:
            return "?"
        go = go_map.get(tf["m_GameObject"]["m_PathID"], {})
        return go.get("m_Name", "?")

    def get_tf_path(tf_pid):
        parts = []
        cur = tf_pid
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            tf = tf_map.get(cur)
            if not tf:
                break
            parts.append(get_tf_name(cur))
            cur = tf.get("m_Father", {}).get("m_PathID", 0)
        return "/".join(reversed(parts))

    def get_tf_world_mat(tf_pid):
        chain = []
        cur = tf_pid
        while cur:
            tf = tf_map.get(cur)
            if not tf:
                break
            chain.append(tf)
            cur = tf.get("m_Father", {}).get("m_PathID", 0)
        m = np.eye(4, dtype=np.float64)
        for tf in reversed(chain):
            m = m @ unity_trs_to_mat(tf["m_LocalPosition"], tf["m_LocalRotation"], tf["m_LocalScale"])
        return m

    # Export meshes as OBJ + inspect vertex/bone summary
    print("=== Export OBJs ===")
    for pid, obj in meshes.items():
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if not name.startswith("cha_ultramagnus"):
            continue
        suffix = ""
        if name.endswith("_00"):
            suffix = "_robot"
        elif name.endswith("_01"):
            suffix = "_alt"
        out_obj = os.path.join(OUT_DIR, f"{name}{suffix}.obj")
        data = obj.read().export()
        with open(out_obj, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"  Wrote {out_obj} ({len(data)} bytes)")

    # Export character textures
    print("\n=== Export Textures ===")
    for pid, obj in texs.items():
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if any(k in name for k in ["ultramagnus", "main", "tform", "wpns"]):
            img = obj.read().image
            out_png = os.path.join(OUT_DIR, f"tex_{name}.png")
            img.save(out_png)
            print(f"  Wrote {out_png} ({img.size})")

    # Inspect Showcase prefab SMRs and dump skeleton_hierarchy.json + per-mesh bone jsons
    smr_records = []
    showcase_smr_by_mesh = {}
    for smr_pid, tt in smrs:
        go_pid = tt["m_GameObject"]["m_PathID"]
        tf_pid = tf_by_go[go_pid]
        hpath = get_tf_path(tf_pid)
        prefab = "Combat_LW" if hpath.startswith("UltraMagnus_GS_Leader_lw") else ("Showcase" if hpath.startswith("UltraMagnus_GS_Leader") else "Other")
        mesh_pid = tt["m_Mesh"]["m_PathID"]
        mesh_tt = meshes[mesh_pid].read_typetree()
        mesh_name = mesh_tt.get("m_Name", "?")
        root_bone_tf = tt["m_RootBone"]["m_PathID"]
        root_bone_path = get_tf_path(root_bone_tf)
        bones = tt.get("m_Bones", [])
        smr_records.append(
            {
                "path_id": smr_pid,
                "prefab": prefab,
                "hierarchy_path": hpath,
                "mesh_name": mesh_name,
                "mesh_pid": mesh_pid,
                "enabled": tt.get("m_Enabled", True),
                "bone_count": len(bones),
                "root_bone": root_bone_path,
            }
        )
        if prefab == "Showcase":
            showcase_smr_by_mesh[mesh_name] = (tt, mesh_tt)

    with open(os.path.join(OUT_DIR, "skeleton_hierarchy.json"), "w", encoding="utf-8") as f:
        json.dump({"bundle_name": "ultramagnus_gs_leader.assetbundle", "skinned_mesh_renderers": smr_records}, f, indent=2)

    # Find Showcase character_model World Transform root offset
    for mesh_name, (smr_tt, mesh_tt) in sorted(showcase_smr_by_mesh.items()):
        bones = smr_tt["m_Bones"]
        raw_bps = mesh_tt["m_BindPose"]
        hashes = mesh_tt.get("m_BoneNameHashes", [])
        root_hash = mesh_tt.get("m_RootBoneNameHash", 0)
        bone_entries = []
        print(f"\n=== Mesh '{mesh_name}' ({len(bones)} bones, bindposes={len(raw_bps)}, hashes={len(hashes)}) ===")
        for idx, b in enumerate(bones):
            btf_pid = b["m_PathID"]
            bname = get_tf_name(btf_pid)
            bpath = get_tf_path(btf_pid)
            ftf_pid = tf_map[btf_pid]["m_Father"]["m_PathID"]
            pname = get_tf_name(ftf_pid) if ftf_pid else ""
            bp_mat = mat4_from_dict(raw_bps[idx]) if idx < len(raw_bps) else np.eye(4)
            inv_bp = np.linalg.inv(bp_mat)
            # In Unity bindpose, inv(bp) is bone_to_meshMatrix. Pos in Unity mesh space = inv_bp[:3, 3]
            upos = inv_bp[:3, 3]
            # Wait: check Unity transform world pos too (relative to character_model)
            wmat = get_tf_world_mat(btf_pid)
            wpos = wmat[:3, 3]
            tf_data = tf_map[btf_pid]
            bone_entries.append(
                {
                    "index": idx,
                    "name": bname,
                    "parent": pname,
                    "hierarchy_path": bpath,
                    "hash_in_mesh": hashes[idx] if idx < len(hashes) else 0,
                    "unity_bindpose_pos": [float(upos[0]), float(upos[1]), float(upos[2])],
                    "unity_world_pos": [float(wpos[0]), float(wpos[1]), float(wpos[2])],
                    "local_pos": [float(tf_data["m_LocalPosition"]["x"]), float(tf_data["m_LocalPosition"]["y"]), float(tf_data["m_LocalPosition"]["z"])],
                    "inv_bindpose_4x4": inv_bp.tolist(),
                    "raw_bindpose": raw_bps[idx] if idx < len(raw_bps) else None,
                }
            )
            if mesh_name.endswith("_01") or "Finger" in bname or "Thumb" in bname or idx < 18 or "Shoulder" in bname or "Arm" in bname or "Hand" in bname or "wpns" in mesh_name:
                print(
                    f"  [{idx:2d}] {bname:30s} parent={pname:22s} "
                    f"u_pos=({upos[0]:7.3f},{upos[1]:7.3f},{upos[2]:7.3f}) "
                    f"hash={hashes[idx] if idx < len(hashes) else 0}"
                )

        # Also check skin vertex weight counts per bone
        try:
            mesh_obj_py = meshes[smr_tt["m_Mesh"]["m_PathID"]].read()
            skin = getattr(mesh_obj_py, "m_Skin", None)
            if skin:
                counts = [0] * len(bones)
                for inf in skin:
                    for b_idx, w in zip(inf.boneIndex, inf.weight):
                        if w > 1e-4 and 0 <= b_idx < len(counts):
                            counts[b_idx] += 1
                print(f"  Bone vertex counts (non-zero):")
                for idx, c in enumerate(counts):
                    if c > 0 or mesh_name.endswith("_01"):
                        print(f"    [{idx:2d}] {bone_entries[idx]['name']:30s}: {c} weighted verts")
        except Exception as e:
            print(f"  Skin weight count check error: {e}")

        out_json = os.path.join(OUT_DIR, f"{mesh_name}_bones.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mesh_name": mesh_name,
                    "root_bone_name": get_tf_name(smr_tt["m_RootBone"]["m_PathID"]),
                    "root_bone_name_hash": root_hash,
                    "bone_count": len(bones),
                    "raw_m_BindPose": raw_bps,
                    "m_BoneNameHashes": hashes,
                    "bones": bone_entries,
                },
                f,
                indent=2,
            )
        print(f"  Wrote {out_json}")

    # Inspect submesh material assignments and bounding boxes of _00 and _01
    print("\n=== Full Showcase Hierarchy (character_model) ===")
    for obj_pid, tf in tf_map.items():
        if get_tf_name(obj_pid) == "character_model" and get_tf_path(obj_pid).startswith("UltraMagnus_GS_Leader/"):
            def dump_full(tpid, d=0):
                print(f"{'  '*d}{get_tf_name(tpid)} pos=({tf_map[tpid]['m_LocalPosition']['x']:.3f},{tf_map[tpid]['m_LocalPosition']['y']:.3f},{tf_map[tpid]['m_LocalPosition']['z']:.3f})")
                for c in tf_map[tpid].get("m_Children", []):
                    dump_full(c["m_PathID"], d + 1)
            dump_full(obj_pid)


if __name__ == "__main__":
    main()
