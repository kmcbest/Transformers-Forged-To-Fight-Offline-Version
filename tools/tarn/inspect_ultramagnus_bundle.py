import os
import sys
import json
import struct
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BUNDLE_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
OUT_DIR = r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader"
os.makedirs(OUT_DIR, exist_ok=True)


def get_name(obj_reader):
    try:
        t = obj_reader.read_typetree()
        return t.get("m_Name", "")
    except Exception:
        return ""


def main():
    env = UnityPy.load(BUNDLE_PATH)
    print(f"Loaded bundle: {BUNDLE_PATH}")
    print(f"CAB files: {list(env.cabs.keys())}")

    by_type = {}
    for obj in env.objects:
        by_type.setdefault(obj.type.name, []).append(obj)

    print("Object counts by type:")
    for t, objs in sorted(by_type.items()):
        print(f"  {t}: {len(objs)}")

    # AssetBundle container
    for obj in by_type.get("AssetBundle", []):
        tt = obj.read_typetree()
        print("\nAssetBundle m_Container keys:")
        for k, v in tt.get("m_Container", []):
            print(f"  {k} -> PID={v['asset']['m_PathID']}")
        print(f"m_MainAsset: {tt.get('m_MainAsset')}")

    # GameObjects & Transforms hierarchy helper
    go_map = {}
    tf_map = {}
    for obj in by_type.get("GameObject", []):
        tt = obj.read_typetree()
        go_map[obj.path_id] = tt
    for obj in by_type.get("Transform", []):
        tt = obj.read_typetree()
        tf_map[obj.path_id] = tt

    def print_tree(tf_pid, depth=0, max_depth=4):
        tf = tf_map.get(tf_pid)
        if not tf:
            return
        go_pid = tf.get("m_GameObject", {}).get("m_PathID", 0)
        go = go_map.get(go_pid, {})
        name = go.get("m_Name", "?")
        pos = tf.get("m_LocalPosition", {})
        rot = tf.get("m_LocalRotation", {})
        scl = tf.get("m_LocalScale", {})
        print(
            f"{'  ' * depth}- {name} (GO={go_pid}, TF={tf_pid}) "
            f"pos=({pos.get('x',0):.3f},{pos.get('y',0):.3f},{pos.get('z',0):.3f}) "
            f"scl=({scl.get('x',1):.3f},{scl.get('y',1):.3f},{scl.get('z',1):.3f})"
        )
        if depth < max_depth:
            for ch in tf.get("m_Children", []):
                print_tree(ch.get("m_PathID", 0), depth + 1, max_depth)

    print("\nRoot Transforms:")
    for tf_pid, tf in tf_map.items():
        if tf.get("m_Father", {}).get("m_PathID", 0) == 0:
            print_tree(tf_pid, 0, max_depth=3)

    # SkinnedMeshRenderer & MeshRenderer
    mesh_map = {obj.path_id: obj for obj in by_type.get("Mesh", [])}
    mat_map = {obj.path_id: obj for obj in by_type.get("Material", [])}
    tex_map = {obj.path_id: obj for obj in by_type.get("Texture2D", [])}

    print("\nSkinnedMeshRenderers:")
    for obj in by_type.get("SkinnedMeshRenderer", []):
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID", 0)
        go_name = go_map.get(go_pid, {}).get("m_Name", "?")
        m_pid = tt.get("m_Mesh", {}).get("m_PathID", 0)
        m_name = get_name(mesh_map[m_pid]) if m_pid in mesh_map else "MISSING"
        mats = [get_name(mat_map[m["m_PathID"]]) if m["m_PathID"] in mat_map else str(m["m_PathID"]) for m in tt.get("m_Materials", [])]
        bones = tt.get("m_Bones", [])
        root_bone_pid = tt.get("m_RootBone", {}).get("m_PathID", 0)
        root_bone_go_pid = tf_map.get(root_bone_pid, {}).get("m_GameObject", {}).get("m_PathID", 0)
        root_bone_name = go_map.get(root_bone_go_pid, {}).get("m_Name", "?")
        print(
            f"  SMR PID={obj.path_id} GO='{go_name}' ({go_pid}) enabled={tt.get('m_Enabled')} "
            f"mesh='{m_name}'({m_pid}) bones={len(bones)} rootBone='{root_bone_name}' mats={mats}"
        )

    print("\nMeshRenderers:")
    for obj in by_type.get("MeshRenderer", []):
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID", 0)
        go_name = go_map.get(go_pid, {}).get("m_Name", "?")
        mats = [get_name(mat_map[m["m_PathID"]]) if m["m_PathID"] in mat_map else str(m["m_PathID"]) for m in tt.get("m_Materials", [])]
        print(f"  MR PID={obj.path_id} GO='{go_name}' ({go_pid}) enabled={tt.get('m_Enabled')} mats={mats}")

    print("\nMeshes:")
    for obj in by_type.get("Mesh", []):
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        vcount = tt.get("m_VertexData", {}).get("m_VertexCount", 0)
        bindposes = tt.get("m_BindPose", [])
        bones_hashes = tt.get("m_BoneNameHashes", [])
        submeshes = tt.get("m_SubMeshes", [])
        aabb = tt.get("m_LocalAABB", {})
        c = aabb.get("m_Center", {})
        e = aabb.get("m_Extent", {})
        print(
            f"  Mesh PID={obj.path_id} '{name}': verts={vcount}, submeshes={len(submeshes)}, "
            f"bindposes={len(bindposes)}, hashes={len(bones_hashes)}, "
            f"center=({c.get('x',0):.3f},{c.get('y',0):.3f},{c.get('z',0):.3f}), "
            f"extent=({e.get('x',0):.3f},{e.get('y',0):.3f},{e.get('z',0):.3f})"
        )

    print("\nMaterials:")
    mat_dump = {}
    for obj in by_type.get("Material", []):
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        sp = tt.get("m_SavedProperties", {})
        texs = {}
        for k, v in sp.get("m_TexEnvs", []):
            tpid = v.get("m_Texture", {}).get("m_PathID", 0)
            tname = get_name(tex_map[tpid]) if tpid in tex_map else str(tpid)
            texs[k] = {"path_id": tpid, "name": tname, "scale": v.get("m_Scale"), "offset": v.get("m_Offset")}
        floats = {k: v for k, v in sp.get("m_Floats", [])}
        cols = {k: v for k, v in sp.get("m_Colors", [])}
        mat_dump[f"{name}_{obj.path_id}"] = {"path_id": obj.path_id, "name": name, "texs": texs, "floats": floats, "cols": cols}
        print(f"  Mat PID={obj.path_id} '{name}': texs={ {k: v['name'] for k, v in texs.items()} }")

    with open(os.path.join(OUT_DIR, "materials_dump.json"), "w", encoding="utf-8") as f:
        json.dump(mat_dump, f, indent=2)

    print("\nTexture2Ds:")
    for obj in by_type.get("Texture2D", []):
        tt = obj.read_typetree()
        print(
            f"  Tex PID={obj.path_id} '{tt.get('m_Name','')}' "
            f"{tt.get('m_Width')}x{tt.get('m_Height')} fmt={tt.get('m_TextureFormat')}"
        )

    print("\nAnimationClips:")
    for obj in by_type.get("AnimationClip", []):
        tt = obj.read_typetree()
        print(f"  Clip PID={obj.path_id} '{tt.get('m_Name','')}' len={tt.get('m_Length',0):.2f}s")

    print("\nParticleSystems (FX):")
    for obj in by_type.get("ParticleSystem", []):
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID", 0)
        go_name = go_map.get(go_pid, {}).get("m_Name", "?")
        print(f"  PS PID={obj.path_id} GO='{go_name}'")


if __name__ == "__main__":
    main()
