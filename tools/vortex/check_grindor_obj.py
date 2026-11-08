import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

# Check cha_grindor_cin_rotf_01.obj
obj_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\Grindor\cha_grindor_cin_rotf_01.obj")
if obj_path.exists():
    verts = []
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    print(f"Grindor OBJ: {len(verts)} vertices")
    print(f"X (left/right?): [{min(xs):.3f}, {max(xs):.3f}] center={(min(xs)+max(xs))/2:.3f}")
    print(f"Y (up/down?):    [{min(ys):.3f}, {max(ys):.3f}] center={(min(ys)+max(ys))/2:.3f}")
    print(f"Z (front/back?): [{min(zs):.3f}, {max(zs):.3f}] center={(min(zs)+max(zs))/2:.3f}")
    
    # Find vertices with max Z vs min Z
    # Grindor cockpit / nose vs tail
    max_z_v = [v for v in verts if v[2] > max(zs) - 1.0]
    min_z_v = [v for v in verts if v[2] < min(zs) + 1.0]
    max_y_v = [v for v in verts if v[1] > max(ys) - 1.0]
    print(f"Max Z verts (sample): {max_z_v[:3]}")
    print(f"Min Z verts (sample): {min_z_v[:3]}")
    print(f"Max Y verts (sample): {max_y_v[:3]}")

