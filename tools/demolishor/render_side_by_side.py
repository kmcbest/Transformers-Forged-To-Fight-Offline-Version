import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_ironhide_side_by_side.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Adjust camera if needed to ensure both bots fit nicely in frame
cam = bpy.data.objects.get("SideBySideCam")
if cam:
    cam.location = (0.0, 22.0, 5.5)
    cam.data.lens = 35 # slightly wider focal length for full body view

# Frame 2: Combat Idle
bpy.context.scene.frame_current = 2
out_f2 = ROOT / "tools" / "demolishor" / "preview_brawler_idle_guard.png"
bpy.context.scene.render.filepath = str(out_f2)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Frame 2 to: {out_f2.name}")

# Frame 14: Punch 1 (Left Jab)
bpy.context.scene.frame_current = 14
out_f14 = ROOT / "tools" / "demolishor" / "preview_brawler_punch1_jab.png"
bpy.context.scene.render.filepath = str(out_f14)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Frame 14 to: {out_f14.name}")

# Frame 34: Punch 2 (Right Straight Punch)
bpy.context.scene.frame_current = 34
out_f34 = ROOT / "tools" / "demolishor" / "preview_brawler_punch2_cross.png"
bpy.context.scene.render.filepath = str(out_f34)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Frame 34 to: {out_f34.name}")
