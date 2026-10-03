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
  coin: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5.5" stroke-dasharray="1.5 2"/><path d="M12 9.2l.9 1.9 2 .3-1.5 1.4.4 2-1.8-1-1.8 1 .4-2-1.5-1.4 2-.3z"/>',
  hardhat: '<path d="M4 16a8 8 0 0116 0M3 16h18v3H3zM10 8.3V12M14 8.3V12"/>',
  wave: '<path d="M2 15c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M2 19.5c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M12 10V3l4 3"/>',
  run: '<circle cx="15" cy="4.5" r="2"/><path d="M8 21l3-6 3 2v5M6 11l4-3 4 1 2 4 3 1M11 15l-1-5"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>',
  heart: '<path d="M12 20s-8-5-8-10.5A4.5 4.5 0 0112 7a4.5 4.5 0 018 2.5C20 15 12 20 12 20z"/>',
  mail: '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3.5 7l8.5 6.5L20.5 7"/>',
  beer: '<path d="M6 8h10v12H6zM16 11h2.5a1.5 1.5 0 011.5 1.5v3a1.5 1.5 0 01-1.5 1.5H16M6 8c0-2 1.5-3 3-3 .5-1.5 4-1.5 4.5 0 1.5 0 2.5 1 2.5 3M9.5 11v6M12.5 11v6"/>',
  egg: '<path d="M12 21c-4 0-6.5-3-6.5-7S8 3 12 3s6.5 7 6.5 11-2.5 7-6.5 7z"/><path d="M6 13l2.5-1.5L11 13l2.5-1.5L16 13l2-1"/>',
  firework: '<path d="M12 14v8M12 14l-1-6M12 14l4-5M12 14l-5-3M12 14l6 0M8 4l.5 2M17 5l-1 1.5M4 9l2 .5M20 10l-2 .5M12 2v2"/>',
  box: '<path d="M3 7.5l9-4.5 9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9M7.5 5.2l9 4.5"/>',
  music: '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
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

const HAS_ART = new Set(['christmas', 'halloween', 'valentines', 'easter', 'stpatricks', 'independence', 'thanksgiving', 'new_years_eve', 'new_years', 'memorial', 'labor']); // every holiday has its own art
const emblemSrc = (id) => `img/${HAS_ART.has(id) ? id : 'default'}/emblem.webp`; // holidays without custom art share the default badge
const heroSrc = (id) => HAS_ART.has(id) ? `img/${id}/scene.webp` : 'img/default/hero.webp';

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

/* The holiday on screen: the one the player picked in "Happening now", else the headline holiday */
const current = (s) => (s.sel && s.active.find(x => x.id === s.sel)) || s.active[0] || s.upcoming[0];

const hubMode = (s) => !s.events; // the server sends `events` only when Config.MenuGames is on
function renderNow(s, h) { // switcher shown when more than one holiday is running at once
  const has = (x) => hubMode(s) ? (s.world && s.world[x.id]) || (s.contest && s.contest[x.id]) || (x.id === 'christmas' && s.advent)
    : x.id === 'christmas' ? s.advent : s.events[x.id];
  const el = $('#now'), live = s.active.filter(has);
  el.hidden = live.length < 2; if (el.hidden) return;
  el.innerHTML = `<h2>Happening now</h2><div class="sw-list">${live.map(x => `<button class="pick${x.id === h.id ? ' on' : ''}" data-sel="${esc(x.id)}"><img src="${emblemSrc(x.id)}" alt=""><span>${esc(x.label)}</span></button>`).join('')}</div>`;
}
$('#now').addEventListener('click', (e) => {
  const b = e.target.closest('[data-sel]'); if (!b || busy || !state) return;
  state.sel = b.dataset.sel; say(''); render(state);
});

function render(s) {
  state = s;
  const h = current(s);
  theme((h && h.theme) || s.theme);
  const hub = hubMode(s);
  if (hub) s.event = null; else if (h) s.event = s.events[h.id] || null; // the experience that matches the holiday on screen
  $('#title').textContent = h ? h.label : 'No holidays scheduled';
  $('#blurb').textContent = h ? h.blurb || '' : '';
  $('#countdown').textContent = h ? when(h.daysUntil) : '';
  $('#eyebrow').textContent = s.active.length ? 'Seasonal event' : h ? 'Next on the calendar' : '';
  $('#today').textContent = s.date;

  $('.list-card h2').textContent = 'Coming up'; $('#upcoming').className = ''; // the Halloween contest swaps these for its leaderboard
  renderNow(s, h);
  const list = ($('#now').hidden ? s.active.filter(x => x !== h) : []).concat(s.upcoming).slice(0, 5); // running holidays live in the switcher, not here
  $('#upcoming').innerHTML = list.length
    ? list.map(x => `<li>${dateBadge(x.date)}<div class="tx"><b>${esc(x.label)}</b><span>${when(x.daysUntil)}</span></div></li>`).join('')
    : '<li><span>Nothing else on the calendar.</span></li>';

  stopAmbient(); setStats([]); setExtra('');
  const advent = s.advent && (!h || h.id === 'christmas') && (!hub || s.view === 'advent');
  const live = h && s.active.includes(h); // a running holiday (not just the next one on the calendar)
  const id = advent ? 'christmas' : hub ? (live ? h.id : '') : (s.event && s.event.id) || '';
  app.dataset.holiday = id;
  setEmblem(id || (h && h.id) || '');
  syncBack(hub && advent);
  if (advent) renderAdvent(s.advent);
  else if (hub && live) renderHub(s, h);
  else if (!hub && s.event && EXPERIENCES[s.event.kind]) EXPERIENCES[s.event.kind](s.event);
  else renderEmpty(s);
}

function renderEmpty(s) { // observance days and quiet stretches
  syncSkinBtn(null);
  const next = s.upcoming[0];
  if (next) setStats([{ icon: 'calendar', label: 'Next up', value: when(next.daysUntil) }]);
  main.innerHTML = `<div class="empty"><img src="img/rewards/star.webp" alt=""><h3>${s.active.length ? 'Enjoy the day' : 'A quiet stretch'}</h3>
    <p>${next ? `${esc(next.label)} is ${when(next.daysUntil).toLowerCase()}. Special events open here when the day gets close.` : 'Check back soon.'}</p></div>`;
}

/* Reward art by outcome kind (img/rewards/*.webp); anything unknown gets the star */
const REWARD_ART = { treat: 'candy', trick: 'scare', ghost: 'ghost', empty: 'empty', dud: 'empty', gift: 'gift', basket: 'gift', cash: 'coins', coins: 'coins', egg: 'coins',
  golden: 'coins', jackpot: 'coins', lucky: 'coins', burst: 'star', finale: 'star', door: 'gift', dish: 'gift', candle: 'star', punch: 'coins' };
const rewardSrc = (kind) => kind === 'prize' ? 'img/halloween/trophy.webp' : `img/rewards/${REWARD_ART[kind] || 'star'}.webp`;

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
