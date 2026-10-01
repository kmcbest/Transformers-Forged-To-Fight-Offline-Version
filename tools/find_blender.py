import os
import glob

candidates = [
    r"C:\Program Files\Blender Foundation\*",
    r"D:\Program Files\Blender Foundation\*",
    r"E:\*",
    r"D:\*",
    r"C:\Users\*\AppData\Local\Programs\*"
]

for pattern in [
    r"C:\Program Files\Blender Foundation\*\blender.exe",
    r"D:\*\blender.exe",
    r"E:\*\blender.exe",
    r"C:\*\blender.exe"
]:
    for p in glob.glob(pattern):
        print("Found blender:", p)
