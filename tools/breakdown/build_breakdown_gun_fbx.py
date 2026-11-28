import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [Breakdown] Stage 2C Left-Hand Pistol Alignment (Breakdown_Weapon -> Sideswipe Pistol_L) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
BD_DIR = ROOT / "3rd-party-models" / "Breakdown"
FBX_SRC = BD_DIR / "source" / "source" / "Breakdown.fbx"
OUT_FBX_DIR = BD_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Breakdown"
UNITY_DIR.mkdir(parents=True, exist_ok=True)


def wrap_polygon_uvs_clean(mesh_obj):
    uvd = mesh_obj.data.uv_layers.active.data
    for p in mesh_obj.data.polygons:
        us = [uvd[li].uv.x for li in p.loop_indices]
        if min(us) >= 0.99:
            for li in p.loop_indices:
                uvd[li].uv.x -= 1.0
        for li in p.loop_indices:
            uvd[li].uv.x = min(0.9995, max(0.0005, uvd[li].uv.x))
            uvd[li].uv.y = min(0.9995, max(0.0005, uvd[li].uv.y))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    gun = bpy.data.objects.get("Breakdown_Weapon")
    assert gun, "Missing Breakdown_Weapon!"
    out_stem = "breakdown_gun_l"
    gun.name = out_stem
    gun.parent = None
    gun.matrix_world = Matrix.Identity(4)

    for o in list(bpy.data.objects):
        if o != gun:
            bpy.data.objects.remove(o, do_unlink=True)

    wrap_polygon_uvs_clean(gun)

    # Raw Breakdown_Weapon bounds (cleared transforms):
    #   X=[-0.082,+0.082], Y=[-0.989,+0.369] (muzzle at -Y!), Z=[-0.125,+0.366] (height along +Z)
    # Sideswipe Pistol_L Unity mesh bounds:
    #   X=[-2.647, +0.513] (muzzle at -X!), Y=[-0.355, +0.210], Z=[-0.291, +1.609]
    # In Blender FBX (BuildGraftedMesh with sx=1, sz=-1 -> Unity ux=-bx, uy=bz, uz=by? Actually sx=1, sz=-1 in Dragstrip gave Unity ux = -bx!):
    #   Target Blender bounds for BuildGraftedMesh(sx=1, sz=-1, zIsHeight=True):
    #   bx in [-0.513, +2.647] (muzzle +bx -> Unity -ux = -2.647!)
    #   by in [-1.609, +0.291] (gun top at -by -> Unity uz = +1.609; grip bottom at +by -> Unity uz = -0.291!)
    #   bz in [-0.355, +0.210] (side center -0.072)
    SCALE_G = 2.40
    gun.data.transform(Matrix.Scale(SCALE_G, 4))
    # RotZ(+90): -Y muzzle -> +X muzzle; +Z rail -> +Z
    gun.data.transform(Matrix.Rotation(math.radians(90.0), 4, 'Z'))
    # RotX(+90): +Z rail -> -Y Blender; thickness -> Z
    gun.data.transform(Matrix.Rotation(math.radians(90.0), 4, 'X'))
    gun.data.update()

    vs = [v.co for v in gun.data.vertices]
    dx = -0.513 - min(v.x for v in vs)
    dy = 0.291 - max(v.y for v in vs)
    cz = (min(v.z for v in vs) + max(v.z for v in vs)) / 2.0
    dz = -0.072 - cz
    gun.data.transform(Matrix.Translation(Vector((dx, dy, dz))))
    gun.data.update()

    vs2 = [v.co for v in gun.data.vertices]
    print(f"[✓] {out_stem} Blender bounds: X=[{min(v.x for v in vs2):.3f},{max(v.x for v in vs2):.3f}], Y=[{min(v.y for v in vs2):.3f},{max(v.y for v in vs2):.3f}], Z=[{min(v.z for v in vs2):.3f},{max(v.z for v in vs2):.3f}]")

    arm_data = bpy.data.armatures.new(f"{out_stem}_arm")
    arm_obj = bpy.data.objects.new(f"{out_stem}_rig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    # Sideswipe Pistol_L 1 bone: 'COG' at blender=(+0.459, -0.139, -0.072)
    b0 = arm_data.edit_bones.new("COG")
    b0.head = Vector((0.459, -0.139, -0.072))
    b0.tail = b0.head + Vector((0.0, 0.0, 0.3))
    bpy.ops.object.mode_set(mode='OBJECT')

    gun.vertex_groups.clear()
    vg = gun.vertex_groups.new(name="COG")
    vg.add(list(range(len(gun.data.vertices))), 1.0, 'REPLACE')
    mod = gun.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    gun.parent = arm_obj

    gun.data.materials.clear()
    gun.data.materials.append(bpy.data.materials.new("cha_breakdown_wpns"))

    for out_fbx in (OUT_FBX_DIR / f"{out_stem}_prepared.fbx", UNITY_DIR / f"{out_stem}_prepared.fbx"):
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        gun.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=False,
            object_types={'ARMATURE', 'MESH'},
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_anim=False,
            axis_forward='-Z',
            axis_up='Y',
        )
        print(f"[✓] Exported {out_fbx} ({out_fbx.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
