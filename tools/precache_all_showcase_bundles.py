import sys
import time
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.patch_showcase_bundle import patch_character_bundle, CACHE_DIR

def main():
    t0 = time.time()
    sources = []
    sources.extend(glob.glob("extracted_apk/assets/assetpack/*_odr/*.assetbundle"))
    sources.extend(glob.glob("assets_redeco/*.assetbundle"))
    sources.extend(glob.glob("assets_netflix/*.assetbundle"))

    # Deduplicate by filename
    seen = set()
    unique_sources = []
    for s in sources:
        p = Path(s)
        if p.name not in seen:
            seen.add(p.name)
            unique_sources.append(p)

    print(f"Total candidate bundles to check: {len(unique_sources)}")
    patched_count = 0
    for p in unique_sources:
        raw = p.read_bytes()
        res = patch_character_bundle(raw, p.name)
        if len(res) != len(raw):
            patched_count += 1

    dt = time.time() - t0
    print(f"\nFinished in {dt:.1f}s. Patched {patched_count} character bundles into {CACHE_DIR}")

if __name__ == "__main__":
    main()
