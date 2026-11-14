import sys
import json
import numpy as np
import UnityPy
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UM_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
UM_BONES_01 = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader\cha_ultramagnus_gs_leader_01_bones.json")


def parse_obj_verts(obj_text):
    vs = []
    for line in obj_text.splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()
            # Note: UnityPy Mesh.export() exports Unity coords directly without flipping X?
            vs.append([float(x), float(y), float(z)])
    return np.array(vs)


def main():
    env = UnityPy.load(UM_PATH)
    bones_spec = json.loads(UM_BONES_01.read_text(encoding="utf-8"))
    bones = bones_spec["bones"]

    for o in env.objects:
        if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_ultramagnus_gs_leader_01":
            m = o.read()
            tt = o.read_typetree()
            verts = parse_obj_verts(m.export())
            skin = tt.get("m_Skin") or []
            print(f"Mesh _01: verts={len(verts)} skin={len(skin)}")
            by_bone = {i: [] for i in range(len(bones))}
            for vi, inf in enumerate(skin):
                b0 = inf["boneIndex[0]"]
                w0 = inf["weight[0]"]
                if w0 > 0.3 and 0 <= b0 < len(bones):
                    by_bone[b0].append(vi)
            print("Weighted regions per bone in cha_ultramagnus_gs_leader_01 (Unity space: Y=up, Z=forward):")
            for i, b in enumerate(bones):
                vis = by_bone[i]
                up = b["unity_bindpose_pos"]
                if vis:
                    sub = verts[vis]
                    print(
                        f"  [{i:2d}] {b['name']:32s} verts={len(vis):5d} parent={b['parent']:24s} "
                        f"u_pos=({up[0]:6.2f},{up[1]:6.2f},{up[2]:6.2f}) "
                        f"Y=[{sub[:,1].min():5.2f},{sub[:,1].max():5.2f}] Z=[{sub[:,2].min():6.2f},{sub[:,2].max():6.2f}]"
                    )
                else:
                    print(
                        f"  [{i:2d}] {b['name']:32s} verts=    0 parent={b['parent']:24s} "
                        f"u_pos=({up[0]:6.2f},{up[1]:6.2f},{up[2]:6.2f})"
                    )


if __name__ == "__main__":
    main()
