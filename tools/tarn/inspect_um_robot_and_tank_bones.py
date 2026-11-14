import json
import sys
import numpy as np
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UM_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\ultramagnus_gs_leader")


def unity_to_blender_pos(upos):
    # Blender import_obj(up_axis=Y, forward_axis=-Z): Wait! Check exact mapping used in cha_megatron_00_robot.obj!
    # Wait: in render_um_donor_vs_tarn.py, bpy.ops.wm.obj_import converted Unity (x, y, z) -> Blender (-x, -z, y) OR (x, z, y)?
    # Actually let's check both by inspecting OBJ vertices directly!
    return [-upos[0], -upos[2], upos[1]]


def main():
    # Check cha_ultramagnus_gs_leader_00_robot.obj X/Y/Z ranges of vertices to verify Unity->Blender axis convention
    obj_path = UM_DIR / "cha_ultramagnus_gs_leader_00_robot.obj"
    verts = []
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                _, x, y, z = line.split()
                verts.append([float(x), float(y), float(z)])
    v = np.array(verts)
    print(f"UM _00 OBJ vertices ({len(v)}): X=[{v[:,0].min():.3f},{v[:,0].max():.3f}] Y=[{v[:,1].min():.3f},{v[:,1].max():.3f}] Z=[{v[:,2].min():.3f},{v[:,2].max():.3f}]")

    robo = json.loads((UM_DIR / "cha_ultramagnus_gs_leader_00_bones.json").read_text(encoding="utf-8"))
    print(f"\n=== ALL {robo['bone_count']} Robot Bones of cha_ultramagnus_gs_leader_00 ===")
    for b in robo["bones"]:
        up = b["unity_bindpose_pos"]
        wp = b["unity_world_pos"]
        diff = np.linalg.norm(np.array(up) - np.array(wp))
        print(
            f"  [{b['index']:2d}] {b['name']:24s} parent={b['parent']:22s} "
            f"u_pos=({up[0]:7.3f},{up[1]:7.3f},{up[2]:7.3f}) "
            f"w_diff={diff:.4f}"
        )

    alt = json.loads((UM_DIR / "cha_ultramagnus_gs_leader_01_bones.json").read_text(encoding="utf-8"))
    print(f"\n=== ALL {alt['bone_count']} Alt Bones of cha_ultramagnus_gs_leader_01 ===")
    for b in alt["bones"]:
        up = b["unity_bindpose_pos"]
        print(
            f"  [{b['index']:2d}] {b['name']:34s} parent={b['parent']:28s} "
            f"u_pos=({up[0]:7.3f},{up[1]:7.3f},{up[2]:7.3f})"
        )


if __name__ == "__main__":
    main()
