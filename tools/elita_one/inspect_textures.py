from PIL import Image
import numpy as np

def inspect(name, p):
    img = Image.open(p)
    arr = np.array(img)
    print(f"\nTexture: {name} (shape: {arr.shape}, dtype: {arr.dtype})")
    if len(arr.shape) == 3:
        for c, cname in enumerate(["R", "G", "B", "A"][:arr.shape[2]]):
            channel = arr[:, :, c]
            print(f"  Channel {cname}: min={channel.min()}, mean={channel.mean():.1f}, max={channel.max()}")
    else:
        print(f"  Grayscale: min={arr.min()}, mean={arr.mean():.1f}, max={arr.max()}")

inspect("Arcee Diffuse", r"E:\Agent\TFTF-blender\tools\elita_one\arcee_extracted\cha_arcee_gs_deluxe2014_main_a.png")
inspect("Arcee RAOE", r"E:\Agent\TFTF-blender\tools\elita_one\arcee_extracted\main_tform_misc_RAOE.png")
inspect("Elita D00", r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\T_CH11_00_D.png")
inspect("Elita R00", r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\T_CH11_00_R.png")
inspect("Elita O00", r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\T_CH11_00_O.png")
inspect("Elita Glow00", r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\textures\MI_CH11_00_glow.tga.png")
