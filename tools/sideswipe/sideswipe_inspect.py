import sys
import os
import zipfile
import io
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

robot_zip_path = r'O:\agent\sideswipe-robot-transformers-human-alliance.zip'
car_zip_path = r'O:\agent\sideswipe-car-transformers-human-alliance.zip'

def inspect_outer_and_inner(outer_path, inner_name):
    print(f"\n=======================================================")
    print(f"Inspecting outer zip: {outer_path}")
    with zipfile.ZipFile(outer_path, 'r') as outer_z:
        for info in outer_z.infolist():
            if info.filename.startswith("textures/"):
                # Read image dimension
                img_data = outer_z.read(info.filename)
                try:
                    img = Image.open(io.BytesIO(img_data))
                    print(f"  [Texture] {info.filename}: size={info.file_size:,} bytes, dim={img.size}, mode={img.mode}")
                except Exception as e:
                    print(f"  [Texture] {info.filename}: size={info.file_size:,} bytes (Could not parse image: {e})")
            else:
                print(f"  {info.filename}: {info.file_size:,} bytes")
                
        if inner_name in outer_z.namelist():
            inner_bytes = outer_z.read(inner_name)
            print(f"\n--- Nested Zip: {inner_name} ({len(inner_bytes):,} bytes) ---")
            with zipfile.ZipFile(io.BytesIO(inner_bytes), 'r') as inner_z:
                for info in inner_z.infolist():
                    print(f"    {info.filename}: {info.file_size:,} bytes")

inspect_outer_and_inner(robot_zip_path, 'source/Sideswipe.zip')
inspect_outer_and_inner(car_zip_path, 'source/Sideswipe_Car.zip')
