import os
import sys
import json
import zlib
import numpy as np
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUNDLE_PATH = os.path.join(ROOT, r"extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
OUT_DIR = os.path.join(ROOT, r"3rd-party-models\BlastOff\00_donor_reference")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    print(f"Loading {BUNDLE_PATH}")
    env = UnityPy.load(BUNDLE_PATH)

    go_map = {}
    tf_map = {}
    tf_by_go = {}
    meshes = {}
    texs = {}
    avatars = {}

    for obj in env.objects:
        t = obj.type.name
        if t == "GameObject":
            go_map[obj.path_id] = obj.read_typetree()
        elif t == "Transform":
            tt = obj.read_typetree()
            tf_map[obj.path_id] = tt
            tf_by_go[tt["m_GameObject"]["m_PathID"]] = obj.path_id
        elif t == "Mesh":
            meshes[obj.path_id] = obj
        elif t == "Texture2D":
            texs[obj.path_id] = obj
        elif t == "Avatar":
            avatars[obj.path_id] = obj

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

    print("=== Exporting Meshes ===")
    mesh_info = {}
    for pid, obj in meshes.items():
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        suffix = "_robot" if name.endswith("_00") else ("_jet" if name.endswith("_01") else "")
        out_obj = os.path.join(OUT_DIR, f"{name}{suffix}.obj")
        data = obj.read().export()
        with open(out_obj, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"  Wrote {out_obj} ({len(data)} bytes)")
        mesh_info[name] = {
            "pid": pid,
            "vertexCount": tt.get("m_VertexData", {}).get("m_VertexCount", 0),
            "boneCount": len(tt.get("m_BoneNameHashes", [])),
            "boneHashes": tt.get("m_BoneNameHashes", []),
            "rootBoneHash": tt.get("m_RootBoneNameHash", 0),
            "submeshes": len(tt.get("m_SubMeshes", [])),
            "bindposes": tt.get("m_BindPose", []),
        }

    print("\n=== Exporting Textures ===")
    for pid, obj in texs.items():
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if any(k in name.lower() for k in ["megatronus", "main", "tform", "wpns"]):
            try:
                img = obj.read().image
                out_png = os.path.join(OUT_DIR, f"tex_{name}.png")
                img.save(out_png)
                print(f"  Wrote {out_png} ({img.size})")
            except Exception as e:
                print(f"  Failed to export texture '{name}': {e}")

    print("\n=== Exporting Avatar Bone Information ===")
    avatar_info = {}
    for pid, obj in avatars.items():
        tt = obj.read_typetree()
        aname = tt.get("m_Name", "")
        tos = dict(tt.get("m_TOS", []))
        avatar_info[aname] = {
            "pid": pid,
            "tos": tos,
        }
        print(f"  Avatar '{aname}' with {len(tos)} TOS entries")

    print("\n=== Building Hierarchy and Summary ===")
    summary = {
        "meshes": mesh_info,
        "avatars": avatar_info,
        "transforms": {
            pid: {
                "name": get_tf_name(pid),
                "path": get_tf_path(pid),
                "localPos": tf["m_LocalPosition"],
                "localRot": tf["m_LocalRotation"],
                "localScale": tf["m_LocalScale"],
                "parent_pid": tf.get("m_Father", {}).get("m_PathID", 0),
            }
            for pid, tf in tf_map.items()
        },
    }
    summary_path = os.path.join(OUT_DIR, "donor_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
