import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import numpy as np
import UnityPy

BUNDLE_PATH = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle"
OUT_DIR = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference"
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
        suffix = "_robot" if name.endswith("_00") else ("_car" if name.endswith("_01") else "")
        out_obj = os.path.join(OUT_DIR, f"{name}{suffix}.obj")
        try:
            data = obj.read().export()
            with open(out_obj, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"  Wrote {out_obj} ({len(data)} bytes)")
        except Exception as e:
            print(f"  Could not export OBJ for {name}: {e}")
        mesh_info[name] = {
            "pid": pid,
            "vertexCount": tt.get("m_VertexData", {}).get("m_VertexCount", 0),
            "boneCount": len(tt.get("m_BoneNameHashes", [])),
            "boneHashes": tt.get("m_BoneNameHashes", []),
            "rootBoneHash": tt.get("m_RootBoneNameHash", 0),
            "submeshes": len(tt.get("m_SubMeshes", [])),
            "bindposes": tt.get("m_BindPose", []),
        }

    print("\n=== Exporting Avatar Bone Information ===")
    avatar_info = {}
    for pid, obj in avatars.items():
        av = obj.read_typetree()
        aname = av.get("m_Name", "")
        tos = av.get("m_TOS", [])
        tos_dict = {entry[0]: entry[1] for entry in tos}
        avatar_info[aname] = {
            "pid": pid,
            "scale": av.get("m_Avatar", {}).get("m_Scale", 1.0),
            "tos": tos_dict,
        }
        print(f"  Avatar '{aname}': scale={avatar_info[aname]['scale']}, {len(tos_dict)} bones")

    summary = {
        "donorBundle": BUNDLE_PATH,
        "meshes": mesh_info,
        "avatars": avatar_info,
    }
    summary_path = os.path.join(OUT_DIR, "donor_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote summary to {summary_path}")


if __name__ == "__main__":
    main()
