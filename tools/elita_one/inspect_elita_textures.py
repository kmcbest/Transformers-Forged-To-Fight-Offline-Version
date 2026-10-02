from PIL import Image
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEX_DIR = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures"

print("=== Inspecting Elita One Textures ===")
for p in sorted(TEX_DIR.glob("*.png")):
    img = Image.open(p)
    arr = np.array(img)
    mean_val = arr.mean() if len(arr.shape) == 2 else arr[:,:,:3].mean()
    print(f"  {p.name:25s}: {img.size}, mode={img.mode}, mean={mean_val:.1f}")
