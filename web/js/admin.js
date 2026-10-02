'use strict';
/* Admin test panel (/holidayadmin). The server owns every rule and permission check; this only renders and sends actions. */
const adminEl = $('#admin');
const KIND_LABEL = { advent: 'Advent calendar', spots: 'Pick and reveal', feast: 'Feast table', countdown: 'Countdown', tribute: 'Tribute vigil', observance: 'Observance card' };

const adminOpen = () => !adminEl.classList.contains('off');
function closeAdmin() { adminEl.classList.add('off'); post('adminClose'); }
function showAdmin(d) { adminEl.classList.remove('off'); renderAdmin(d); }

async function adminDo(action, extra = {}) {
  const res = await post('adminDo', { action, ...extra });
  if (res && res.holidays) renderAdmin(res);
}

function renderAdmin(d) {
  const row = (h) => `<tr class="${h.enabled ? '' : 'dim'}">
    <td class="nm"><img src="${emblemSrc(h.id)}" alt=""><span>${esc(h.label)}</span>${h.natural ? '<em class="tag live">Today</em>' : ''}${h.forced ? '<em class="tag force">Forced</em>' : ''}</td>
    <td class="kd">${KIND_LABEL[h.kind] || h.kind}</td>
    <td class="tg"><label class="sw" title="Enable or disable this holiday"><input type="checkbox" data-a="toggle" data-id="${esc(h.id)}" ${h.enabled ? 'checked' : ''}><i></i></label></td>
    <td class="tg"><label class="sw" title="Treat this holiday as active right now"><input type="checkbox" data-a="force" data-id="${esc(h.id)}" ${h.forced ? 'checked' : ''} ${h.enabled ? '' : 'disabled'}><i></i></label></td>
    <td class="rt"><button data-a="reset" data-id="${esc(h.id)}" ${h.kind === 'observance' ? 'disabled' : ''}>Reset my claims</button></td></tr>`;
  adminEl.innerHTML = `<div class="adm">
    <header>
      <div><h2>Holiday admin</h2><p>Server date <b>${esc(d.date)}</b>${d.override ? ' <em class="tag force">overridden</em>' : ''} \u00b7 clock <b>${esc(d.clock || 'real time')}</b>${d.ghostMax ? ` \u00b7 ghosts active <b>${d.ghosts}/${d.ghostMax}</b>` : ''}</p></div>
      <div class="hb"><button data-a="open">Open player UI</button><button data-a="close">Close</button></div>
    </header>
    <div class="body">
    <section><h3>Testing clock</h3>
      <div class="row"><label>Date <input id="adm-date" type="date" value="${esc(d.date)}"></label><button data-a="date">Apply</button><button data-a="dateReset">Use real date</button>
        <button class="chip" data-a="preset" data-v="${d.year}-10-31">Halloween night</button><button class="chip" data-a="preset" data-v="${d.year}-12-12">Advent (Dec 12)</button><button class="chip" data-a="preset" data-v="${d.year}-12-31">New Year's Eve</button><button class="chip" data-a="preset" data-v="${d.year + 1}-01-01">New Year's Day</button></div>
      <div class="row"><label>Fake time <input id="adm-clock" type="text" size="9" placeholder="23:58:30" value="${esc(d.clock || '')}"></label><button data-a="clock">Apply</button><button data-a="clockReset">Use real time</button><span class="hint">Drives the New Year's Eve countdown (set the date to Dec 31 first).</span></div>
    </section>
    <section><h3>Holidays</h3>
      <table><thead><tr><th>Holiday</th><th>Experience</th><th>Enabled</th><th>Force on now</th><th></th></tr></thead><tbody>${d.holidays.map(row).join('')}</tbody></table>
    </section>
    <section><h3>Tools</h3>
      <div class="row"><button data-a="minutes">Add 30 minutes of playtime (me, today)</button>
        <label>Advent calendar <span class="sw"><input type="checkbox" data-a="advent" ${d.advent ? 'checked' : ''}><i></i></span></label></div>
      <div class="row"><span class="lbl">Halloween</span><button data-a="spawnGhost">Spawn ghost near me</button><button data-a="clearGhosts">Clear ghosts</button>
        <button data-a="addPoints">+100 points (me)</button><button class="warn" data-a="resetContest">Reset contest</button></div>
    </section>
    </div>
    <footer><p class="note" role="status">${esc(d.msg || '')}</p><p class="hint">Enabled/disabled and the advent switch are saved. Forced holidays, date and clock reset on restart.</p></footer>
  </div>`;
}

adminEl.addEventListener('click', (e) => {
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const a = b.dataset.a;
  if (a === 'close') closeAdmin();
  else if (a === 'open') { adminEl.classList.add('off'); post('adminPreview'); }
  else if (a === 'date') adminDo('date', { value: $('#adm-date').value });
  else if (a === 'dateReset') adminDo('date', {});
  else if (a === 'preset') adminDo('date', { value: b.dataset.v });
  else if (a === 'clock') adminDo('clock', { value: $('#adm-clock').value.trim() });
  else if (a === 'clockReset') adminDo('clock', {});
  else if (a === 'reset') adminDo('resetClaims', { id: b.dataset.id });
  else if (a === 'minutes') adminDo('playtime', { minutes: 30 });
  else if (a === 'spawnGhost' || a === 'clearGhosts') adminDo(a);
  else if (a === 'addPoints') adminDo('addPoints', { points: 100 });
  else if (a === 'resetContest') { // two-step confirm: wipes this year's board, winners and ghost catches for everyone
    if (b.dataset.armed) adminDo('resetContest');
    else { b.dataset.armed = '1'; b.textContent = 'Click again to confirm'; }
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
