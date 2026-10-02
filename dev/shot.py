#!/usr/bin/env python3
"""Render the browser preview to PNGs in web/screenshots/.
   python dev/shot.py                 everything: every holiday, the holo skin, the jump scare, the admin panel, a contact sheet
   python dev/shot.py halloween easter   only those holidays
Setup once: pip install -r dev/requirements.txt && playwright install chromium"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / 'web' / 'index.html').as_uri()
OUT = ROOT / 'web' / 'screenshots'; OUT.mkdir(exist_ok=True)
IDS = ['christmas', 'halloween', 'valentines', 'easter', 'stpatricks', 'independence', 'thanksgiving', 'new_years_eve', 'new_years', 'memorial', 'veterans',
       'mlk', 'presidents', 'mothers_day', 'juneteenth', 'fathers_day', 'labor', 'columbus']
BG = 'html{background:linear-gradient(160deg,#233246,#0c1420 60%,#1b2733)!important}'  # stand-in for the game world behind the NUI

def main():
    want = sys.argv[1:]; errors = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1920, 'height': 1080})
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        def shot(query, name, wait=2300, act=None):
            pg.goto(URL + query); pg.add_style_tag(content=BG); pg.wait_for_timeout(wait)
            if act: act()
            pg.screenshot(path=str(OUT / f'{name}.png')); print('wrote', OUT / f'{name}.png')
        beam = lambda: (pg.mouse.move(1180, 560), pg.wait_for_timeout(150))  # sweep the flashlight into the sky for the Halloween shot
        for i in (want or IDS): shot(f'?holiday={i}&art', i, act=beam if i == 'halloween' else None)
        if not want:
            shot('?holiday=halloween&force=trick&games', 'halloween_scare', 1900, lambda: (pg.click('.spot:not([disabled])'), pg.wait_for_timeout(260)))
            shot('?holiday=christmas&skin=holo&art', 'holo')
            shot('?holiday=halloween&closed', 'halloween_closed')
            shot('?admin', 'admin', 600)
            shot('?admin', 'admin_holidays', 600, lambda: (pg.click('button[data-tab=holidays]'), pg.click('input[data-id=easter][data-a=force]'), pg.wait_for_timeout(200)))
            shot('?admin', 'admin_halloween', 600, lambda: (pg.click('button[data-tab=halloween]'), pg.wait_for_timeout(200)))
        b.close()
    if not want:
        from PIL import Image
        names = IDS + ['halloween_scare', 'holo']; w, h = 480, 270; cols = 5; sheet = Image.new('RGB', (w * cols, h * -(-len(names) // cols)))
        for k, n in enumerate(names): sheet.paste(Image.open(OUT / f'{n}.png').resize((w, h)), ((k % cols) * w, (k // cols) * h))
        sheet.save(OUT / 'all-holidays.png')
    print('console/page errors:', errors or 'none'); sys.exit(1 if errors else 0)

if __name__ == '__main__': main()
