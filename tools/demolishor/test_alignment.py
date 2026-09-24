import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Ironhide
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
ironhide = bpy.context.selected_objects[0]
ironhide.name = "Ironhide_Ref"

# 2. Load Demolishor
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

# Compare bounds before rotation
def get_bounds(obj):
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return {
        "x": (min(v.x for v in verts), max(v.x for v in verts)),
        "y": (min(v.y for v in verts), max(v.y for v in verts)),
        "z": (min(v.z for v in verts), max(v.z for v in verts)),
    }

print("Ironhide Bounds:")
ib = get_bounds(ironhide)
print(f"  X: {ib['x'][0]:.2f} to {ib['x'][1]:.2f} (span: {ib['x'][1]-ib['x'][0]:.2f})")
print(f"  Y (height): {ib['y'][0]:.2f} to {ib['y'][1]:.2f} (span: {ib['y'][1]-ib['y'][0]:.2f})")
print(f"  Z: {ib['z'][0]:.2f} to {ib['z'][1]:.2f} (span: {ib['z'][1]-ib['z'][0]:.2f})")

print("\nDemolishor Raw Bounds:")
db = get_bounds(mesh)
print(f"  X: {db['x'][0]:.2f} to {db['x'][1]:.2f} (span: {db['x'][1]-db['x'][0]:.2f})")
print(f"  Y: {db['y'][0]:.2f} to {db['y'][1]:.2f} (span: {db['y'][1]-db['y'][0]:.2f})")
print(f"  Z: {db['z'][0]:.2f} to {db['z'][1]:.2f} (span: {db['z'][1]-db['z'][0]:.2f})")
