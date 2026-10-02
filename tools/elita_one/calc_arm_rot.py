import mathutils
import math

# Direction in rest mesh
v_cur = mathutils.Vector((-0.5125, -0.3888, -0.7656)).normalized()
v_target = mathutils.Vector((0.0, 0.0, -1.0))

# Rotation quaternion from v_cur to v_target
q = v_cur.rotation_difference(v_target)
print("Rotation quaternion to hang straight down:", q)
print("Euler angles (degrees):", [math.degrees(a) for a in q.to_euler()])
