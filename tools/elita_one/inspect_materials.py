import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

print("Objects in blend:")
for o in bpy.data.objects:
    print(f" - {o.name} (type: {o.type})")
    if o.type == 'MESH':
        print(f"   Materials ({len(o.material_slots)}):")
        for idx, slot in enumerate(o.material_slots):
            mat_name = slot.material.name if slot.material else "None"
            count = sum(1 for p in o.data.polygons if p.material_index == idx)
            print(f"     Slot {idx}: {mat_name} (polys: {count})")
