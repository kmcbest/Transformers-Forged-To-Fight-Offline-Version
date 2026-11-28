import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [WildRider] Stage 2C Gun Alignment (WildRider_Gun -> Prowl Shotgun Dock) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
FBX_SRC = WR_DIR / "source" / "WildRider_pbr.fbx"
OUT_FBX_DIR = WR_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "WildRider"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    gun = bpy.data.objects.get("WildRider_Gun")
    assert gun, "Missing WildRider_Gun!"

    gun.name = "cha_wildrider_gun"
    gun.parent = None
    gun.matrix_world = Matrix.Identity(4)

    for o in list(bpy.data.objects):
        if o != gun:
            bpy.data.objects.remove(o, do_unlink=True)

    # In raw local space:
    #   X in [-0.0787, 0.0787] (thickness)
    #   Y in [-1.0468, +0.2933] (length 1.3401, muzzle at -Y = -1.0468, grip around Y in [-0.25, 0])
    #   Z in [-0.2141, +0.3792] (grip bottom at Z = -0.2141, top rail at Z = +0.3792)
    # In Prowl shotgun Unity mesh space (where cha_prowl_gs_deluxe2016_wpns_shotgun has child rot X=180 deg):
    #   Muzzle faces -Z (-3.46), Stock faces +Z (+1.05) -> length 4.51m
    #   Grip extends to +Y (+0.500), barrel centered at Y ≈ -0.92 (because parent transform rotates X 180 deg, flipping Y!)
    # Wait: in Blender FBX export with axis_forward='-Z', axis_up='Y':
    #   Blender (bx, by, bz) -> Unity (-bx, bz, -by)!! Wait: verify!
    #   In robot FBX export (axis_forward='-Z', axis_up='Y'), Blender (x, y, z) maps to Unity (-x, z, -y) ->
    #   Wait: if we want Unity mesh space (ux, uy, uz) where:
    #     Muzzle is at uz = -3.46, Stock at uz = +1.05 -> in Blender, by = -uz -> muzzle at by = +3.46? NO!
    #     Check prowl_50_bones: Unity Forward is +Z, Blender Forward is -Y, so unity_z = -blender_y!
    #     Prowl shotgun muzzle is at Unity uz = -3.46, which corresponds to Blender by = +3.46? Wait!
    #     Why is Prowl shotgun muzzle at -Z in Unity mesh space? Because its parent Transform 'gun' has rot=(0.5,-0.5,-0.5,0.5) + child rot X=180!
    #     So in Unity mesh space, muzzle MUST BE AT uz = -3.46 -> Blender by = +3.46!
    #     Let's double check StarSaber gun: StarSaber exported with axis_forward='Y', axis_up='Z' where Blender -Y became Unity -Z!
    #     Here if we export with axis_forward='Y', axis_up='Z' (exactly like build_gun_fbx.py!),
    #     Wait: in build_gun_fbx.py, Blender (bx, by, bz) exported with (axis_forward='Y', axis_up='Z'):
    #       Blender Y -> Unity Z, Blender Z -> Unity Y (wait or let's verify in Unity Gate 3 directly)!
    #     Even simpler: let's transform WildRider_Gun in Blender to match Prowl's shotgun orientation cleanly:
    #       Scale 3.30x -> length 1.34 * 3.30 = 4.42m (vs Prowl 4.51m)
    #       Rotate X by 180 deg so grip bottom (-Z) points UP (+Z in Blender) and muzzle (-Y) flips to +Y (Wait: rotating X 180 flips Y -> -Y and Z -> -Z, so muzzle moves from -Y to +Y!)
    #       Wait: in prowl_shotgun_ref.obj (Unity OBJ coords):
    #         If we import prowl_shotgun_ref.obj into Blender with Blender's default OBJ importer (forward='-Z', up='Y'),
    #         we see its EXACT Blender-imported vertices directly! Let's check against prowl_shotgun_ref.obj right inside this script!
    bpy.ops.wm.obj_import(filepath=str(WR_DIR / "prowl_shotgun_ref.obj"))
    prowl_gun = [o for o in bpy.data.objects if o != gun][0]
    p_verts = [prowl_gun.matrix_world @ v.co for v in prowl_gun.data.vertices]
    pxs = [p.x for p in p_verts]; pys = [p.y for p in p_verts]; pzs = [p.z for p in p_verts]
    print(f"[*] Prowl shotgun imported to Blender space: X=[{min(pxs):.3f},{max(pxs):.3f}], Y=[{min(pys):.3f},{max(pys):.3f}], Z=[{min(pzs):.3f},{max(pzs):.3f}]")
    bpy.data.objects.remove(prowl_gun, do_unlink=True)

    # Note: In raw WildRider_Gun, muzzle is -Y, stock is +Y, top rail is +Z, grip bottom is -Z.
    # Let's see how prowl_gun sits in Blender space after import:
    # Raw scale 3.30x:
    SCALE_GUN = 3.30
    gun.data.transform(Matrix.Scale(SCALE_GUN, 4))
    # Rotate around X by 180 deg -> top rail becomes -Z, grip bottom becomes +Z, muzzle becomes +Y (just wait: let's print pzs/pys above first, OR rotate Y=180 & Z=180!)
    # Wait: if prowl_shotgun_ref.obj in Unity has muzzle at -Z, grip at +Y:
    # Blender's OBJ importer (Unity -X -> Blender X, or standard OBJ forward=-Z, up=Y): (ux, uy, uz) -> Blender (ux, -uz, uy)!
    # So Unity muzzle (uz = -3.46) becomes Blender Y = +3.46! Unity grip (uy = +0.50) becomes Blender Z = +0.50!
    # Therefore rotating WildRider_Gun around X by 180 deg maps:
    #   muzzle (-Y) -> +Y!
    #   grip (-Z) -> +Z!
    #   top rail (+Z) -> -Z!
    # Let's check exact bounds after RotX(180) and align center to Prowl shotgun's barrel/grip!
    gun.data.transform(Matrix.Rotation(math.radians(180.0), 4, 'X'))
    gun.data.update()

    vs = [v.co for v in gun.data.vertices]
    # Center gun receiver/grip onto Prowl's barrel center (Y ≈ +0.9, Z ≈ -0.92 in Blender -> wait check max(pzs)=+0.50, barrel at Z=-0.92)
    # Grip tip on WildRider_Gun after RotX(180) is max(Z)! Match max(Z) to +0.500 (or grip centroid to Y=0.0, Z=+0.05)
    g_zs = [v.z for v in vs]; g_ys = [v.y for v in vs]
    print(f"[*] After RotX(180) & scale {SCALE_GUN}x: Y=[{min(g_ys):.3f},{max(g_ys):.3f}], Z=[{min(g_zs):.3f},{max(g_zs):.3f}]")
    # Shift so top/grip max_z aligns to +0.500 and Y aligns muzzle to +3.460!
    dy = 3.460 - max(g_ys)
    dz = 0.500 - max(g_zs)
    gun.data.transform(Matrix.Translation(Vector((0.0, dy, dz))))
    gun.data.update()

    vs2 = [v.co for v in gun.data.vertices]
    print(f"[✓] Final WildRider_Gun bounds: X=[{min(v.x for v in vs2):.3f},{max(v.x for v in vs2):.3f}], Y=[{min(v.y for v in vs2):.3f},{max(v.y for v in vs2):.3f}], Z=[{min(v.z for v in vs2):.3f},{max(v.z for v in vs2):.3f}]")

    # Add 1-bone Armature
    arm_data = bpy.data.armatures.new("GunArmature")
    arm_obj = bpy.data.objects.new("cha_wildrider_gun_rig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    b = arm_data.edit_bones.new("COG")
    b.head = Vector((0, 0, 0)); b.tail = Vector((0, 0, 1))
    bpy.ops.object.mode_set(mode='OBJECT')

    gun.vertex_groups.clear()
    vg = gun.vertex_groups.new(name="COG")
    vg.add(list(range(len(gun.data.vertices))), 1.0, 'REPLACE')
    mod = gun.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    gun.parent = arm_obj

    gun.data.materials.clear()
    mat = bpy.data.materials.new("cha_wildrider_main")
    gun.data.materials.append(mat)

    for out_fbx in (OUT_FBX_DIR / "wildrider_gun_prepared.fbx", UNITY_DIR / "wildrider_gun_prepared.fbx"):
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
