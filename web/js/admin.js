'use strict';
/* Admin tablet (/holidayadmin). The server owns every rule and permission check; this only renders and sends actions. */
const adminEl = $('#admin');
const KIND_LABEL = { advent: 'Advent calendar', spots: 'Pick and reveal', feast: 'Feast table', countdown: 'Countdown', tribute: 'Tribute vigil', observance: 'Observance card' };
const TABS = [['overview', 'Overview', 'rank'], ['holidays', 'Holidays', 'calendar'], ['time', 'Time travel', 'clock'], ['halloween', 'Halloween', 'ghost']];
let admTab = 'overview', admData = null;

const adminOpen = () => !adminEl.classList.contains('off');
function closeAdmin() { adminEl.classList.add('off'); post('adminClose'); }
function showAdmin(d) { adminEl.classList.remove('off'); renderAdmin(d); }

async function adminDo(action, extra = {}) {
  const res = await post('adminDo', { action, ...extra });
  if (res && res.holidays) renderAdmin(res);
}

const sw = (attrs, on, title, off = false) => `<label class="sw" title="${title}"><input type="checkbox" ${attrs} ${on ? 'checked' : ''} ${off ? 'disabled' : ''}><i></i></label>`;
const tile = (ic, label, value, sub = '', cls = '') => `<div class="tile ${cls}"><span class="ti">${icon(ic)}</span><div><small>${label}</small><b>${value}</b>${sub ? `<em>${sub}</em>` : ''}</div></div>`;

function tabOverview(d) {
  const live = d.holidays.filter(h => (h.natural || h.forced) && h.enabled);
  const pct = d.ghostMax ? Math.round(d.ghosts / d.ghostMax * 100) : 0;
  return `<div class="tiles">
      ${tile('calendar', 'Server date', esc(d.date), d.override ? 'Overridden' : 'Real date', d.override ? 'warn' : '')}
      ${tile('clock', 'Clock', esc(d.clock || 'Real time'), d.clock ? 'Fake clock running' : 'Server time')}
      ${tile('star', 'Active now', live.length, live.map(h => esc(h.label)).join(', ') || 'Nothing running')}
      ${tile('ghost', 'Ghosts active', `${d.ghosts}/${d.ghostMax}`, `<span class="mini"><i style="width:${pct}%"></i></span>`)}
    </div>
    <div class="grid2">
      <section class="pane"><h3>Live holidays</h3>${live.length ? live.map(h => `<div class="li"><img src="${emblemSrc(h.id)}" alt=""><span>${esc(h.label)}</span>${h.forced ? '<em class="tag force">Forced</em>' : '<em class="tag live">Today</em>'}</div>`).join('') : '<p class="muted">No holiday is active on this date. Force one on from the Holidays tab.</p>'}</section>
      <section class="pane"><h3>Quick actions</h3><div class="qa">
        <button data-a="minutes">${icon('clock')}Add 30 min playtime</button>
        <button data-a="spawnGhost">${icon('ghost')}Spawn ghost near me</button>
        <button data-a="preset" data-v="${d.year}-10-31">${icon('calendar')}Jump to Halloween night</button>
        <button data-a="open">${icon('spark')}Open player UI</button></div>
        <div class="li sw-row"><span>Advent calendar</span>${sw('data-a="advent"', d.advent, 'Turn the advent calendar on or off')}</div></section>
    </div>`;
}

function tabHolidays(d) {
  return `<div class="hl">${d.holidays.map(h => `<div class="hrow${h.enabled ? '' : ' dim'}">
      <img src="${emblemSrc(h.id)}" alt=""><div class="hn"><b>${esc(h.label)}</b><span>${KIND_LABEL[h.kind] || esc(h.kind)}</span></div>
      <div class="tags">${h.natural ? '<em class="tag live">Today</em>' : ''}${h.forced ? '<em class="tag force">Forced</em>' : ''}</div>
      <label class="lbl">Enabled ${sw(`data-a="toggle" data-id="${esc(h.id)}"`, h.enabled, 'Enable or disable this holiday')}</label>
      <label class="lbl">Force on ${sw(`data-a="force" data-id="${esc(h.id)}"`, h.forced, 'Treat this holiday as active right now', !h.enabled)}</label>
      <button class="ghost-btn" data-a="reset" data-id="${esc(h.id)}" ${h.kind === 'observance' ? 'disabled' : ''}>Reset my claims</button></div>`).join('')}</div>`;
}

function tabTime(d) {
  return `<div class="grid2">
    <section class="pane"><h3>Date</h3><p class="muted">Pretend the server is on another day. Resets on restart.</p>
      <div class="row"><input id="adm-date" type="date" value="${esc(d.date)}"><button class="pri" data-a="date">Apply</button><button data-a="dateReset">Use real date</button></div>
      <div class="chips"><button class="chip" data-a="preset" data-v="${d.year}-10-31">Halloween night</button><button class="chip" data-a="preset" data-v="${d.year}-11-26">Thanksgiving</button>
        <button class="chip" data-a="preset" data-v="${d.year}-12-12">Advent (Dec 12)</button><button class="chip" data-a="preset" data-v="${d.year}-12-31">New Year's Eve</button><button class="chip" data-a="preset" data-v="${d.year + 1}-01-01">New Year's Day</button></div></section>
    <section class="pane"><h3>Clock</h3><p class="muted">Runs a fake clock from the time you set. Drives the New Year's Eve countdown and the contest close.</p>
      <div class="row"><input id="adm-clock" type="text" size="9" placeholder="23:59:30" value="${esc(d.clock || '')}"><button class="pri" data-a="clock">Apply</button><button data-a="clockReset">Use real time</button></div>
      <div class="chips"><button class="chip" data-a="clockPreset" data-v="23:59:30">23:59:30</button><button class="chip" data-a="clockPreset" data-v="20:00">20:00</button><button class="chip" data-a="clockPreset" data-v="12:00">Noon</button></div></section>
  </div>`;
}

function tabHalloween(d) {
  const pct = d.ghostMax ? Math.round(d.ghosts / d.ghostMax * 100) : 0;
  return `<div class="tiles">
      ${tile('ghost', 'Ghosts active', `${d.ghosts}/${d.ghostMax}`, `<span class="mini"><i style="width:${pct}%"></i></span>`)}
      ${tile('flashlight', 'Catch mode', d.flashlight ? 'Flashlight' : 'Walk up', d.flashlight ? 'Beam must stay on the ghost' : 'Press E next to it')}
      ${tile('door', 'City doors', d.doors || 0, 'Trick or treat spots on the map')}
    </div>
    <div class="grid2">
      <section class="pane"><h3>Ghosts</h3><p class="muted">Spawned ghosts ignore the night-only rule so you can test any time.</p>
        <div class="qa"><button class="pri" data-a="spawnGhost">${icon('ghost')}Spawn ghost near me</button><button data-a="clearGhosts">${icon('spark')}Clear all ghosts</button></div></section>
      <section class="pane"><h3>Contest</h3><p class="muted">Give yourself points to test the board, or wipe this year's contest.</p>
        <div class="qa"><button data-a="addPoints">${icon('trophy')}+100 points (me)</button><button class="warn" data-a="resetContest">${icon('flame')}Reset contest</button></div>
        <p class="hint">Reset removes every score, winner, ghost catch and door knock for this year. It asks twice.</p></section>
    </div>`;
}
const TAB_FN = { overview: tabOverview, holidays: tabHolidays, time: tabTime, halloween: tabHalloween };

function renderAdmin(d) {
  admData = d;
  const now = new Date(), hhmm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const tabName = TABS.find(t => t[0] === admTab)[1];
  adminEl.innerHTML = `<div class="tablet"><i class="cam"></i><div class="screen">
    <div class="status"><b>${hhmm}</b><span>S2 Admin</span><span class="sys"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M2 9a15 15 0 0120 0M5.5 12.5a10 10 0 0113 0M9 16a5 5 0 016 0M12 19.5h.01"/></svg>
      <span class="batt"><i></i></span>87%</span></div>
    <div class="adm">
      <nav class="nav"><div class="app"><img src="img/brand.svg" alt=""><div><b>Holiday admin</b><span>s2-holidays</span></div></div>
        ${TABS.map(([id, label, ic]) => `<button class="tab${admTab === id ? ' on' : ''}" data-tab="${id}">${icon(ic)}<span>${label}</span></button>`).join('')}
        <div class="nav-foot"><button data-a="open">${icon('spark')}Open player UI</button><button data-a="close">Close tablet</button></div></nav>
      <div class="content">
        <header><div><h2>${tabName}</h2><p>Server date <b>${esc(d.date)}</b>${d.override ? ' <em class="tag force">overridden</em>' : ''} · clock <b>${esc(d.clock || 'real time')}</b>${d.ghostMax ? ` · ghosts active <b>${d.ghosts}/${d.ghostMax}</b>` : ''}</p></div></header>
        <div class="body">${TAB_FN[admTab](d)}</div>
        <footer><p class="note" role="status">${esc(d.msg || '')}</p><p class="hint">Enabled holidays and the advent switch are saved. Forced holidays, date and clock reset on restart.</p></footer>
      </div>
    </div><i class="homebar"></i></div></div>`;
}

adminEl.addEventListener('click', (e) => {
  if (e.target === adminEl) return closeAdmin(); // click outside the tablet
  const t = e.target.closest('button[data-tab]');
  if (t) { admTab = t.dataset.tab; return renderAdmin(admData); }
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const a = b.dataset.a;
  if (a === 'close') closeAdmin();
  else if (a === 'open') { adminEl.classList.add('off'); post('adminPreview'); }
  else if (a === 'date') adminDo('date', { value: $('#adm-date').value });
  else if (a === 'dateReset') adminDo('date', {});
  else if (a === 'preset') adminDo('date', { value: b.dataset.v });
  else if (a === 'clock') adminDo('clock', { value: $('#adm-clock').value.trim() });
  else if (a === 'clockPreset') adminDo('clock', { value: b.dataset.v });
  else if (a === 'clockReset') adminDo('clock', {});
  else if (a === 'reset') adminDo('resetClaims', { id: b.dataset.id });
  else if (a === 'minutes') adminDo('playtime', { minutes: 30 });
  else if (a === 'spawnGhost' || a === 'clearGhosts') adminDo(a);
  else if (a === 'addPoints') adminDo('addPoints', { points: 100 });
  else if (a === 'resetContest') { // two-step confirm: wipes this year's board, winners, ghost catches and door knocks for everyone
    if (b.dataset.armed) adminDo('resetContest');
    else { b.dataset.armed = '1'; b.lastChild.textContent = 'Click again to confirm'; }
  }
});

adminEl.addEventListener('change', (e) => {
  const i = e.target.closest('input[data-a]'); if (!i) return;
  const a = i.dataset.a;
  if (a === 'toggle') adminDo('toggle', { id: i.dataset.id, enabled: i.checked });
  else if (a === 'force') adminDo('force', { id: i.dataset.id, on: i.checked });
  else if (a === 'advent') adminDo('advent', { enabled: i.checked });
});

window.addEventListener('message', (e) => {
  const { action, data } = e.data || {};
  if (action === 'admin') showAdmin(data);
  else if (action === 'adminHide') adminEl.classList.add('off');
});
