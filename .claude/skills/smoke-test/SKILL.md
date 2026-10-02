---
description: Run the NUI click-through smoke test and fix any failures. Use before finishing any change that touches web/.
---
Run `python dev/smoke.py`. It exits non-zero on any failure.
If a check fails, find the root cause (do not weaken the check unless the behavior was intentionally changed),
fix it, and re-run until every line prints PASS and there are no page errors. If you added behavior, add a check for it
to `dev/smoke.py` in the same style.
