import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROBOT_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend"
bpy.ops.wm.open_mainfile(filepath=ROBOT_BLEND)

# Find meshes and materials
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"Mesh: {obj.name}")
        for slot in obj.material_slots:
            mat = slot.material
            if mat:
                # count polygons for this material
                count = sum(1 for p in obj.data.polygons if p.material_index == obj.data.materials.find(mat.name))
                print(f"  Material: {mat.name} ({count} polys)")

# Check if there are rotor bones in Vortex_ARM
arm = bpy.data.objects.get("Vortex_ARM")
if arm:
    rotor_bones = [b.name for b in arm.data.bones if "rotor" in b.name.lower() or "blade" in b.name.lower() or "prop" in b.name.lower()]
    print(f"\nRotor/Blade bones in Vortex_ARM ({len(rotor_bones)}): {rotor_bones}")

VH_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend"
bpy.ops.wm.open_mainfile(filepath=VH_BLEND)
vh_arm = bpy.data.objects.get("Vortex_VH_ARM")
if vh_arm:
    vh_rotor_bones = [b.name for b in vh_arm.data.bones if "rotor" in b.name.lower() or "blade" in b.name.lower() or "prop" in b.name.lower()]
    print(f"\nRotor/Blade bones in Vortex_VH_ARM ({len(vh_rotor_bones)}): {vh_rotor_bones}")
