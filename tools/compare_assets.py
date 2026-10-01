import os
import hashlib

def file_hash(path):
    h = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

repo_a = r"e:\Agent\TFTF-blender"
repo_b = r"e:\Agent\TFTF"

# Compare key directories: assets_redeco, assets_netflix, gamedata
dirs_to_check = ["assets_redeco", "assets_netflix"]

print("=== Comparing asset directories ===")
for d in dirs_to_check:
    da = os.path.join(repo_a, d)
    db = os.path.join(repo_b, d)
    files_a = set(os.listdir(da)) if os.path.exists(da) else set()
    files_b = set(os.listdir(db)) if os.path.exists(db) else set()
    
    only_a = files_a - files_b
    only_b = files_b - files_a
    common = files_a & files_b
    
    print(f"\n[{d}]")
    if only_a:
        print(f"  Only in blender: {only_a}")
    if only_b:
        print(f"  Only in TFTF: {only_b}")
    diff = []
    for f in common:
        fa = os.path.join(da, f)
        fb = os.path.join(db, f)
        if os.path.isfile(fa) and os.path.isfile(fb):
            if os.path.getsize(fa) != os.path.getsize(fb):
                diff.append((f, os.path.getsize(fa), os.path.getsize(fb)))
    if diff:
        print("  Size differences:")
        for name, sa, sb in diff:
            print(f"    {name}: blender={sa} vs TFTF={sb}")

