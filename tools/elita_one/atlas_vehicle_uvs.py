import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_OUT = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "elita_one_vehicle.fbx"

print("\n=== Atlasing Mesh UVs in Blender ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "tools" / "elita_one" / "elita_vehicle_clean.blend"))

vh = bpy.data.objects.get("cha_elita_one_vehicle")
mesh = vh.data

# Access UV loop data
uv_layer = mesh.uv_layers.active
if not uv_layer:
    raise RuntimeError("No active UV layer found!")

# For each polygon, pack UV horizontally [Left = VH00 | Right = VH01]
# so Kabam's Vehicle Material (tform_misc_A/NM scale=(1, 0.5) offset=(0, 0.5),
# main_tform_misc_RAOE scale=(0.5, 0.5) offset=(0.5, 0)) samples both sheets 1:1
# without colliding with Robot Submesh[1] (T_CH11_01) in the bottom half of tform_misc!
for poly in mesh.polygons:
    slot = poly.material_index
    for loop_idx in poly.loop_indices:
        u, v = uv_layer.data[loop_idx].uv
        if slot == 0:
            # VH00: Left half, U' in [0.0, 0.5], V' in [0.0, 1.0]
            new_u = u * 0.5
            new_v = v
        elif slot == 1:
            # VH01: Right half, U' in [0.5, 1.0], V' in [0.0, 1.0]
            new_u = u * 0.5 + 0.5
            new_v = v
        else:
            # Glass / Cockpit: Uniform sleek dark charcoal patch in VH01 top-left
            new_u = 0.5732
            new_v = 0.9219
        uv_layer.data[loop_idx].uv = (new_u, new_v)

print(f"[✓] Transformed UVs for {len(mesh.polygons)} polygons to match atlas layout!")
mesh.update()

print("\n=== Exporting Atlased Vehicle FBX ===")
bpy.ops.object.select_all(action='DESELECT')
vh.select_set(True)
bpy.context.view_layer.objects.active = vh

FBX_OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(FBX_OUT),
    use_selection=True,
    axis_forward='-Z',
    axis_up='Y',
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True
)
print(f"[✓] Exported atlased vehicle FBX to: {FBX_OUT}")
