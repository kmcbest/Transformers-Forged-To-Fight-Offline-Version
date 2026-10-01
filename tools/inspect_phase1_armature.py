import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

print("=== Objects in demolishor_phase1.blend ===")
for obj in bpy.data.objects:
    print(f"- {obj.name} (type: {obj.type}, rot: {obj.rotation_euler})")
    if obj.type == 'ARMATURE':
        print(f"  Armature bones count: {len(obj.data.bones)}")
        # Check bone orientations
        for bname in ["Hips", "LeftArm", "LeftForeArm", "RightArm", "RightForeArm", "Head"]:
            b = obj.data.bones.get(bname)
            if b:
                print(f"    Bone {bname}: head={b.head}, tail={b.tail}, roll={b.roll}")
