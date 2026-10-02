import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

# Render keyframes: 0, 6, 11, 18
frames = [0, 6, 11, 18]
names = [
    "preview_elita_arcee_frame00_guard.png",
    "preview_elita_arcee_frame06_windup.png",
    "preview_elita_arcee_frame11_jab_strike.png",
    "preview_elita_arcee_frame18_recovery.png"
]

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

for f, name in zip(frames, names):
    bpy.context.scene.frame_set(f)
    out_path = OUT_DIR / name
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered frame {f} to {name}")

print("All frames rendered successfully!")
