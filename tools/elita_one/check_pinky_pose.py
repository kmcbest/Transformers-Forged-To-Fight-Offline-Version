import json
import bpy
import mathutils
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

arcee_arm = bpy.data.objects.get("Arcee_Armature")
elita_arm = bpy.data.objects.get("Elita_One_Armature")

for arm_name, arm in [("Arcee", arcee_arm), ("Elita", elita_arm)]:
    pb = arm.pose.bones.get("LeftHandPinky2")
    eb = arm.data.bones.get("LeftHandPinky2")
    print(f"\n{arm_name} LeftHandPinky2:")
    print(f"  Edit bone head: {eb.head_local}")
    print(f"  Pose bone rot quat: {pb.rotation_quaternion}")
    print(f"  Pose bone matrix in arm space:\n{pb.matrix}")

# Now check Arcee's actual vertices weighted to LeftHandPinky2 in Frame 0
arcee_mesh = bpy.data.objects.get("Arcee_Mesh")
depsgraph = bpy.context.evaluated_depsgraph_get()
arc_eval = arcee_mesh.evaluated_get(depsgraph)
m_eval = arc_eval.to_mesh()

vg_p2 = arcee_mesh.vertex_groups.get("LeftHandPinky2")
if vg_p2:
    p2_verts = [i for i, v in enumerate(arcee_mesh.data.vertices) if any(g.group == vg_p2.index and g.weight > 0.5 for g in v.groups)]
    print(f"\nArcee has {len(p2_verts)} verts weighted to LeftHandPinky2.")
    for vi in p2_verts[:5]:
        rest_co = arcee_mesh.data.vertices[vi].co
        eval_co = m_eval.vertices[vi].co
        print(f"  Arcee Vert {vi}: Rest={rest_co} -> Eval={eval_co} (dist={(eval_co - rest_co).length:.3f}m)")

arc_eval.to_mesh_clear()
