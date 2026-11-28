import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy, math
from mathutils import Vector, Matrix
from pathlib import Path

print("=== [DragStrip] Stage 2C Dual Blaster Alignment (Dragstrip_Weapon_01_R & 02_L -> Mirage Blasters) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DS_DIR = ROOT / "3rd-party-models" / "DragStrip"
FBX_SRC = DS_DIR / "source" / "source" / "Dragstrip.fbx"
OUT_FBX_DIR = DS_DIR / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "DragStrip"
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


def build_single_blaster(src_name: str, is_left: bool, out_stem: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    gun = bpy.data.objects.get(src_name)
    assert gun, f"Missing {src_name}!"
    gun.name = out_stem
    gun.parent = None
    gun.matrix_world = Matrix.Identity(4)

    for o in list(bpy.data.objects):
        if o != gun:
            bpy.data.objects.remove(o, do_unlink=True)

    wrap_polygon_uvs_clean(gun)

    # Raw Dragstrip_Weapon bounds: X=[-0.063,0.063], Y=[-1.218,+0.079] (muzzle at -Y!), Z=[-0.099,+0.395] (top rail +Z, grip -Z)
    # Target Mirage blaster (Unity OBJ): X=[-0.489, +3.878] (muzzle +X!), Y=[0,+0.494] (right) or [-0.494,0] (left), Z=[-0.10,+1.41] (in Blender: Y=[-1.41,+0.10], Z=[-0.005,+0.494] right / [-0.494,+0.005] left)!
    #Wait: check Blender OBJ import vs Unity mesh coords directly!
    # Earlier extract_mirage_truth printed Mirage blaster Unity mesh coords:
    #   right: X=[-0.489, 3.878], Y=[-0.005, 0.494], Z=[-0.102, 1.407]
    #   left : X=[-0.489, 3.878], Y=[-0.494, 0.005], Z=[-0.102, 1.407]
    # Note: in Dragstrip_Weapon, length along Y is 1.296m. Scale 3.20x -> 4.148m (vs Mirage 4.367m).
    # Rotate around Z by +90 deg maps raw (-Y muzzle -> +X muzzle!), (raw +X -> +Y), (raw +Z top -> +Z top)!
    # Check Unity conversion: Blender (bx, by, bz) -> BuildGraftedMesh -> Unity (ux, uy, uz):
    #   We'll export with 2 bones ['COG', 'FX'] and verify exact Unity bounds in Gate 3 vs Mirage blaster_right/left!
    SCALE_G = 3.20
    gun.data.transform(Matrix.Scale(SCALE_G, 4))
    # Rotate +90 around Z: (-Y) -> (+X muzzle!), +Z stays +Z (top of gun up!)
    gun.data.transform(Matrix.Rotation(math.radians(90.0), 4, 'Z'))
    gun.data.update()

    vs = [v.co for v in gun.data.vertices]
    # Align rear butt (min_x) to -0.45m (matching Mirage -0.489), center grip Y to +0.24 (right) or -0.24 (left) in Unity Y (Blender Z!),
    # Wait: in Blender Z-up -> Unity Y-up (`uy = bz`), so side offset Y_mirage=[0, 0.494] / [-0.494, 0] is Blender Z!
    # Wait no: Mirage blaster_right has Y=[-0.005, +0.494] (0.50m height? Or thickness?!), Z=[-0.102, +1.407] (1.51m)!
    # Check: 1.51m is the TOP-TO-BOTTOM HEIGHT (grip+scope = 1.58m = 0.494 * 3.20!! Look: raw Dragstrip Z size = 0.395 - (-0.099) = 0.494! * 3.20 = 1.581m! And raw X size = 0.126 * 3.20 = 0.404m vs Mirage 0.50m!!).
    # SO ON MIRAGE BLASTERS:
    #   Unity X = Barrel length (+3.88 muzzle, -0.49 rear)!
    #   Unity Y = Side thickness ([0, +0.49] right, [-0.49, 0] left)!
    #   Unity Z = Top/Bottom height ([-0.10, +1.41]) -> Wait is +Z up or -Z up in Hand space?! We check RightHand axis: in Blender OBJ import, Unity Y -> Blender Z, Unity Z -> Blender -Y (`Y=[-1.407, +0.102]`)!
    # Let's match Blender OBJ coords of Mirage blaster EXACTLY:
    #   Blender X = [-0.489, +3.878] (muzzle at +X!)
    #   Blender Y = [-1.407, +0.102] (so gun top/bottom height must lie along Blender Y, NOT Z!)
    #   Blender Z = [-0.005, +0.494] (right) or [-0.494, +0.005] (left)!
    # Rotate gun +90 deg around X so raw +Z (top/grip height) maps to Blender -Y ([-1.4, +0.1]) and raw -Y (width) maps to Z!
    #Wait: first undo Z+90? Even simpler: combine cleanly from raw!
    # Reset? No, right now after Z(+90): muzzle=+X, height=+Z, thickness=Y. Rotating +90 around X maps (X, Y, Z) -> (X, -Z, Y):
    #   Muzzle (+X) stays +X!
    #   Height (+Z = [-0.32, +1.26]) -> Blender Y = [-1.26, +0.32]! (Matches Mirage Blender Y=[-1.41, +0.10]!!)
    #   Thickness (Y = [-0.20, +0.20]) -> Blender Z = [-0.20, +0.20]!
    gun.data.transform(Matrix.Rotation(math.radians(90.0), 4, 'X'))
    gun.data.update()

    vs2 = [v.co for v in gun.data.vertices]
    dx = -0.489 - min(v.x for v in vs2)
    dy = 0.102 - max(v.y for v in vs2)
    target_cz = -0.245 if is_left else 0.245
    cz = (min(v.z for v in vs2) + max(v.z for v in vs2)) / 2.0
    dz = target_cz - cz
    gun.data.transform(Matrix.Translation(Vector((dx, dy, dz))))
    gun.data.update()

    vs3 = [v.co for v in gun.data.vertices]
    print(f"[✓] {out_stem} aligned Blender bounds: X=[{min(v.x for v in vs3):.3f},{max(v.x for v in vs3):.3f}], Y=[{min(v.y for v in vs3):.3f},{max(v.y for v in vs3):.3f}], Z=[{min(v.z for v in vs3):.3f},{max(v.z for v in vs3):.3f}]")

    arm_data = bpy.data.armatures.new(f"{out_stem}_arm")
    arm_obj = bpy.data.objects.new(f"{out_stem}_rig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    b0 = arm_data.edit_bones.new("COG")
    b0.head = Vector((0, 0, 0)); b0.tail = Vector((0, 0, 0.5))
    b1 = arm_data.edit_bones.new("FX")
    b1.head = Vector((3.8, -0.7, target_cz)); b1.tail = b1.head + Vector((0.3, 0, 0))
    b1.parent = b0
    bpy.ops.object.mode_set(mode='OBJECT')

    gun.vertex_groups.clear()
    vg = gun.vertex_groups.new(name="COG")
    vg.add(list(range(len(gun.data.vertices))), 1.0, 'REPLACE')
    gun.vertex_groups.new(name="FX")
    mod = gun.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    gun.parent = arm_obj

    gun.data.materials.clear()
    gun.data.materials.append(bpy.data.materials.new("cha_dragstrip_wpns"))

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


def main():
    build_single_blaster("Dragstrip_Weapon_01_R", is_left=False, out_stem="dragstrip_gun_r")
    build_single_blaster("Dragstrip_Weapon_02_L", is_left=True, out_stem="dragstrip_gun_l")


if __name__ == "__main__":
    main()
