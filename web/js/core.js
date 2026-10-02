'use strict';
/* Core: helpers, state, render pipeline, NUI messaging.
   Experience modules register themselves in EXPERIENCES (js/events.js); the advent calendar lives in js/advent.js. */
const $ = (s) => document.querySelector(s);
const app = $('#app'), main = $('#main'), msg = $('#msg'), emblem = $('#emblem');
const inGame = typeof GetParentResourceName === 'function';
let state = null, busy = false;

const post = (name, data = {}) => inGame
  ? fetch(`https://${GetParentResourceName()}/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json; charset=UTF-8' }, body: JSON.stringify(data) })
      .then(r => r.json()).catch(() => ({ ok: false, msg: 'Could not reach the server. Try again.' }))
  : mock(name, data);

const esc = (t) => String(t ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const rgb = (hex) => { const n = parseInt(hex.slice(1), 16); return `${n >> 16},${(n >> 8) & 255},${n & 255}`; };
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
const when = (days) => days === 0 ? 'Today' : days > 0 ? (days === 1 ? 'Tomorrow' : `In ${plural(days, 'day')}`) : 'Celebrating now';

function say(text, err) { msg.textContent = text || ''; msg.className = 'msg' + (err ? ' err' : ''); }

function theme(t) {
  const r = document.documentElement.style;
  r.setProperty('--a', t.a); r.setProperty('--b', t.b);
  r.setProperty('--a-rgb', rgb(t.a)); r.setProperty('--b-rgb', rgb(t.b));
}

const EXPERIENCES = {}; // kind -> render(event)

const HAS_ART = new Set(['christmas', 'halloween', 'valentines', 'easter', 'stpatricks', 'independence', 'thanksgiving', 'new_years_eve', 'new_years', 'memorial', 'veterans']);
const emblemSrc = (id) => `img/${HAS_ART.has(id) ? id : 'default'}/emblem.svg`; // holidays without custom art share the default badge

function setEmblem(id) {
  if (id) emblem.src = emblemSrc(id);
  emblem.hidden = !id;
}

function render(s) {
  state = s; theme(s.theme);
  const h = s.active[0] || s.upcoming[0];
  $('#title').textContent = h ? h.label : 'No holidays scheduled';
  $('#blurb').textContent = h ? h.blurb || '' : '';
  $('#countdown').textContent = h ? when(h.daysUntil) : '';
  $('#today').textContent = s.date;

  $('.side h2').textContent = 'Coming up'; $('#upcoming').className = ''; // the Halloween contest swaps these for its leaderboard
  const list = s.active.slice(1).concat(s.upcoming).slice(0, 5);
  $('#upcoming').innerHTML = list.length
    ? list.map(x => `<li><b>${esc(x.label)}</b><span>${when(x.daysUntil)} \u2022 ${esc(x.date)}</span></li>`).join('')
    : '<li><span>Nothing else on the calendar.</span></li>';

  stopAmbient();
  const id = s.advent ? 'christmas' : (s.event && s.event.id) || '';
  app.dataset.holiday = id;
  setEmblem(id || (h && h.id) || '');
  if (s.advent) renderAdvent(s.advent);
  else if (s.event && EXPERIENCES[s.event.kind]) EXPERIENCES[s.event.kind](s.event);
  else renderEmpty(s);
}

function renderEmpty(s) { // observance days and quiet stretches
  syncSkinBtn(null);
  const next = s.upcoming[0];
  main.innerHTML = `<div class="empty"><h3>${s.active.length ? 'Enjoy the day' : 'A quiet stretch'}</h3>
    <p>${next ? `${esc(next.label)} is ${when(next.daysUntil).toLowerCase()}. Special events open here when the day gets close.` : 'Check back soon.'}</p></div>`;
}

function reveal({ head, label, sub }) {
  const rig = $('.rig'); rig.querySelector('.reveal')?.remove();
  const sparks = Array.from({ length: 16 }, (_, i) => `<i style="--r:${i * 22.5}deg;--d:${-(90 + (i % 3) * 45)}px"></i>`).join('');
  const el = document.createElement('div'); el.className = 'reveal'; el.setAttribute('role', 'status');
  el.innerHTML = `<div class="card"><div class="burst">${sparks}</div><span class="k">${esc(head)}</span><b>${esc(label)}</b><small>${esc(sub || 'Click to continue')}</small></div>`;
  const done = () => { el.classList.add('out'); setTimeout(() => el.remove(), 350); };
  el.addEventListener('click', done); rig.appendChild(el); setTimeout(done, 3200);
}

function show(s) {
  app.classList.remove('hidden', 'boot'); void app.offsetWidth; app.classList.add('boot');
  clearTimeout(show.t); show.t = setTimeout(() => app.classList.remove('boot'), 1600);
  say(''); render(s);
}
function hide() { stopAmbient(); app.classList.add('hidden'); } // timers must never run while the UI is closed
function close() { hide(); post('close'); }

window.addEventListener('message', (e) => {
  const { action, state: s } = e.data || {};
  if (action === 'open') show(s);
  else if (action === 'refresh') render(s);
  else if (action === 'close') hide();
});
$('#close').addEventListener('click', close);
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (adminOpen()) closeAdmin(); else if (!app.classList.contains('hidden')) close();
});
