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
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/* Line icons (24px grid, stroke = currentColor) used by stat cards, cards and the admin tablet */
const ICON = {
  ghost: '<path d="M5 21V11a7 7 0 0114 0v10l-2.3-1.6L14.3 21 12 19.4 9.7 21l-2.4-1.6z"/><path d="M9.5 11h.01M14.5 11h.01"/>',
  candy: '<circle cx="12" cy="12" r="4.2"/><path d="M8.3 9.7L4 7.2 3 11zM15.7 14.3l4.3 2.5 1-3.8M10 10.2l4 3.6"/>',
  house: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10M10 20v-6h4v6"/>',
  trophy: '<path d="M8 4h8v5a4 4 0 01-8 0zM8 6H4.5a3 3 0 003.6 4M16 6h3.5a3 3 0 01-3.6 4M12 13v4M8.5 20h7M10 17h4"/>',
  rank: '<path d="M4 20V13h4v7M10 20V8h4v12M16 20v-9h4v9"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  flashlight: '<path d="M7 3h10v4l-2 3v11H9V10L7 7z"/><path d="M7 7h10M12 13.5v2.5"/>',
  calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  gift: '<path d="M4 9h16v4H4zM5.5 13h13v8h-13zM12 9v12M12 9c-2-.3-5-1.3-5-3.2S10 4 12 9c2-5 5-5 5-3.2S14 8.7 12 9z"/>',
  star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
  pin: '<path d="M12 21s7-6.4 7-11.5a7 7 0 00-14 0C5 14.6 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0113 0M16 4.5a3.5 3.5 0 010 7M17.5 14a6.5 6.5 0 014 6"/>',
  flame: '<path d="M12 21c-4 0-6.5-2.6-6.5-6.2C5.5 10 12 7.5 10.5 3c3.5 1.5 8 5.6 8 11.4 0 4-2.7 6.6-6.5 6.6z"/><path d="M12 21c-1.7 0-3-1.2-3-3 0-2.2 3-3.5 3-5.5 1.6 1 3 2.8 3 5.1 0 2-1.3 3.4-3 3.4z"/>',
  plate: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/>',
  check: '<path d="M4.5 12.5l5 5L19.5 7"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>',
  door: '<path d="M5 21V4.5A1.5 1.5 0 016.5 3h11A1.5 1.5 0 0119 4.5V21M3 21h18M15 12h.01"/>',
};
const icon = (n) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n] || ICON.star}</svg>`;

function say(text, err) { // toast; clears itself after a few seconds (timer goes through `timers` so hiding the UI cancels it)
  msg.textContent = text || ''; msg.className = 'msg' + (err ? ' err' : '');
  if (text) timers.push(setTimeout(() => { if (msg.textContent === text) say(''); }, 4500));
}

function theme(t) {
  const r = document.documentElement.style;
  r.setProperty('--a', t.a); r.setProperty('--b', t.b);
  r.setProperty('--a-rgb', rgb(t.a)); r.setProperty('--b-rgb', rgb(t.b));
}

const EXPERIENCES = {}; // kind -> render(event)

const HAS_ART = new Set(['christmas', 'halloween', 'valentines', 'easter', 'stpatricks', 'independence', 'thanksgiving', 'new_years_eve', 'new_years', 'memorial', 'veterans']);
const emblemSrc = (id) => `img/${HAS_ART.has(id) ? id : 'default'}/emblem.svg`; // holidays without custom art share the default badge
const heroSrc = (id) => HAS_ART.has(id) ? `img/${id}/scene.svg` : 'img/default/hero.svg';

function setEmblem(id) {
  if (id) emblem.src = emblemSrc(id);
  emblem.hidden = !id;
  $('#hero').style.backgroundImage = `url(${heroSrc(id)})`;
}

/* Stat cards in the header: [{ icon, label, value, sub?, hot? }] */
function setStats(list) {
  $('#stats').innerHTML = (list || []).map((s, i) => `<div class="stat${s.hot ? ' hot' : ''}" style="--i:${i}"><span class="ic">${icon(s.icon)}</span>
    <b>${esc(s.value)}${s.sub ? ` <small>${esc(s.sub)}</small>` : ''}</b><span>${esc(s.label)}</span></div>`).join('');
}
/* Extra sidebar cards under the list (e.g. city trick or treating) */
function setExtra(html) { $('#extra').innerHTML = html || ''; }

function dateBadge(iso) {
  const [, m, d] = String(iso || '').split('-').map(Number);
  return m ? `<span class="dt"><i>${MONTHS[m - 1]}</i><em>${d}</em></span>` : '<span class="dt"></span>';
}

function render(s) {
  state = s; theme(s.theme);
  const h = s.active[0] || s.upcoming[0];
  $('#title').textContent = h ? h.label : 'No holidays scheduled';
  $('#blurb').textContent = h ? h.blurb || '' : '';
  $('#countdown').textContent = h ? when(h.daysUntil) : '';
  $('#eyebrow').textContent = s.active.length ? 'Seasonal event' : h ? 'Next on the calendar' : '';
  $('#today').textContent = s.date;

  $('.side h2').textContent = 'Coming up'; $('#upcoming').className = ''; // the Halloween contest swaps these for its leaderboard
  const list = s.active.slice(1).concat(s.upcoming).slice(0, 5);
  $('#upcoming').innerHTML = list.length
    ? list.map(x => `<li>${dateBadge(x.date)}<div class="tx"><b>${esc(x.label)}</b><span>${when(x.daysUntil)}</span></div></li>`).join('')
    : '<li><span>Nothing else on the calendar.</span></li>';

  stopAmbient(); setStats([]); setExtra('');
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
  if (next) setStats([{ icon: 'calendar', label: 'Next up', value: when(next.daysUntil) }]);
  main.innerHTML = `<div class="empty"><img src="img/rewards/star.svg" alt=""><h3>${s.active.length ? 'Enjoy the day' : 'A quiet stretch'}</h3>
    <p>${next ? `${esc(next.label)} is ${when(next.daysUntil).toLowerCase()}. Special events open here when the day gets close.` : 'Check back soon.'}</p></div>`;
}

/* Reward art by outcome kind (img/rewards/*.svg); anything unknown gets the star */
const REWARD_ART = { treat: 'candy', trick: 'scare', ghost: 'ghost', empty: 'empty', dud: 'empty', gift: 'gift', basket: 'gift', cash: 'coins', coins: 'coins', egg: 'coins',
  golden: 'coins', jackpot: 'coins', lucky: 'coins', burst: 'star', finale: 'star', door: 'gift', dish: 'gift', candle: 'star' };
const rewardSrc = (kind) => kind === 'prize' ? 'img/halloween/trophy.svg' : `img/rewards/${REWARD_ART[kind] || 'star'}.svg`;

function reveal({ head, label, sub, kind, points }) {
  const rig = $('.rig'); rig.querySelector('.reveal')?.remove();
  const sparks = Array.from({ length: 18 }, (_, i) => `<i style="--r:${i * 20}deg;--d:${-(110 + (i % 3) * 50)}px"></i>`).join('');
  const el = document.createElement('div'); el.className = 'reveal'; el.setAttribute('role', 'status');
  el.innerHTML = `<div class="card"><div class="burst">${sparks}</div><img class="art" src="${rewardSrc(kind)}" alt=""><span class="k">${esc(head)}</span><b>${esc(label)}</b>
    ${sub ? `<small>${esc(sub)}</small>` : ''}${points ? `<span class="pts">+${points} pts</span>` : ''}<span class="hint">Click anywhere to continue</span></div>`;
  const done = () => { el.classList.add('out'); setTimeout(() => el.remove(), 350); };
  el.addEventListener('click', done); rig.appendChild(el); setTimeout(done, 3600);
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
