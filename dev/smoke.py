#!/usr/bin/env python3
"""Click-through smoke test of the NUI preview (mock server). Exits non-zero on any failure.
Setup once: pip install -r dev/requirements.txt && playwright install chromium"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parent.parent / 'web' / 'index.html').as_uri()
results, errors = [], []
def check(name, cond): results.append((name, bool(cond)))

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    pg.on('pageerror', lambda e: errors.append(str(e)))
    def go(q): pg.goto(URL + q); pg.wait_for_timeout(1800)

    go('?holiday=halloween')
    check('contest: sidebar shows the leaderboard', pg.inner_text('.side h2') == 'Leaderboard' and pg.locator('#upcoming.board li').count() == 6)
    check('contest: your row is pinned below the top 5', pg.locator('#upcoming.board li.you.gap').count() == 1)
    check('contest: countdown shows time left', pg.inner_text('#countdown').startswith('Ends in'))
    pg.click('.spot:not([disabled])'); pg.wait_for_timeout(400)
    check('halloween: opening a house increments used', pg.evaluate('state.event.used') == 3)
    check('contest: points from a play land on the board', pg.evaluate('state.event.contest.points') > 85)
    go('?holiday=halloween&closed')
    check('contest closed: podium with three places', pg.locator('.podium .pod').count() == 3 and pg.locator('.results .trophy').count() == 1)
    check('contest closed: claim button for a winner', pg.locator('.grace.ready[data-arg="8"]').count() == 1)
    pg.click('.grace.ready'); pg.wait_for_timeout(400)
    check('contest closed: claiming marks the prize claimed', pg.evaluate('state.event.contest.prize.claimed') is True and pg.locator('.grace.ready').count() == 0)
    go('?holiday=easter')
    check('sidebar resets to Coming up off-contest', pg.inner_text('.side h2') == 'Coming up' and pg.evaluate("document.getElementById('upcoming').className") == '')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('esc hides the UI', pg.evaluate("document.getElementById('app').classList.contains('hidden')"))
    check('timers stop when hidden', pg.evaluate('timers.length') == 0)
    go('?holiday=thanksgiving'); pg.click('.plate.ready'); pg.wait_for_timeout(400)
    check('feast: dish gets served', pg.evaluate('state.event.dishes[3].status') == 'served')
    go('?holiday=memorial'); pg.click('.candle-btn'); pg.wait_for_timeout(400)
    check('tribute: candle lit and total incremented', pg.evaluate('state.event.lit && state.event.total') == 1205)
    go('?holiday=new_years_eve'); pg.wait_for_timeout(600)
    check('countdown ticks', pg.inner_text('.clock b').count(':') == 2)
    go('?holiday=christmas&art'); pg.click('.door.ready'); pg.wait_for_timeout(400)
    check('advent: door claimed and reveal shown', pg.evaluate('state.advent.doors[11].status') == 'claimed' and pg.locator('.reveal').count() == 1)
    pg.click('#skin'); pg.wait_for_timeout(200)
    check('skin toggles to holo', pg.locator('.skin-holo').count() == 1)
    go('?admin'); pg.click('input[data-id=halloween][data-a=toggle]'); pg.wait_for_timeout(200)
    check('admin: toggle disables a holiday', pg.evaluate("ADM.holidays.find(h => h.id === 'halloween').enabled") is False)
    pg.fill('#adm-date', '2026-12-31'); pg.click('button[data-a=date]'); pg.wait_for_timeout(200)
    check('admin: date override reflected', 'overridden' in pg.inner_text('.adm header'))
    check('admin: ghost count in header', 'ghosts active' in pg.inner_text('.adm header'))
    pg.click('button[data-a=resetContest]'); pg.wait_for_timeout(100)
    check('admin: reset contest asks to confirm first', pg.inner_text('button[data-a=resetContest]') == 'Click again to confirm' and 'reset' not in pg.inner_text('.adm .note'))
    pg.click('button[data-a=resetContest]'); pg.wait_for_timeout(200)
    check('admin: reset contest runs on the second click', 'reset' in pg.inner_text('.adm .note'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('esc closes the admin panel first', pg.evaluate("adminEl.classList.contains('off')"))
    b.close()

for n, c in results: print(('PASS ' if c else 'FAIL ') + n)
print('page errors:', errors or 'none')
sys.exit(0 if all(c for _, c in results) and not errors else 1)
