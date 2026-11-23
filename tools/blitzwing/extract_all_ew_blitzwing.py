import sys
import zipfile
import io
import os
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
DEST = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
DEST.mkdir(parents=True, exist_ok=True)

zips = [
    (r"o:\agent\eternal-war-blitzwing.zip", "robot"),
    (r"o:\agent\eternal-war-blitzwing-jet-mode.zip", "jet"),
    (r"o:\agent\eternal-war-blitzwing-tank-mode.zip", "tank"),
]

for zip_path, mode in zips:
    print(f"Extracting {mode} from {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if name.endswith('.zip'):
                print(f"  Unpacking nested {name}...")
                data = z.read(name)
                with zipfile.ZipFile(io.BytesIO(data)) as nz:
                    for nname in nz.namelist():
                        if not nname.endswith('/'):
                            out_p = DEST / os.path.basename(nname)
                            out_p.write_bytes(nz.read(nname))
                            print(f"    -> {out_p.name} ({out_p.stat().st_size:,} bytes)")
            elif not name.endswith('/'):
                out_p = DEST / os.path.basename(name)
                out_p.write_bytes(z.read(name))
                print(f"  -> {out_p.name} ({out_p.stat().st_size:,} bytes)")

print("\n[Done] All files in DEST:")
for p in sorted(DEST.iterdir()):
    print(f"  {p.name:32s} {p.stat().st_size:,} bytes")
