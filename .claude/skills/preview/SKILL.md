---
description: Render the browser preview of the NUI to PNGs and review them. Use after any change under web/ or when asked how a holiday looks.
argument-hint: [holiday-id ...]
---
Render screenshots with `python dev/shot.py $ARGUMENTS` (no argument renders every holiday, the holo skin, the jump scare and the admin panel).

Then open the PNGs in `web/screenshots/` and review them for: clipped or overlapping art, text overflow, weak contrast,
console or page errors printed by the script, and consistency with the look described in CLAUDE.md.
Fix what you find and re-render until clean. Finish with a short summary of what you checked and changed.
