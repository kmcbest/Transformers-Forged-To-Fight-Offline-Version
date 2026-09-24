# -*- coding: utf-8 -*-
import sys
import urllib.request
import re

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request("https://unity.com/download", headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'https://[^\s"\'<>]*(?:UnityHub|hub)[^\s"\'<>]*\.exe', html, re.I)
        print("Matches:", set(matches))
except Exception as e:
    print("Error:", e)
