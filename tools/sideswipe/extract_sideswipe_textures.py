import sys
import os
import zipfile
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scratch_dir = r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\scratch"
tex_dir = os.path.join(scratch_dir, "textures")
os.makedirs(tex_dir, exist_ok=True)

robot_zip_path = r'O:\agent\sideswipe-robot-transformers-human-alliance.zip'
car_zip_path = r'O:\agent\sideswipe-car-transformers-human-alliance.zip'

with zipfile.ZipFile(robot_zip_path, 'r') as z:
    for name in z.namelist():
        if name.startswith("textures/"):
            data = z.read(name)
            out_path = os.path.join(tex_dir, os.path.basename(name))
            with open(out_path, 'wb') as f:
                f.write(data)
            print(f"Extracted robot tex: {out_path} ({len(data):,} bytes)")

with zipfile.ZipFile(car_zip_path, 'r') as z:
    for name in z.namelist():
        if name.startswith("textures/"):
            data = z.read(name)
            out_path = os.path.join(tex_dir, os.path.basename(name))
            with open(out_path, 'wb') as f:
                f.write(data)
            print(f"Extracted car tex: {out_path} ({len(data):,} bytes)")
