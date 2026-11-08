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
b0 = arm.data.bones["bip_index_0_L"]
b1 = arm.data.bones["bip_index_1_L"]
dir_local = (b1.head_local - b0.head_local).normalized()
vg_idx = armlo_l.vertex_groups["bip_index_1_L"].index
shells = find_connected_shells(armlo_l, vg_idx, b1.head_local, dir_local, arm_inv)
print("Index finger shells detail:")
for i, s in enumerate(shells):
    print(f"  Shell {i}: proj_min={s[0]:.4f}, proj_max={s[1]:.4f}, len={len(s[2])}")
