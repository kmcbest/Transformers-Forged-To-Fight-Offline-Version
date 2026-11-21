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
act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")

print(f"Action: {act.name}, frame_range: {act.frame_range}")

# Print all fcurves in vehicle_idle01
bones_in_act = set()
for fc in act.fcurves:
    if 'pose.bones["' in fc.data_path:
        bname = fc.data_path.split('pose.bones["')[1].split('"]')[0]
        prop = fc.data_path.split('"].')[1]
        bones_in_act.add((bname, prop))

print("\n=== Animated bones & properties in vehicle_idle01 ===")
for bname, prop in sorted(bones_in_act):
    if any(k in bname.lower() for k in ["wing", "bird", "beak", "back", "spine", "pelvis", "head", "clav", "arm", "thigh", "calf", "foot"]):
        # check min/max values across frames
        fcs = [fc for fc in act.fcurves if fc.data_path == f'pose.bones["{bname}"].{prop}']
        vals_f1 = [round(fc.evaluate(1), 4) for fc in fcs]
        vals_f15 = [round(fc.evaluate(15), 4) for fc in fcs]
        vals_f30 = [round(fc.evaluate(30), 4) for fc in fcs]
        print(f"  {bname:26s} .{prop:20s}: f1={vals_f1} | f15={vals_f15} | f30={vals_f30}")
