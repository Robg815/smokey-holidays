#!/usr/bin/env python3
"""Builds dist/s2-holidays.zip with only what a server needs (no dev tools, docs or screenshots). Unzip into resources/."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ['fxmanifest.lua', 'config.lua', 'config_world.lua', 'README.md', 'LICENSE', 'docs/live-test.md']
DIRS = ['client', 'server', 'web']
SKIP = {'screenshots'}

out = ROOT / 'dist' / 's2-holidays.zip'
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        if (ROOT / f).exists(): z.write(ROOT / f, f's2-holidays/{f}')
    for d in DIRS:
        for p in sorted((ROOT / d).rglob('*')):
            if p.is_file() and not SKIP & set(p.relative_to(ROOT).parts):
                z.write(p, f's2-holidays/{p.relative_to(ROOT)}')
    names = z.namelist()
print(f'wrote {out.relative_to(ROOT)} ({len(names)} files, {out.stat().st_size // 1024} KB)')
