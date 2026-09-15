from fontTools.ttLib import TTFont

font = TTFont("tools/extracted_font.ttf")
cmap = font.getBestCmap()
print("Total cmap entries:", len(cmap))
pua_chars = []
for code, name in cmap.items():
    # Check if PUA or non-standard
    # Standard ASCII/Latin usually <= 0x024F
    # PUA: 0xE000-0xF8FF, 0xF0000-0xFFFFD, 0x100000-0x10FFFD
    if (0xE000 <= code <= 0xF8FF) or (0xF0000 <= code <= 0xFFFFD) or (0x100000 <= code <= 0x10FFFD):
        pua_chars.append((code, name))
    elif code > 0x0500:
        # Let's also see what other codes exist
        pass

print(f"PUA chars count: {len(pua_chars)}")
for code, name in pua_chars:
    print(f"U+{code:04X} (\\u{code:04x}): {name}")
