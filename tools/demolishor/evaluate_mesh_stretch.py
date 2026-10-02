import bpy
import bmesh
import numpy as np
from pathlib import Path

BLEND_FILE = r"tools\demolishor\demolishor_ironhide_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
demo_arm = bpy.data.objects.get("Demolishor_Armature")

# Measure rest edge lengths
bm = bmesh.new()
bm.from_mesh(demo_mesh.data)
rest_lengths = [e.calc_length() for e in bm.edges]
bm.free()

print(f"Total edges: {len(rest_lengths)}")

# Check in pose: evaluate mesh under armature
depsgraph = bpy.context.evaluated_depsgraph_get()

def check_pose_stretch(label):
    eval_mesh_obj = demo_mesh.evaluated_get(depsgraph)
    eval_mesh = eval_mesh_obj.to_mesh()
    
    bm_eval = bmesh.new()
    bm_eval.from_mesh(eval_mesh)
    
    ratios = []
    stretched_edges = []
    for i, e in enumerate(bm_eval.edges):
        l_eval = e.calc_length()
        l_rest = rest_lengths[i]
        if l_rest > 0.001:
            ratio = l_eval / l_rest
            ratios.append(ratio)
            if ratio > 2.0 or (l_eval - l_rest) > 0.5: # 50cm expansion is a spike!
                stretched_edges.append((i, l_rest, l_eval, ratio, e.verts[0].co, e.verts[1].co))
                
    bm_eval.free()
    eval_mesh_obj.to_mesh_clear()
    
    max_ratio = max(ratios) if ratios else 1.0
    print(f"\n--- Evaluation in {label} ---")
    print(f"  Max edge stretch ratio: {max_ratio:.2f}x")
    print(f"  Abnormally stretched edges (spikes > 50cm or >2x): {len(stretched_edges)}")
    if stretched_edges:
        print("  Top stretched edges:")
        for idx, l0, l1, r, c1, c2 in sorted(stretched_edges, key=lambda x: x[3], reverse=True)[:5]:
            print(f"    Edge {idx}: rest={l0:.3f}m -> posed={l1:.3f}m ({r:.1f}x) from {c1} to {c2}")
    else:
        print("  [✓] ZERO SPIKES DETECTED! All mechanical parts are rigid.")
    return len(stretched_edges) == 0

# Check in Rest Pose
check_pose_stretch("Rest Pose")

# Check under Punch Pose if action exists
if demo_arm.animation_data and demo_arm.animation_data.action:
    for frame in (8, 14, 22, 34):
        bpy.context.scene.frame_set(frame)
        depsgraph.update()
        check_pose_stretch(f"Frame {frame}")
