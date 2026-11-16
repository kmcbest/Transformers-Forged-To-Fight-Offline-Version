import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_dir = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
files = [
    "rb_brawl_head_mat_inst_b.jpg",
    "rb_brawl_head_mat_inst_n.jpg",
    "rb_brawl_head_mat_inst_e.jpg",
    "rb_brawl_chest_mat_inst_b.jpg",
    "rb_brawl_chest_mat_inst_n.jpg",
    "rb_brawl_chest_mat_inst_e.jpg",
    "rb_brawl_armup_mat_inst_b.jpg",
    "rb_brawl_armup_mat_inst_n.jpg",
    "rb_brawl_armlo_mat_inst_b.jpg",
    "rb_brawl_armlo_mat_inst_n.jpg",
    "rb_brawl_legs_mat_inst_b.jpg",
    "rb_brawl_legs_mat_inst_n.jpg",
    "rb_brawl_legs_mat_inst_e.jpg",
    "vh_brawl_cust_matinst.jpg",
    "vh_brawl_cust_matinst_n.jpg",
    "vh_brawl_cust_matinst_e.jpg",
    "vh_brawlegsl_cust_matinst.jpg",
    "vh_interior_mat.jpg",
    "vh_interior_n.jpg",
]

for fn in files:
    fp = tex_dir / fn
    if fp.exists():
        im = Image.open(fp)
        print(f"{fn:<32}: size={im.size}, mode={im.mode}")
    else:
        print(f"MISSING: {fn}")
