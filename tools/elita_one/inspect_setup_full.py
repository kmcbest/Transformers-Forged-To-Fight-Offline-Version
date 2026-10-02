import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

for o in bpy.data.objects:
    print(f"Object: {o.name} (type: {o.type})")
    print(f"  loc: {o.location}, rot: {o.rotation_euler}, scale: {o.scale}")
    if o.parent:
        print(f"  parent: {o.parent.name}")
    if o.type == 'MESH':
        print(f"  modifiers: {[m.type for m in o.modifiers]}")
        print(f"  materials: {[s.material.name for s in o.material_slots if s.material]}")
