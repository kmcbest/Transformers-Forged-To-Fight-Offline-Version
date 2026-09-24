# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

backup_root = Path("demolishor_backup")
keep_files = {"README.md"}

removed_count = 0
for item in backup_root.iterdir():
    if item.is_file() and item.name not in keep_files:
        item.unlink()
        removed_count += 1

print(f"[✓] Cleaned up {removed_count} truncated/redundant files from backup root.")
