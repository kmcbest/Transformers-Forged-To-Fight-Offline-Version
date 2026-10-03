import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_vehicle.fbx")

obj = bpy.context.scene.objects.get("cha_elita_one_vehicle")
# Check front bumper vs rear exhaust in Elita vehicle
# In Elita vehicle, let's find the max Y (top) or min/max Z
zs = [v.co.z for v in obj.data.vertices]
print(f"Elita vehicle Z min={min(zs):.2f}, max={max(zs):.2f}")
# Let's inspect vertices at min Z vs max Z:
# Where are the headlights/windshield? Windshield slopes up towards the back
front_candidates = [v.co for v in obj.data.vertices if v.co.z > 3.0]
back_candidates = [v.co for v in obj.data.vertices if v.co.z < -3.0]
print(f"Verts at Z > 3.0: count={len(front_candidates)}, Y avg={sum(v.y for v in front_candidates)/len(front_candidates):.2f}")
print(f"Verts at Z < -3.0: count={len(back_candidates)}, Y avg={sum(v.y for v in back_candidates)/len(back_candidates):.2f}")
