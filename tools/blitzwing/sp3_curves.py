"""
Shared math, curve evaluation, coordinate transform, and Matinee timeline utilities
for Blitzwing Triple-Changer SP3 Stage authoring (Phase 2 Blender & Phase 3 Unity).
"""

import math
from typing import Sequence, Tuple, List, Dict, Optional

# Anchoring offset to align Motormaster Actor1(f=134) onto Windblade Actor1(f=107)
# Derived from Unity batchmode sampling:
# wb_A1(107) = (-5.11, 0.27, -2.03), mm_A1(134) = (2.33, -0.50, -8.62)
# Exact XZ delta + ground Y alignment:
MM_ANCHOR_OFFSET_U = (-7.44, 0.104, 6.59)

# Timeline schedule @ 30fps (7.40s = 222 frames)
FPS = 30.0
I_END = 107        # Windblade Robot(0..35) + Jet(35..107)
II_START = 108     # Custom cubic-Hermite bridge start
II_END = 125       # Bridge end -> seamlessly hands off to Motormaster f=134
MM_START = 134     # Motormaster f=134 -> combined f=126
MM_END = 230       # Motormaster f=230 -> combined f=222
TOTAL_FRAMES = II_END + 1 + (MM_END - MM_START)  # 126 + 96 = 222 frames (7.40s)

# Sub-phase visibility / swap frames (mutually exclusive Robot _00 / Tank _01 / Jet _02)
F_ROBOT_TO_JET = 35       # f=35: _00 OFF, _02 ON
F_JET_TO_TANK = 123       # f=123: _02 OFF, _01 ON (mid-air swap right before sky apex handoff)
F_TANK_TO_ROBOT = 178     # f=178 (= mm 186): _01 OFF, _00 ON (landing hero finish)


def combined_to_mm_frame(f: int) -> float:
    return MM_START + (f - (II_END + 1))


def mm_to_combined_frame(mm_f: float) -> float:
    return (II_END + 1) + (mm_f - MM_START)


def v3(v) -> Tuple[float, float, float]:
    if isinstance(v, dict):
        return (float(v["x"]), float(v["y"]), float(v["z"]))
    return (float(v[0]), float(v[1]), float(v[2]))


def q4_xyzw(q) -> Tuple[float, float, float, float]:
    if isinstance(q, dict):
        return (float(q["x"]), float(q["y"]), float(q["z"]), float(q["w"]))
    return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(a, s: float):
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_norm(a):
    l = math.sqrt(v_dot(a, a))
    if l < 1e-8:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def q_norm(q):
    l = math.sqrt(sum(c * c for c in q))
    if l < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    return tuple(c / l for c in q)


def q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def q_conj(q):
    return (-q[0], -q[1], -q[2], q[3])


def q_rot_vec(q, v):
    qx, qy, qz, qw = q
    vx, vy, vz = v
    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)
    return (
        vx + qw * tx + (qy * tz - qz * ty),
        vy + qw * ty + (qz * tx - qx * tz),
        vz + qw * tz + (qx * ty - qy * tx),
    )


def q_slerp(q0, q1, t: float):
    t = max(0.0, min(1.0, t))
    q0 = q_norm(q0)
    q1 = q_norm(q1)
    d = sum(a * b for a, b in zip(q0, q1))
    if d < 0.0:
        q1 = tuple(-c for c in q1)
        d = -d
    if d > 0.9995:
        return q_norm(tuple(q0[i] + t * (q1[i] - q0[i]) for i in range(4)))
    theta0 = math.acos(max(-1.0, min(1.0, d)))
    sin0 = math.sin(theta0)
    theta = theta0 * t
    s0 = math.cos(theta) - d * math.sin(theta) / sin0
    s1 = math.sin(theta) / sin0
    return q_norm(tuple(s0 * q0[i] + s1 * q1[i] for i in range(4)))


def mat3_to_q_xyzw(m00, m01, m02, m10, m11, m12, m20, m21, m22):
    """Convert orthonormal 3x3 basis columns to Unity quaternion (x,y,z,w)."""
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    return q_norm((x, y, z, w))


def q_xyzw_to_mat3(q):
    x, y, z, w = q_norm(q)
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        (1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)),
        (2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)),
        (2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)),
    )


def mat3_mul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def basis_to_q_xyzw(right, up, forward):
    """Build Unity quaternion from orthonormal (Right, Up, Forward) basis columns."""
    r = v_norm(right)
    u = v_norm(up)
    f = v_norm(forward)
    # Re-orthogonalize to ensure det = +1 right=col0, up=col1, fwd=col2
    f = v_norm(f)
    u = v_norm(v_sub(u, v_scale(f, v_dot(u, f))))
    r = v_norm(r)
    r_chk = v_cross(u, f)  # wait: in left-handed Unity (+X Right, +Y Up, +Z Fwd), Up x Fwd = +X Right?
    # Check: (0,1,0) x (0,0,1) = (1*1 - 0, 0, 0) = (1,0,0)! YES! (Right-hand rule on numerical tuples gives (+1,0,0)!)
    if v_dot(r, r_chk) < 0:
        r_chk = v_scale(r_chk, -1.0)
    r = v_norm(r_chk)
    return mat3_to_q_xyzw(
        r[0], u[0], f[0],
        r[1], u[1], f[1],
        r[2], u[2], f[2],
    )


def hermite_vec3(p0, v0, p1, v1, u: float):
    """Cubic Hermite on [0,1] where v0, v1 are derivatives dp/du."""
    u = max(0.0, min(1.0, u))
    u2 = u * u
    u3 = u2 * u
    h00 = 2.0 * u3 - 3.0 * u2 + 1.0
    h10 = u3 - 2.0 * u2 + u
    h01 = -2.0 * u3 + 3.0 * u2
    h11 = u3 - u2
    return tuple(h00 * p0[i] + h10 * v0[i] + h01 * p1[i] + h11 * v1[i] for i in range(3))


def smoothstep(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def eval_unity_anim_curve(keys: List[dict], t: float) -> float:
    """Evaluate Unity AnimationCurve safely, handling infinite/step tangents."""
    if not keys:
        return 0.0
    if t <= keys[0]["t"]:
        return float(keys[0]["v"])
    if t >= keys[-1]["t"]:
        return float(keys[-1]["v"])
    for i in range(len(keys) - 1):
        k0, k1 = keys[i], keys[i + 1]
        if k0["t"] <= t <= k1["t"]:
            dt = k1["t"] - k0["t"]
            if dt <= 1e-7:
                return float(k1["v"])
            m0 = float(k0.get("out", 0.0))
            m1 = float(k1.get("in", 0.0))
            if (not math.isfinite(m0)) or (not math.isfinite(m1)) or abs(m0) > 1e10 or abs(m1) > 1e10:
                return float(k0["v"])
            u = (t - k0["t"]) / dt
            u2 = u * u
            u3 = u2 * u
            return (
                (2.0 * u3 - 3.0 * u2 + 1.0) * float(k0["v"])
                + (u3 - 2.0 * u2 + u) * dt * m0
                + (-2.0 * u3 + 3.0 * u2) * float(k1["v"])
                + (u3 - u2) * dt * m1
            )
    return float(keys[-1]["v"])


# Unity <-> Blender conversion P: u_to_b(x,y,z) = (-x, -z, y)
P_MAT = ((-1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))
P_TRANS = ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))


def u_pos_to_b(p) -> Tuple[float, float, float]:
    return (-p[0], -p[2], p[1])


def b_pos_to_u(p) -> Tuple[float, float, float]:
    return (-p[0], p[2], -p[1])


def u_quat_to_b_wxyz(q_xyzw) -> Tuple[float, float, float, float]:
    """Convert Unity quaternion (x,y,z,w) -> Blender quaternion (w,x,y,z)."""
    ru = q_xyzw_to_mat3(q_xyzw)
    rb = mat3_mul(mat3_mul(P_MAT, ru), P_TRANS)
    qx, qy, qz, qw = mat3_to_q_xyzw(
        rb[0][0], rb[0][1], rb[0][2],
        rb[1][0], rb[1][1], rb[1][2],
        rb[2][0], rb[2][1], rb[2][2],
    )
    return (qw, qx, qy, qz)


def b_quat_wxyz_to_u_xyzw(q_wxyz) -> Tuple[float, float, float, float]:
    qw, qx, qy, qz = q_wxyz
    rb = q_xyzw_to_mat3((qx, qy, qz, qw))
    ru = mat3_mul(mat3_mul(P_TRANS, rb), P_MAT)
    return mat3_to_q_xyzw(
        ru[0][0], ru[0][1], ru[0][2],
        ru[1][0], ru[1][1], ru[1][2],
        ru[2][0], ru[2][1], ru[2][2],
    )
