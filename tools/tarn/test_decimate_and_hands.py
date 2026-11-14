import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import bmesh
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

# Test decimating Cube.049 and Cylinder.045 after applying Mirror
for nm in ["Cube.049", "Cylinder.045", "Plane.004", "Sphere.001", "Plane.050", "Cylinder.001"]:
    o = bpy.data.objects[nm]
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        if m.type == 'MIRROR':
            bpy.ops.object.modifier_apply(modifier=m.name)
    tris0 = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
    
    # Try dissolve_degenerate / remove_doubles then decimate
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.005)
    bpy.ops.object.mode_set(mode='OBJECT')
    tris_w = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
    
    mod = o.modifiers.new("Dec", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = 500.0 / max(tris_w, 1)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    tris1 = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
    print(f"  {nm:14s}: init_tris={tris0:6d} -> weld={tris_w:6d} -> collapse(target=500)={tris1:6d}, verts={len(o.data.vertices):6d}")
    
    if tris1 > 2000:
        # Try PLANAR decimate
        mp = o.modifiers.new("Planar", 'DECIMATE')
        mp.decimate_type = 'DISSOLVE'
        mp.angle_limit = 0.25 # ~14 deg
        bpy.ops.object.modifier_apply(modifier=mp.name)
        tris2 = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
        print(f"     after PLANAR(14deg): tris={tris2:6d}, verts={len(o.data.vertices):6d}")
        if tris2 > 2000:
            # Try Voxel Remesh preserving bounds (for solid greeble Cube.049/Cyl.045)
            o.modifiers.clear()
            dim = max(o.dimensions.x, o.dimensions.y, o.dimensions.z)
            # Note object scale might be non-1, apply scale first
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            dim = max(o.dimensions.x, o.dimensions.y, o.dimensions.z)
            mr = o.modifiers.new("Remesh", 'REMESH')
            mr.mode = 'VOXEL'
            mr.voxel_size = max(dim / 24.0, 0.05)
            bpy.ops.object.modifier_apply(modifier=mr.name)
            tris3 = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
            print(f"     after VOXEL(dim/24): tris={tris3:6d}, verts={len(o.data.vertices):6d}")
