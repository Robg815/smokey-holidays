---
paths:
  - "web/**"
---
# Web (NUI) rules
- No frameworks, bundlers, remote assets or web fonts. Escape every dynamic string with `esc()`.
- Timers: use `later()` / `timers`; `stopAmbient()` must be able to cancel everything when the UI hides or re-renders.
- New holiday scene: CSS in `css/events.css`, art in `img/<id>/scene.svg` + `emblem.svg` (add the id to `HAS_ART` in
  `js/core.js`), preview data in `js/preview.js`, and a case in `dev/smoke.py`.
- Style with the theme tokens (`var(--a)`, `rgba(var(--a-rgb), .2)`), never hard-coded accent colors on shared pieces.
- After any visual change run `/preview <id>` and look at the PNG before calling it done.
