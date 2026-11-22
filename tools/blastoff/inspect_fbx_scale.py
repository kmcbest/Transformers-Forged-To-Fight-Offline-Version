import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

def inspect_fbx(path):
    print("=== Inspecting", path, "===")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    for obj in bpy.data.objects:
        print(f"Object: {obj.name}, type: {obj.type}, scale: {obj.scale}, loc: {obj.location}")
        if obj.type == 'MESH':
            m = obj
            vs = [v.co for v in m.data.vertices]
            min_x = min(v.x for v in vs); max_x = max(v.x for v in vs)
            min_y = min(v.y for v in vs); max_y = max(v.y for v in vs)
            min_z = min(v.z for v in vs); max_z = max(v.z for v in vs)
            print(f"  Mesh vertices: count={len(vs)}")
            print(f"  Local X: [{min_x:.4f}, {max_x:.4f}]")
            print(f"  Local Y: [{min_y:.4f}, {max_y:.4f}]")
            print(f"  Local Z: [{min_z:.4f}, {max_z:.4f}]")
            wvs = [obj.matrix_world @ v.co for v in m.data.vertices]
            print(f"  World Z: [{min(v.z for v in wvs):.4f}, {max(v.z for v in wvs):.4f}]")

inspect_fbx(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\BlastOff\blastoff_robot_prepared.fbx")
inspect_fbx(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\BlastOff\blastoff_vh_prepared.fbx")
