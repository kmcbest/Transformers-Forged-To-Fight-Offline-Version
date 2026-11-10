import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=str(obj_path))

m = bpy.data.objects['strongarm_vehicle']

# In strongarm_vehicle, let's see which Z has the highest vertices or windshield
# Usually windshield slopes up towards the back or front
# Let's check vertices with highest Y (roof/sirens)
high_y_verts = [v for v in m.data.vertices if v.co.y > 2.3]
z_of_high = [v.co.z for v in high_y_verts]
print(f"Roof / Siren Z range: min={min(z_of_high):.3f}, max={max(z_of_high):.3f}, avg={sum(z_of_high)/len(z_of_high):.3f}")

# Check lowest Y near front vs rear (wheels)
low_y_verts = [v for v in m.data.vertices if v.co.y < 0.2]
z_of_low = [v.co.z for v in low_y_verts]
print(f"Ground / Wheels Z range: min={min(z_of_low):.3f}, max={max(z_of_low):.3f}")
