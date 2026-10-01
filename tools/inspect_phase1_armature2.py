import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

for obj in bpy.data.objects:
    print(f"- {obj.name} (type: {obj.type})")
    if obj.type == 'ARMATURE':
        print(f"  Armature bones count: {len(obj.data.bones)}")
        for bname in ["Hips", "LeftArm", "LeftForeArm", "RightArm", "RightForeArm", "Head"]:
            b = obj.data.bones.get(bname)
            if b:
                print(f"    Bone {bname}: head={b.head_local}, tail={b.tail_local}")
                print(f"      matrix_local:\n{b.matrix_local}")
