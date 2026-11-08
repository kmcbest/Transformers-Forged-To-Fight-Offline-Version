import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
armlo_l = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoL.mo.dmx"]
armlo_r = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoR.mo.dmx"]

scale_factor = 2.05
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.context.view_layer.update()

def find_connected_shells(mesh_obj, vg_idx, ref_head_local, dir_local, arm_inv):
    vset = {vi for vi, v in enumerate(mesh_obj.data.vertices) if any(g.group == vg_idx and g.weight > 0.5 for g in v.groups)}
    adj = {vi: set() for vi in vset}
    for e in mesh_obj.data.edges:
        u, w = e.vertices
        if u in vset and w in vset:
            adj[u].add(w)
            adj[w].add(u)
    visited = set()
    shells = []
    for vi in vset:
        if vi not in visited:
            comp = []
            stack = [vi]
            visited.add(vi)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nb in adj[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            pts_arm = [arm_inv @ (mesh_obj.matrix_world @ mesh_obj.data.vertices[c].co) for c in comp]
            projs = [(p - ref_head_local).dot(dir_local) for p in pts_arm]
            shells.append((min(projs), max(projs), comp))
    shells.sort(key=lambda x: x[0])
    return shells

arm_inv = arm.matrix_world.inverted()
for side, mesh_obj in [("L", armlo_l), ("R", armlo_r)]:
    print(f"\n--- Side {side} ---")
    for fn in ("index", "middle", "ring", "pinky"):
        b0 = arm.data.bones[f"bip_{fn}_0_{side}"]
        b1 = arm.data.bones[f"bip_{fn}_1_{side}"]
        dir_local = (b1.head_local - b0.head_local).normalized()
        vg1_idx = mesh_obj.vertex_groups[f"bip_{fn}_1_{side}"].index
        shells = find_connected_shells(mesh_obj, vg1_idx, b1.head_local, dir_local, arm_inv)
        print(f"  {fn:7s}: shells={len(shells)}, counts={[len(s[2]) for s in shells]}")
        
    b0_t = arm.data.bones[f"bip_thumb_0_{side}"]
    b1_t = arm.data.bones[f"bip_thumb_1_{side}"]
    dir_t = (b1_t.head_local - b0_t.head_local).normalized()
    vgt_idx = mesh_obj.vertex_groups[f"bip_thumb_1_{side}"].index
    t_shells = find_connected_shells(mesh_obj, vgt_idx, b1_t.head_local, dir_t, arm_inv)
    print(f"  thumb  : shells={len(t_shells)}, counts={[len(s[2]) for s in t_shells]}")
