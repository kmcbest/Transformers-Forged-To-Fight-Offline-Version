import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=r"tools/elita_one/elita_vehicle_clean.blend")

vh = bpy.data.objects.get("cha_elita_one_vehicle")
print("Vehicle materials:", [m.name for m in vh.data.materials])
print("Polys count:", len(vh.data.polygons))
for i, m in enumerate(vh.data.materials):
    polys = [p for p in vh.data.polygons if p.material_index == i]
    print(f"  Slot {i} '{m.name}': {len(polys)} polys")
