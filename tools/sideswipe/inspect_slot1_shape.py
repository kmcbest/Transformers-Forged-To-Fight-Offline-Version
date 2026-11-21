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
left_slot1 = [p for p in slot1_polys if p.center.x < 0]
right_slot1 = [p for p in slot1_polys if p.center.x > 0]

print(f"Left Slot 1: {len(left_slot1)} polys, Right Slot 1: {len(right_slot1)} polys")
for pi, p in enumerate(left_slot1):
    c = p.center
    n = p.normal
    print(f"  Left S1 poly {pi} (orig idx {p.index}): center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({n.x:.3f}, {n.y:.3f}, {n.z:.3f})")
