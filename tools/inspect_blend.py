import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")

print("=== Objects in demolishor_phase2_inspect.blend ===")
for obj in bpy.data.objects:
    print(f"- {obj.name} (type: {obj.type})")
    if obj.type == 'ARMATURE':
        print(f"  Armature bones count: {len(obj.data.bones)}")
        if obj.animation_data and obj.animation_data.action:
            print(f"  Current Action: {obj.animation_data.action.name}")
            print(f"  Frame range: {obj.animation_data.action.frame_range}")

print("\n=== Actions in blend ===")
for act in bpy.data.actions:
    print(f"- {act.name} (frames: {act.frame_range})")
