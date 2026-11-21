import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Check where Bone_L_Wing_01 and 02 are in ALL actions (idle01, transform_r, transform_v, vehicle_idle01)
for act_name in ["Bip001|idle01|Base Layer", "Bip001|transform_v|Base Layer", "Bip001|transform_r|Base Layer", "Bip001|vehicle_idle01|Base Layer"]:
    act = bpy.data.actions.get(act_name)
    if not act: continue
    arm.animation_data.action = act
    print(f"\n=== Action: {act_name} (range {act.frame_range[0]:.0f}..{act.frame_range[1]:.0f}) ===")
    for f in [int(act.frame_range[0]), int((act.frame_range[0]+act.frame_range[1])/2), int(act.frame_range[1])]:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(deps)
        vg1 = mesh.vertex_groups["Bone_L_Wing_01(mirrored)"].index
        vg2 = mesh.vertex_groups["Bone_L_Wing_02(mirrored)"].index
        pts1 = [ev.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg1 and g.weight > 0.5 for g in v.groups)]
        pts2 = [ev.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg2 and g.weight > 0.5 for g in v.groups)]
        print(f"  f={f:2d}: Wing01 X=[{min(p.x for p in pts1):.3f},{max(p.x for p in pts1):.3f}] | Wing02 X=[{min(p.x for p in pts2):.3f},{max(p.x for p in pts2):.3f}]")
