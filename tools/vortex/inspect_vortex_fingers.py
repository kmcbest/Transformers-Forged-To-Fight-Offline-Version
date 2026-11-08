import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROBOT_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend")
bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))

arm = bpy.data.objects["Vortex_ARM"]
armlo_l = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoL.mo.dmx"]
armlo_r = bpy.data.objects["RB_Vortex_CHARSKEL_ArmLoR.mo.dmx"]

def find_connected_shells(mesh_obj, vg_idx):
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
            shells.append(comp)
    return shells

print("--- Inspecting Vortex Hand Fingers (Left Hand) ---")
for vg in armlo_l.vertex_groups:
    if "thumb" in vg.name or "index" in vg.name or "middle" in vg.name or "ring" in vg.name or "pinky" in vg.name:
        shells = find_connected_shells(armlo_l, vg.index)
        vcount = sum(len(s) for s in shells)
        print(f"  VG: {vg.name:20s} | Verts: {vcount:4d} | Shells: {len(shells)} | Sizes: {[len(s) for s in shells]}")

print("\n--- Inspecting Vortex Hand Fingers (Right Hand) ---")
for vg in armlo_r.vertex_groups:
    if "thumb" in vg.name or "index" in vg.name or "middle" in vg.name or "ring" in vg.name or "pinky" in vg.name:
        shells = find_connected_shells(armlo_r, vg.index)
        vcount = sum(len(s) for s in shells)
        print(f"  VG: {vg.name:20s} | Verts: {vcount:4d} | Shells: {len(shells)} | Sizes: {[len(s) for s in shells]}")
