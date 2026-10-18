import zipfile
from pathlib import Path
import time

def unpack():
    ipa_path = Path("e:/Agent/TFTF/TFTF-store-9.2.0.ipa")
    out_dir = Path("e:/Agent/TFTF/assets_ios")
    out_dir.mkdir(exist_ok=True)

    print(f">>> Unpacking {ipa_path} to {out_dir}...")
    start_time = time.time()
    
    with zipfile.ZipFile(ipa_path, "r") as zf:
        namelist = zf.namelist()
        # Find all files under Payload/Transformers.app/Data/
        prefix = "Payload/Transformers.app/Data/"
        target_files = [n for n in namelist if n.startswith(prefix) and not n.endswith("/")]
        print(f"    Found {len(target_files)} files under {prefix}")
        
        extracted_count = 0
        total_bytes = 0
        for name in target_files:
            rel_name = name[len(prefix):]
            dest = out_dir / rel_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = zf.read(name)
            dest.write_bytes(data)
            total_bytes += len(data)
            extracted_count += 1
            if extracted_count % 200 == 0:
                print(f"    Extracted {extracted_count}/{len(target_files)} files ({total_bytes/1024/1024:.1f} MB)...")

    duration = time.time() - start_time
    print(f"[OK] Extracted {extracted_count} files ({total_bytes/1024/1024:.2f} MB) in {duration:.2f} seconds!")

if __name__ == "__main__":
    unpack()
