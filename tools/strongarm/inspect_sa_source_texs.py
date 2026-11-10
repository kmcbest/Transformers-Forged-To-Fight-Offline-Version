import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")
tex_dir = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\textures")
vh_tex_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.png")
vh_obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

# Check RGB ranges and save UV grid / color inspection overlays for robot parts + vehicle
for name in ["face_maskOn_MD", "chest_MD", "leg_MD", "hand_MD", "body_MD", "head_MD", "doorWing_MD", "blaster_MD"]:
    p = tex_dir / f"{name}.png"
    if p.exists():
        im = Image.open(p).convert("RGB")
        arr = np.array(im)
        # Cyan test (eyes/glow trim) vs general blue armor
        r, g, b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
        # Pure bright cyan: high G & high B, low R
        pure_cyan = (g > 170) & (b > 170) & (r < 90)
        print(f"{name:15s} size={im.size}: pure_cyan pct={pure_cyan.mean()*100:.2f}%, R_mean={r.mean():.1f}, G_mean={g.mean():.1f}, B_mean={b.mean():.1f}")

# Check vehicle texture & obj material groups!
vh_im = Image.open(vh_tex_path).convert("RGB")
print(f"\nVehicle tex size: {vh_im.size}")

# Parse UVs per group/material in strongarm_vehicle.obj
vt = []
groups = {}
cur_grp = "default"
for line in vh_obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("g ") or line.startswith("usemtl "):
        cur_grp = line.strip()
        groups.setdefault(cur_grp, [])
    elif line.startswith("vt "):
        parts = line.split()
        vt.append((float(parts[1]), float(parts[2])))
    elif line.startswith("f "):
        for tok in line.split()[1:]:
            segs = tok.split("/")
            if len(segs) >= 2 and segs[1]:
                groups.setdefault(cur_grp, []).append(int(segs[1]) - 1)

print("Vehicle OBJ groups & UV bboxes:")
for gname, idxs in groups.items():
    if idxs:
        us = [vt[i][0] for i in idxs if 0 <= i < len(vt)]
        vs = [vt[i][1] for i in idxs if 0 <= i < len(vt)]
        if us:
            print(f"  {gname}: count={len(us)}, u=[{min(us):.3f}, {max(us):.3f}], v=[{min(vs):.3f}, {max(vs):.3f}]")

# Save labeled grid of strongarm_vehicle.png (512x512 upscaled with 0.1 grid) to inspect where siren/headlights/windshield/tires are
grid_im = vh_im.resize((1024, 1024), Image.Resampling.NEAREST)
draw = ImageDraw.Draw(grid_im)
for i in range(1, 10):
    px = int(i * 0.1 * 1024)
    draw.line([(px, 0), (px, 1024)], fill=(255, 255, 0), width=1)
    draw.line([(0, px), (1024, px)], fill=(255, 255, 0), width=1)
grid_im.save(SCRATCH / "vh_uv_grid.png")

# Save face_maskOn_MD + body/chest/leg/doorWing with 0.1 grid for exact glowing pixel inspection
sheet = Image.new("RGB", (2048, 1024), (30, 30, 30))
for idx, name in enumerate(["face_maskOn_MD", "chest_MD", "leg_MD", "hand_MD", "body_MD", "head_MD", "doorWing_MD", "blaster_MD"]):
    p = tex_dir / f"{name}.png"
    if p.exists():
        sub = Image.open(p).convert("RGB").resize((512, 512), Image.Resampling.NEAREST)
        x = (idx % 4) * 512
        y = (idx // 4) * 512
        sheet.paste(sub, (x, y))
        d = ImageDraw.Draw(sheet)
        d.text((x + 8, y + 8), name, fill=(255, 255, 0))
sheet.save(SCRATCH / "robot_slots_sheet.png")
print(f"Saved inspection sheets to {SCRATCH}")
