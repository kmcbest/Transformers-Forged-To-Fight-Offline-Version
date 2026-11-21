import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def parse_obj_bounds(path):
    xs, ys, zs = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                xs.append(float(parts[1]))
                ys.append(float(parts[2]))
                zs.append(float(parts[3]))
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

p_rob = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_00_robot.obj"
p_car = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_01_car.obj"

xb, yb, zb = parse_obj_bounds(p_rob)
print(f"Barricade Robot OBJ Bounds:")
print(f"  X: [{xb[0]:.3f}, {xb[1]:.3f}] (width={xb[1]-xb[0]:.3f})")
print(f"  Y: [{yb[0]:.3f}, {yb[1]:.3f}] (height={yb[1]-yb[0]:.3f})")
print(f"  Z: [{zb[0]:.3f}, {zb[1]:.3f}] (depth={zb[1]-zb[0]:.3f})")

xb, yb, zb = parse_obj_bounds(p_car)
print(f"\nBarricade Car OBJ Bounds:")
print(f"  X: [{xb[0]:.3f}, {xb[1]:.3f}] (width={xb[1]-xb[0]:.3f})")
print(f"  Y: [{yb[0]:.3f}, {yb[1]:.3f}] (height={yb[1]-yb[0]:.3f})")
print(f"  Z: [{zb[0]:.3f}, {zb[1]:.3f}] (depth={zb[1]-zb[0]:.3f})")
