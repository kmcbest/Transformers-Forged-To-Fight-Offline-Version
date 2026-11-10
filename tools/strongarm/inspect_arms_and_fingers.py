import sys
import json
import math
import numpy as np
import bpy
from pathlib import Path

prowl_rig_path = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json")
with open(prowl_rig_path, "r", encoding="utf-8") as f:
    prowl_bones = json.load(f)

pb_bl = {}
for b in prowl_bones:
    bp = b["bindpose"]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    ux, uy, uz = inv[0, 3], inv[1, 3], inv[2, 3]
    pb_bl[b["name"]] = (-ux, uz, uy)

print("=== Prowl Left Arm & Finger Bones (Blender space: +X=Left, +Y=Fwd, +Z=Up) ===")
for bn in sorted(pb_bl.keys()):
    if bn.startswith("Left") or bn in ("Spine", "Spine1", "Hips", "Head"):
        x, y, z = pb_bl[bn]
        print(f"  {bn:22s}: ({x:+.3f}, {y:+.3f}, {z:+.3f})")

la = np.array(pb_bl["LeftArm"])
lfa = np.array(pb_bl["LeftForeArm"])
lh = np.array(pb_bl["LeftHand"])
v_arm = lfa - la
v_fa = lh - lfa
ang_arm = math.degrees(math.atan2(v_arm[0], -v_arm[2]))
ang_fa  = math.degrees(math.atan2(v_fa[0], -v_fa[2]))
print(f"\nProwl UpperArm flare from vertical (+X outward): {ang_arm:.2f} deg, vec={v_arm.round(3)}")
print(f"Prowl ForeArm  flare from vertical (+X outward): {ang_fa:.2f} deg, vec={v_fa.round(3)}")

# Also inspect raw Strongarm.fbx original armature, hand/finger objects & vertex groups
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
print(f"\n=== Strongarm.fbx Original Armature ({len(orig_arm.data.bones)} bones) ===")
for b in orig_arm.data.bones:
    if any(k in b.name.lower() for k in ("arm", "elbow", "shoulder", "hand", "wrist", "thumb", "index", "middle", "ring", "pinky", "finger", "_l", "_r")):
        if not ("_r" in b.name.lower() and not "ring" in b.name.lower()):
            print(f"  bone: {b.name:30s} head=({b.head_local.x:+.4f}, {b.head_local.y:+.4f}, {b.head_local.z:+.4f})")

print("\n=== Strongarm.fbx Hand / Finger / Arm Mesh Objects & Vertex Groups ===")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type == 'MESH' and any(k in o.name.lower() for k in ("hand", "palm", "finger", "arm", "shoulder")):
        if "_r" not in o.name.lower() or "arm" in o.name.lower() and "_l" in o.name.lower():
            vgs = [g.name for g in o.vertex_groups]
            # print active vgroups (with weight > 0.01)
            active_vgs = set()
            for v in o.data.vertices:
                for ge in v.groups:
                    if ge.weight > 0.01:
                        active_vgs.add(o.vertex_groups[ge.group].name)
            vs = [o.matrix_world @ v.co for v in o.data.vertices]
            cx = sum(v.x for v in vs)/max(len(vs),1)
            cy = sum(v.y for v in vs)/max(len(vs),1)
            cz = sum(v.z for v in vs)/max(len(vs),1)
            print(f"  {o.name:28s}: verts={len(vs):4d} center=({cx:+.4f},{cy:+.4f},{cz:+.4f}) vgs={sorted(active_vgs)}")
