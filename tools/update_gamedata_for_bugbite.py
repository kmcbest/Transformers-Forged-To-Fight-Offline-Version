import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

p = Path("Server/gamedata.py")
text = p.read_text(encoding="utf-8")

# 1. Update ROSTER factions
# dirge
text = text.replace('"dirge_gs_deluxe2008":          ("decepticon", "warr", 5),',
                    '"dirge_gs_deluxe2008":          ("mercenary",  "warr", 5),')
# ramjet
text = text.replace('"ramjet_gs_deluxe2008":         ("decepticon", "demo", 5),',
                    '"ramjet_gs_deluxe2008":         ("mercenary",  "demo", 5),')
# soundblaster
text = text.replace('"soundblaster_gs_mp13b":        ("decepticon", "tact", 5),',
                    '"soundblaster_gs_mp13b":        ("mercenary",  "tact", 5),')
# thrust
text = text.replace('"thrust_gs_deluxe2008":         ("decepticon", "scou", 5),',
                    '"thrust_gs_deluxe2008":         ("mercenary",  "scou", 5),')

# Add bugbite to ROSTER right after tantrum_gs_kabam
old_tantrum = '"tantrum_gs_kabam":             ("decepticon", "braw", 5),'
new_tantrum = old_tantrum + '\n    "bugbite_gs_kabam":             ("mercenary",  "braw", 5),'
if '"bugbite_gs_kabam"' not in text:
    text = text.replace(old_tantrum, new_tantrum)

# 2. Add bugbite to _ART_BASE
old_art = '"bumblebee_gs_kabam": "bumbl_gs",'
new_art = old_art + '\n    "bugbite_gs_kabam": "bugbite_gs",'
if '"bugbite_gs_kabam": "bugbite_gs"' not in text:
    text = text.replace(old_art, new_art)

# 3. Add bugbite to _BOT_NAMES
old_bot = '"bumblebee_gs_kabam": "Bumblebee",'
new_bot = old_bot + '\n    "bugbite_gs_kabam": "Bug Bite",'
if '"bugbite_gs_kabam": "Bug Bite"' not in text:
    text = text.replace(old_bot, new_bot)

p.write_text(text, encoding="utf-8")
print("[+] Updated Server/gamedata.py successfully!")
