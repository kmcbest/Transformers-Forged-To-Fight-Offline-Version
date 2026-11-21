import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_main")

slot1_polys = [p for p in robot.data.polygons if p.material_index == 1]
slot0_polys = [p for p in robot.data.polygons if p.material_index == 0]

# For each poly in Slot 1, check if there is an identical or near-identical poly in Slot 0:
coincident = []
for p1 in slot1_polys:
    c1 = p1.center
    for p0 in slot0_polys:
        dist = (p0.center - c1).length
        if dist < 0.05: # within 5cm
            coincident.append((p1, p0, dist))

print(f"Coincident/near poly pairs between Slot 1 and Slot 0: {len(coincident)}")
uv_layer = robot.data.uv_layers.active.data
for p1, p0, dist in coincident[:20]:
    uv0 = [uv_layer[li].uv for li in p0.loop_indices]
    u_avg0 = sum(u[0] for u in uv0)/len(uv0)
    v_avg0 = sum(u[1] for u in uv0)/len(uv0)
    print(f"Pair: p1({p1.index}, c={p1.center}) <-> p0({p0.index}, c={p0.center}, norm={p0.normal}), dist={dist:.4f}, p0_uv=({u_avg0:.3f}, {v_avg0:.3f})")
