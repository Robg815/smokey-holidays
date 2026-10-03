'use strict';
/* ==========================================================================
   Holiday experiences. The server rolls every outcome; the UI only presents it.
   ========================================================================== */
let timers = [];
const stopAmbient = () => { timers.forEach(clearTimeout); timers = []; };
const later = (fn, min, max) => timers.push(setTimeout(fn, min + Math.random() * (max - min)));
const rnd = (a, b) => a + Math.random() * (b - a);
const pick = (a) => a[Math.floor(Math.random() * a.length)];

const GHOST = '<svg viewBox="0 0 60 70"><path d="M8 66V28C8 12 18 4 30 4s22 8 22 24v38l-7-6-7 6-8-6-8 6-7-6z" fill="#eafcff" opacity=".93"/><circle cx="22" cy="28" r="4" fill="#1a0b2e"/><circle cx="38" cy="28" r="4" fill="#1a0b2e"/><ellipse cx="30" cy="42" rx="5" ry="7" fill="#1a0b2e"/></svg>';
const BAT = '<svg viewBox="0 0 40 20"><path d="M20 10c-3-6-9-8-18-4 3 0 5 2 6 5 2-1 4 0 5 3 2-2 5-2 7 0 1-3 3-4 5-3 1-3 3-5 6-5C29 2 23 4 20 10z" fill="#0b0413"/></svg>';

/* Spot art: (opened outcome | undefined, spot number) => svg */
const HOUSE = (o) => {
  const lit = o && o.kind === 'empty' ? '#2a1a38' : '#ffb347';
  const door = !o ? '#5a3216' : o.kind === 'empty' ? '#0d0713' : o.kind === 'trick' ? '#c1002f' : '#ffd36b';
  return `<svg viewBox="0 0 100 120"><path d="M4 54L50 12l46 42z" fill="#1c0f26" stroke="#7a45a0" stroke-width="2"/><rect x="12" y="54" width="76" height="60" fill="#241335" stroke="#7a45a0" stroke-width="2"/><rect x="20" y="64" width="16" height="16" rx="2" fill="${lit}"/><rect x="64" y="64" width="16" height="16" rx="2" fill="${lit}"/><rect x="40" y="76" width="20" height="38" rx="2" fill="${door}" stroke="#000" stroke-opacity=".4"/><circle cx="55" cy="96" r="1.8" fill="#e6b84a"/><ellipse cx="80" cy="108" rx="8" ry="6.5" fill="#ff8a1f"/><path d="M80 101v-4" stroke="#3a7d2a" stroke-width="2"/></svg>`;
};
const ENV = (o) => `<svg viewBox="0 -8 100 88"><rect x="4" y="16" width="92" height="60" rx="6" fill="#ffd7e6" stroke="#e0508a" stroke-width="2"/>${o
  ? '<path d="M4 22L50 -2l46 24z" fill="#ffb6d1" stroke="#e0508a" stroke-width="2"/><rect x="18" y="6" width="64" height="44" rx="3" fill="#fff" stroke="#e0508a"/><path d="M50 40c-14-9-14-20-4-20 3 0 4 3 4 3s1-3 4-3c10 0 10 11-4 20z" fill="#e0243f"/>'
  : '<path d="M4 20L50 52l46-32" fill="#ffc2da" stroke="#e0508a" stroke-width="2"/><path d="M50 60c-12-8-12-18-3-18 2 0 3 2 3 2s1-2 3-2c9 0 9 10-3 18z" fill="#e0243f"/>'}</svg>`;
const EGGC = ['#ff9ecb', '#9ed8ff', '#ffe27a', '#b9f0a0', '#c9a5ff', '#ffb38a', '#8fe3d0', '#ff9a9a'];
const EGG = (o, n) => `<svg viewBox="0 0 60 80"><ellipse cx="30" cy="46" rx="22" ry="30" fill="${EGGC[(n - 1) % 8]}" stroke="#0003" stroke-width="2"/><path d="M8 44l8-6 8 6 8-6 8 6 8-6 6 5M10 58l10-6 10 6 10-6 10 6" fill="none" stroke="#fff" stroke-width="3" opacity=".75"/>${o
  ? (o.kind === 'empty' ? '<path d="M14 30l8 8-6 6 10 4" stroke="#0007" stroke-width="3" fill="none"/>' : '<path d="M30 20l4 10 11 1-8 7 3 11-10-6-10 6 3-11-8-7 11-1z" fill="#ffe27a" stroke="#c9961a" stroke-width="1.5"/>')
  : '<ellipse cx="22" cy="30" rx="5" ry="9" fill="#fff" opacity=".35" transform="rotate(20 22 30)"/>'}</svg>`;
const CLOVER = (o) => {
  const dud = o && o.kind === 'dud';
  return `<svg viewBox="0 0 60 70"><path d="M30 38C30 52 26 62 20 68" stroke="#1f7a3a" stroke-width="3" fill="none"/><g fill="${dud ? '#7a8a4a' : '#2fbf5a'}" stroke="${dud ? '#4d5a2a' : '#14733a'}" stroke-width="2"><circle cx="21" cy="21" r="12"/><circle cx="39" cy="21" r="12"/><circle cx="21" cy="39" r="12"/><circle cx="39" cy="39" r="12"/></g>${o && !dud
    ? '<circle cx="30" cy="30" r="15" fill="#f5c542" stroke="#b8860b" stroke-width="3"/><text x="30" y="36" text-anchor="middle" font-size="16" font-weight="700" fill="#8a5a00">$</text>'
    : '<circle cx="30" cy="30" r="4" fill="#14733a"/>'}</svg>`;
};
const ROCKET = (o) => o
  ? '<svg viewBox="0 0 60 100"><rect x="26" y="70" width="8" height="28" fill="#5b3a1e"/><ellipse cx="30" cy="96" rx="14" ry="3" fill="#000" opacity=".4"/></svg>'
  : '<svg viewBox="0 0 60 100"><path d="M30 4c10 10 12 30 10 52H20c-2-22 0-42 10-52z" fill="#f4f6ff" stroke="#3b57c8" stroke-width="2"/><path d="M30 4c6 6 9 14 10 22H20c1-8 4-16 10-22z" fill="#d7263d"/><circle cx="30" cy="42" r="6" fill="#3b57c8"/><path d="M20 56l-10 14 10-4zM40 56l10 14-10-4z" fill="#d7263d"/><path d="M24 58h12l-3 10h-6z" fill="#ffb347"/><rect x="26" y="70" width="8" height="28" fill="#5b3a1e"/></svg>';

const CARD = (o) => `<svg viewBox="0 0 70 100"><rect x="3" y="3" width="64" height="94" rx="8" fill="${o ? '#f6f0d8' : '#141c52'}" stroke="#f5c542" stroke-width="3"/>${o
  ? (o.kind === 'empty' ? '<path d="M20 50h30" stroke="#8a7a4a" stroke-width="4" stroke-linecap="round"/>' : '<path d="M35 24l6 16 17 1-13 11 4 17-14-9-14 9 4-17-13-11 17-1z" fill="#f5c542" stroke="#b8860b" stroke-width="2"/>')
  : '<path d="M35 26l4 10 11 1-8 7 3 11-10-6-10 6 3-11-8-7 11-1z" fill="#f5c542"/><circle cx="35" cy="76" r="8" fill="none" stroke="#f5c542" stroke-width="2"/>'}</svg>`;

const SCENES = {
  halloween: { art: HOUSE, cta: 'Knock', bg: '<i class="fog"></i>',
    amb: { cls: 'bat', n: 3, still: 1, colors: ['#000'], html: BAT },
    line: (l, ev) => l ? `${plural(l, 'house')} left to visit tonight.${ev.ghost ? ' Watch the sky for ghosts.' : ''}` : 'The street has gone quiet. Come back tomorrow night.',
    mock: [['treat', 'Candy haul', 'Full-size bars. Jackpot.'], ['trick', 'Jump scare', 'Something jumped out.'], ['ghost', 'Ghost loot', 'A ghost slipped you something.'], ['empty', 'Nobody home', 'The lights are off.']] },
  valentines: { art: ENV, cta: 'Open', bg: '', amb: { cls: 'heart', n: 30, up: 1, colors: ['#ff6fb5', '#ffc2e0', '#ff4d7a'] },
    line: (l) => l ? 'Someone left you sealed letters. Pick one.' : "You've read today's letter. Come back tomorrow.",
    mock: [['gift', 'Chocolates', 'A box of chocolates.'], ['cash', 'Love note cash', 'Cash folded inside.'], ['jackpot', 'Golden ticket', 'Somebody really likes you.'], ['empty', 'Wrong address', 'Return to sender.']] },
  easter: { art: EGG, cta: 'Crack', bg: '<i class="cloud c1"></i><i class="cloud c2"></i>', amb: null,
    line: (l) => l ? `${plural(l, 'egg')} left to find today.` : "Basket's full. More eggs tomorrow.",
    mock: [['egg', 'Pocket cash', 'A few dollars in foil.'], ['golden', 'Golden egg', 'Very rare!'], ['basket', 'Basket goodies', 'Bandages and snacks.'], ['empty', 'Cracked egg', 'Empty.']] },
  stpatricks: { art: CLOVER, cta: 'Look', bg: '', amb: { cls: 'coin', n: 10, colors: ['#f5c542', '#ffd86b'] },
    line: (l) => l ? `Search the clover patch. ${plural(l, 'look')} left today.` : 'The rainbow has faded. Come back tomorrow.',
    mock: [['coins', 'Gold coins', 'Shiny.'], ['lucky', 'Four-leaf clover', 'Luck of the Irish.'], ['dud', 'Just clover', 'Nothing here.']] },
  independence: { art: ROCKET, cta: 'Launch', bg: '', amb: { cls: 'star', n: 26, still: 1, colors: ['#fff', '#cfe0ff', '#ffd6d6'] },
    line: (l) => l ? `${plural(l, 'rocket')} left to launch tonight.` : 'Show is over. See you tomorrow.',
    mock: [['burst', 'Big burst', 'Fireworks!'], ['finale', 'Grand finale', 'The whole sky lit up.'], ['dud', 'Fizzled', 'Dud.']] },
  new_years: { art: CARD, cta: 'Draw', bg: '', amb: { cls: 'confetti', n: 26, colors: ['#f5c542', '#ffd86b', '#e8ecff', '#ff9ac1', '#8fd8ff'] },
    line: (l) => l ? 'Draw a card. It sets the tone for your year.' : 'Your resolution is set. See you next year.',
    mock: [['gift', 'Fresh start', 'Supplies for the year ahead.'], ['cash', 'Savings goal', 'A solid start to the year.'], ['jackpot', 'Lucky year', 'This is your year.'], ['empty', 'Same as last year', 'Maybe next time.']] },
};

function ambient(sc, host) {
  const a = sc.amb; if (!a) return;
  host.insertAdjacentHTML('beforeend', Array.from({ length: a.n }, () =>
    `<i class="amb ${a.cls}${a.up ? ' up' : ''}" style="left:${rnd(0, 96).toFixed(0)}%;${a.still ? `top:${rnd(3, 42).toFixed(0)}%;` : ''}--s:${rnd(.6, 1.5).toFixed(2)};--c:${pick(a.colors)};animation-duration:${rnd(7, 16).toFixed(1)}s;animation-delay:-${rnd(0, 14).toFixed(1)}s">${a.html || ''}</i>`).join(''));
}

/* ---------- Halloween: the street is dark. Sweep the flashlight (your cursor) over a ghost and hold it there to trap it. ---------- */
const mouse = { x: -1e4, y: -1e4 };
const BEAM_R = 72, CHARGE_MS = 1300, TICK = 60;
function aimBeam() {
  const scene = $('.scene.lights-out'); if (!scene) return;
  const r = scene.getBoundingClientRect();
  scene.style.setProperty('--mx', `${mouse.x - r.left}px`); scene.style.setProperty('--my', `${mouse.y - r.top}px`);
}
window.addEventListener('mousemove', (e) => { mouse.x = e.clientX; mouse.y = e.clientY; aimBeam(); });

function launchGhost(scene) {
  scene.insertAdjacentHTML('beforeend', `<span class="ghost" style="--y:${rnd(8, 40).toFixed(0)}%;--c:0">${GHOST}<i class="ring"></i></span>`);
  const g = scene.lastElementChild; g.charge = 0;
  timers.push(setTimeout(() => g.remove(), 9200));
  return g;
}

function flashlight(scene) { // charges any ghost under the beam; a full charge traps it
  (function tick() {
    scene.querySelectorAll('.ghost:not(.pop)').forEach((g) => {
      const r = g.getBoundingClientRect(), on = Math.hypot(r.left + r.width / 2 - mouse.x, r.top + r.height / 2 - mouse.y) < BEAM_R + r.width / 3;
      g.charge = on ? Math.min(1, g.charge + TICK / CHARGE_MS) : Math.max(0, g.charge - TICK / (CHARGE_MS * 2));
      g.style.setProperty('--c', g.charge.toFixed(2)); g.classList.toggle('lit', on);
      if (g.charge >= 1 && !busy) act(g, 9);
    });
    timers.push(setTimeout(tick, TICK));
  })();
}

function haunt(ev, scene) { // random ghosts and lightning while the street is open
  if (ev.ghost) later(function spawn() { launchGhost(scene); later(spawn, 9000, 17000); }, 2500, 6000);
  later(function bolt() { scene.classList.add('flash'); setTimeout(() => scene.classList.remove('flash'), 400); later(bolt, 7000, 15000); }, 4500, 9000);
  flashlight(scene); aimBeam();
}

const SPOT_ICON = { halloween: 'house', valentines: 'gift', easter: 'gift', stpatricks: 'star', independence: 'spark', new_years: 'star' };
function spotStats(ev, left) {
  const c = ev.contest;
  if (c) return setStats([
    { icon: 'trophy', label: 'Your score', value: ptsText(c.points), hot: true },
    { icon: 'rank', label: 'Leaderboard', value: c.rank ? `#${c.rank}` : 'Unranked' },
    ev.doors ? { icon: 'door', label: 'City doors tonight', value: ev.doors.today, sub: `/ ${ev.doors.cap}` } : { icon: 'house', label: 'Houses left', value: left, sub: `/ ${ev.picks}` },
    ev.world ? { icon: 'ghost', label: 'Ghosts today', value: ev.world.today, sub: `/ ${ev.world.cap}` } : null,
  ].filter(Boolean));
  setStats([{ icon: SPOT_ICON[ev.id] || 'star', label: 'Left today', value: left, sub: `/ ${ev.picks}` }, { icon: 'check', label: 'Opened today', value: ev.used }]);
}

function cityCards(ev) { // one sidebar card for the city-wide parts of Halloween: door knocking and ghost hunting
  const d = ev.doors, w = ev.world; if (!d && !w) return;
  const meter = (ic, label, n, cap) => `<div class="meter">${icon(ic)}<div><p><span>${label}</span><b>${n}/${cap}</b></p><div class="bar"><i style="width:${cap ? Math.min(100, n / cap * 100) : 0}%"></i></div></div></div>`;
  setExtra(`<section class="card city"><h2>Around the city${d ? `<span class="badge">${d.total} houses</span>` : ''}</h2>
    ${d ? `<div class="map"><img src="img/halloween/map.svg" alt=""><span>${icon('pin')} Pumpkin markers on your map</span></div>` : ''}
    ${d ? meter('door', 'Doors tonight', d.today, d.cap) : ''}${w ? meter(w.flashlight === false ? 'ghost' : 'flashlight', w.flashlight === false ? 'Ghosts caught today' : 'Ghosts trapped with a flashlight', w.today, w.cap) : ''}
</section>`);
}

function renderSpots(ev) {
  syncSkinBtn(null); stopAmbient();
  if (ev.contest) { renderBoard(ev.contest); if (!ev.contest.open) return renderResults(ev); }
  const sc = SCENES[ev.id] || SCENES.halloween, left = ev.picks - ev.used, by = Object.fromEntries(ev.opened.map(o => [o.n, o]));
  const night = ev.id === 'halloween';
  const spots = Array.from({ length: ev.spots }, (_, i) => {
    const n = i + 1, o = by[n];
    return `<button class="spot ${o ? 'done ' + o.kind : ''}" data-n="${n}" style="--i:${i}" ${o || left <= 0 ? 'disabled' : ''}>${sc.art(o, n)}<small>${esc(o ? o.label : sc.cta)}</small></button>`;
  }).join('');
  main.innerHTML = `<div class="scene sc-${ev.id}${night ? ' lights-out' : ''}">${sc.bg}<div class="spots">${spots}</div>${night ? '<i class="dark"></i><i class="beam"></i>' : ''}</div>
    <div class="progress"><div class="row"><p>${sc.line(left, ev)}${contestLine(ev)}</p>${night && ev.ghost ? `<span class="tip">${icon('flashlight')}Hold your flashlight on a ghost to trap it</span>` : ''}</div>
    <div class="bar"><i style="width:${ev.picks ? ev.used / ev.picks * 100 : 0}%"></i></div></div>`;
  const scene = $('.scene'); ambient(sc, scene);
  spotStats(ev, left);
  if (night) { haunt(ev, scene); cityCards(ev); }
}

/* ---------- Halloween contest: leaderboard in the sidebar, podium once the board closes ---------- */
const ordinal = (n) => n + (['th', 'st', 'nd', 'rd'][(n % 100 - 20) % 10] || ['th', 'st', 'nd', 'rd'][n % 100] || 'th');
const ptsText = (n) => `${Number(n || 0).toLocaleString()} pts`;
const initials = (name) => String(name || '?').split(/\s+/).map(w => w[0] || '').join('').slice(0, 2).toUpperCase();
function endsIn(s) {
  if (s >= 2 * 86400) return `Ends in ${Math.floor(s / 86400)} days`;
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  return h ? `Ends in ${h}h ${m}m` : `Ends in ${Math.max(m, 1)}m`;
}

function contestLine(ev) {
  const c = ev.contest;
  return c && c.hint ? `<br><small class="hint">${esc(c.hint)}</small>` : '';
}

function renderBoard(c) {
  $('.list-card h2').textContent = 'Leaderboard';
  const ul = $('#upcoming'); ul.className = 'board';
  const row = (r, extra = '') => `<li class="r${r.rank}${r.you ? ' you' : ''}${extra}"><em>${r.rank}</em><i class="av">${esc(initials(r.name))}</i><b>${esc(r.name)}</b><span>${ptsText(r.points)}</span></li>`;
  const top = (c.board || []).slice(0, 5), mine = top.some(r => r.you);
  ul.innerHTML = top.length ? top.map(r => row(r)).join('') + (!mine && c.points > 0 ? row({ rank: c.rank, name: 'You', points: c.points, you: true }, ' gap') : '')
    : '<li class="none"><span>No scores yet. Be the first on the board.</span></li>';
  $('#countdown').textContent = c.open ? endsIn(c.secondsLeft) : 'Contest closed';
}

function renderResults(ev) {
  const c = ev.contest, w = c.winners || [], prize = c.prize;
  setStats([{ icon: 'trophy', label: 'Final score', value: ptsText(c.points), hot: true }, { icon: 'rank', label: 'Final rank', value: c.rank ? `#${c.rank}` : 'Unranked' }]);
  const pod = [2, 1, 3].map(p => {
    const x = w.find(r => r.place === p);
    return `<div class="pod p${p}${x && x.you ? ' you' : ''}" style="--i:${p}"><i class="av">${x ? esc(initials(x.name)) : '?'}</i><span class="nm">${x ? esc(x.name) : 'Nobody'}</span><small>${x ? ptsText(x.points) : ''}</small><div class="step"><b>${ordinal(p)}</b></div></div>`;
  }).join('');
  const line = prize ? (prize.claimed ? `You placed ${ordinal(prize.place)}. Your prize has been claimed. Well played.` : `You placed ${ordinal(prize.place)}. Claim your prize before the season ends.`)
    : c.points > 0 ? `The contest is over. You finished #${c.rank} with ${ptsText(c.points)}.` : 'The contest is over. Thanks to everyone who played.';
  const btn = prize ? `<button class="grace ${prize.claimed ? 'done' : 'ready'}" ${prize.claimed ? 'disabled' : 'data-arg="8"'}>${prize.claimed ? 'Prize claimed' : `Claim ${esc(prize.label)}`}</button>` : '';
  main.innerHTML = `<div class="scene sc-halloween results"><i class="fog"></i><img class="trophy" src="img/halloween/trophy.webp" alt=""><div class="podium">${pod}</div></div>
    <div class="progress"><div class="row"><p>${line}</p>${btn}</div></div>`;
}

const DISH = {
  turkey: '<ellipse cx="32" cy="38" rx="20" ry="15" fill="#b8642e" stroke="#7a3a14" stroke-width="2"/><ellipse cx="26" cy="33" rx="9" ry="5" fill="#d98a4a" opacity=".7"/><path d="M14 46l-8 8M50 46l8 8" stroke="#e9d9b8" stroke-width="6" stroke-linecap="round"/><circle cx="6" cy="55" r="4" fill="#f4ead2"/><circle cx="58" cy="55" r="4" fill="#f4ead2"/>',
  stuffing: '<path d="M8 30h48c0 16-10 26-24 26S8 46 8 30z" fill="#c9a26a" stroke="#7a5a2a" stroke-width="2"/><path d="M10 30c4-8 14-12 22-12s18 4 22 12z" fill="#e0b86c"/><circle cx="24" cy="26" r="2.5" fill="#7a9a3a"/><circle cx="36" cy="24" r="2.5" fill="#a55a2a"/><circle cx="44" cy="28" r="2" fill="#7a9a3a"/>',
  pie: '<circle cx="32" cy="34" r="24" fill="#d99a4a" stroke="#8a5a1a" stroke-width="2"/><circle cx="32" cy="34" r="17" fill="#c4682a"/><path d="M15 34h34M32 17v34M20 22l24 24M44 22L20 46" stroke="#e8b46a" stroke-width="3"/>',
  corn: '<path d="M32 8c10 8 12 30 0 46C20 38 22 16 32 8z" fill="#f5c542" stroke="#b8860b" stroke-width="2"/><path d="M26 22h12M25 30h14M26 38h12" stroke="#d9a520" stroke-width="2"/><path d="M32 54c-12 0-20-8-22-18 8 2 14 8 22 18zM32 54c12 0 20-8 22-18-8 2-14 8-22 18z" fill="#4a9a3a"/>',
  rolls: '<g fill="#d8a05a" stroke="#8a5a1a" stroke-width="2"><ellipse cx="20" cy="38" rx="13" ry="10"/><ellipse cx="44" cy="38" rx="13" ry="10"/><ellipse cx="32" cy="24" rx="13" ry="10"/></g><path d="M14 36h12M38 36h12M26 22h12" stroke="#f0c88a" stroke-width="2" stroke-linecap="round"/>',
  cranberry: '<path d="M12 28h40l-4 22H16z" fill="#a4142f" stroke="#5a0a18" stroke-width="2"/><ellipse cx="32" cy="28" rx="20" ry="6" fill="#d02a48"/><path d="M20 34v12M28 34v14M36 34v14M44 34v12" stroke="#7a0f22" stroke-width="2" opacity=".6"/>',
};

const FEAST_COPY = {
  table: { serve: 'Serve', ready: 'Ready to serve', served: 'On the table', btn: 'Give thanks', btnDone: 'Thanks given', head: 'Served', finaleHead: 'Grace', kind: 'dish',
    done: 'The table is set and everyone has eaten. Happy Thanksgiving.', all: 'Every dish is on the table. Time to give thanks.', unit: 'dishes are on the table' },
};

function renderFeast(ev) {
  syncSkinBtn(null); stopAmbient();
  if (ev.style === 'timecard') return renderTimecard(ev);
  const C = FEAST_COPY[ev.style] || FEAST_COPY.table;
  const n = ev.dishes.length, done = ev.dishes.filter(d => d.status === 'served').length;
  setStats([{ icon: 'plate', label: 'Dishes served', value: done, sub: `/ ${n}`, hot: true }, { icon: 'clock', label: 'Played today', value: ev.minutes, sub: 'min' }]);
  const plates = ev.dishes.map((d, i) => `<div class="dish s-${d.status}"><button class="plate ${d.status === 'ready' ? 'ready' : ''}" data-i="${i + 1}" ${d.status === 'ready' ? '' : 'disabled'}><svg viewBox="0 0 64 64">${DISH[d.id] || DISH.pie}</svg>${d.status === 'ready' ? `<em>${C.serve}</em>` : ''}</button>
    <small><b>${esc(d.label)}</b>${d.status === 'served' ? C.served : d.status === 'ready' ? C.ready : `Unlocks at ${d.need} min`}</small></div>`).join('');
  const line = ev.final === 'done' ? C.done : ev.final === 'ready' ? C.all : `You've played ${ev.minutes} minutes today. ${done} of ${n} ${C.unit}.`;
  main.innerHTML = `<div class="scene sc-${ev.id}"><i class="cloth"></i><i class="candle l"></i><i class="candle r"></i><div class="plates">${plates}</div></div>
    <div class="progress"><div class="row"><p>${line}</p><button class="grace ${ev.final}" ${ev.final === 'ready' ? '' : 'disabled'}>${ev.final === 'done' ? C.btnDone : C.btn}</button></div>
    <div class="bar"><i style="width:${done / n * 100}%"></i></div></div>`;
  ambient({ amb: { cls: 'leaf', n: 14, colors: ['#e8762c', '#c4452a', '#f0b23c', '#a4531f'] } }, $('.scene'));
}

/* Labor Day: a paper time card. Each shift unlocks with playtime and gets punched; payday is the finale. */
const STAMP_TIMES = ['08:58', '10:30', '12:02', '13:15', '17:45', '18:31'];
function renderTimecard(ev) {
  const n = ev.dishes.length, done = ev.dishes.filter(d => d.status === 'served').length;
  setStats([{ icon: 'clock', label: 'Played today', value: ev.minutes, sub: 'min', hot: true }, { icon: 'hardhat', label: 'Shifts punched', value: done, sub: `/ ${n}` }]);
  const rows = ev.dishes.map((d, i) => `<li class="s-${d.status}"><span class="sh">${esc(d.label)}</span><span class="nd">${d.need} min</span>
    ${d.status === 'served' ? `<span class="stamp" style="--r:${(i % 3 - 1) * 4}deg">${STAMP_TIMES[i % 6]}</span>`
      : d.status === 'ready' ? `<button class="punch ready" data-i="${i + 1}">Punch</button>` : `<span class="lock">Unlocks at ${d.need} min</span>`}</li>`).join('');
  const line = ev.final === 'done' ? 'Paid in full. Enjoy the long weekend.' : ev.final === 'ready' ? 'Every shift is punched. Collect your holiday pay.'
    : `You've played ${ev.minutes} minutes today. ${done} of ${n} shifts punched.`;
  main.innerHTML = `<div class="scene sc-${ev.id}"><div class="timecard"><header><b>Time card</b><span>Los Santos Works · Labor Day</span></header><ul>${rows}</ul></div></div>
    <div class="progress"><div class="row"><p>${line}</p><button class="grace ${ev.final}" ${ev.final === 'ready' ? '' : 'disabled'}>${ev.final === 'done' ? 'Paid' : 'Collect payday'}</button></div>
    <div class="bar"><i style="width:${done / n * 100}%"></i></div></div>`;
}

Object.assign(EXPERIENCES, { spots: renderSpots, feast: renderFeast, countdown: renderCountdown, tribute: renderTribute });

const FXK = { trick: 'scare', empty: 'none', dud: 'none' };
function fx(res, x, y) {
  const k = FXK[res.kind] || 'win', scene = $('.scene'), rig = $('.rig'), id = state.event.id;
  const pts = state.event.contest && res.points ? res.points : 0;
  if (k === 'scare') {
    rig.classList.add('scare'); rig.insertAdjacentHTML('beforeend', '<div class="boo">BOO!</div>');
    setTimeout(() => { rig.classList.remove('scare'); rig.querySelector('.boo')?.remove(); }, 950);
    return say((res.msg || 'Something jumped out.') + (pts ? ` +${pts} pts` : ''));
  }
  if (k === 'none') return say((res.msg || res.label) + (pts ? ` +${pts} pts` : ''));
  const b = getComputedStyle(document.documentElement).getPropertyValue('--b').trim(), fw = ['#ff6b6b', '#5b8cff', '#ffffff', '#ffd36b'];
  const n = id === 'independence' ? 28 : 14;
  scene.insertAdjacentHTML('beforeend', Array.from({ length: n }, (_, i) => `<i class="fw" style="left:${x}px;top:${y}px;--c:${id === 'independence' ? fw[i % 4] : b};--r:${i * 360 / n}deg;--d:${-(60 + (i % 3) * (id === 'independence' ? 45 : 30))}px"></i>`).join(''));
  if (res.kind === 'ghost') scene.insertAdjacentHTML('beforeend', `<span class="ghost pop" style="left:${x}px;top:${y}px">${GHOST}</span>`);
  reveal({ head: res.kind === 'ghost' ? 'Ghost trapped' : 'You found something', label: res.label, sub: res.msg, kind: res.kind, points: pts });
}

/* One play: el is the thing that was used (spot, plate, candle, prize button or a trapped ghost) */
async function act(el, arg) {
  const ev = state && state.event; if (!ev || busy) return;
  const sr = $('.scene').getBoundingClientRect(), r = el.getBoundingClientRect();
  const x = r.left + r.width / 2 - sr.left, y = r.top + r.height / 2 - sr.top;
  busy = true; say(''); if (arg === 9) el.remove();
  const res = await post('play', { event: ev.id, arg }); busy = false;
  if (!res.ok) return say(res.msg, true);
  if (ev.kind === 'feast') {
    if (arg === 7) ev.final = 'done';
    else { ev.dishes[arg - 1].status = 'served'; if (ev.dishes.every(d => d.status === 'served') && ev.final === 'locked') ev.final = 'ready'; }
    renderFeast(ev);
    const C = ev.style === 'timecard' ? { head: 'Punched in', finaleHead: 'Payday', kind: 'punch' } : FEAST_COPY[ev.style] || FEAST_COPY.table;
    return reveal({ head: arg === 7 ? C.finaleHead : C.head, label: res.label, sub: res.msg, kind: C.kind });
  }
  if (ev.kind === 'tribute') { ev.lit = true; ev.total++; renderTribute(ev); return reveal({ head: 'Remembered', label: res.label, sub: res.msg, kind: 'candle' }); }
  if (arg === 8) { ev.contest.prize.claimed = true; renderSpots(ev); return reveal({ head: 'Prize claimed', label: res.label, sub: res.msg, kind: 'prize' }); }
  if (res.contest && ev.contest) Object.assign(ev.contest, res.contest);
  if (arg === 9) ev.ghost = false; else { ev.used++; ev.opened.push({ n: arg, kind: res.kind, label: res.label }); }
  renderSpots(ev); fx(res, x, y);
}

main.addEventListener('click', (e) => {
  const s = e.target.closest('.spot:not([disabled])'), p = e.target.closest('.plate.ready, .punch.ready, .grace.ready'), c = e.target.closest('.candle-btn:not([disabled])');
  const el = s || p || c; if (!el) return;
  act(el, s ? +s.dataset.n : c ? 1 : p.dataset.arg ? +p.dataset.arg : p.dataset.i ? +p.dataset.i : 7);
});

/* ---------- New Year's Eve: ball-drop countdown (display only; the ball falls through the last hour) ---------- */
const clockText = (s) => [Math.floor(s / 3600), Math.floor(s % 3600 / 60), s % 60].map(n => String(n).padStart(2, '0')).join(':');

function burst(scene, x, y, cols, n = 24, dist = 90) {
  scene.insertAdjacentHTML('beforeend', Array.from({ length: n }, (_, i) =>
    `<i class="fw" style="left:${x}px;top:${y}px;--c:${cols[i % cols.length]};--r:${i * 360 / n}deg;--d:${-(dist * (.6 + (i % 3) * .25))}px"></i>`).join(''));
}

function renderCountdown(ev) {
  syncSkinBtn(null); stopAmbient();
  setStats([{ icon: 'clock', label: 'Countdown', value: ev.secondsLeft > 0 ? 'Tonight' : 'Midnight', hot: true }, { icon: 'users', label: 'Celebrate with', value: 'The city' }]);
  main.innerHTML = `<div class="scene sc-${ev.id}"><i class="ball"></i><div class="clock"><small></small><b></b></div></div><div class="progress"><p></p><div class="bar"><i></i></div></div>`;
  const scene = $('.scene'), ball = $('.ball'), digits = $('.clock b'), label = $('.clock small'), line = $('.progress p'), bar = $('.bar i');
  ambient({ amb: { cls: 'confetti', n: 28, colors: ['#f5c542', '#ffd86b', '#e8ecff', '#ff9ac1', '#8fd8ff'] } }, scene);
  const t0 = Date.now(); let fired = false;
  (function tick() {
    const left = Math.max(0, ev.secondsLeft - Math.floor((Date.now() - t0) / 1000)), p = Math.min(1, Math.max(0, 1 - left / 3600));
    digits.textContent = left > 0 ? clockText(left) : 'Happy New Year!';
    label.textContent = left > 0 ? 'Midnight in' : '';
    ball.style.top = `${12 + p * 52}%`; bar.style.width = `${p * 100}%`;
    line.textContent = left <= 0 ? 'It is midnight. Make it a good one.' : left <= 3600 ? 'The ball is dropping. Grab someone and count it down.' : 'Stay close. The ball starts to fall in the last hour.';
    if (left > 0) timers.push(setTimeout(tick, 250));
    else if (!fired) {
      fired = true; const r = scene.getBoundingClientRect();
      for (let i = 0; i < 7; i++) later(() => burst(scene, rnd(.15, .85) * r.width, rnd(.12, .5) * r.height, ['#f5c542', '#ffffff', '#8fd8ff', '#ff9ac1'], 30, 120), i * 350, i * 350 + 600);
    }
  })();
}

/* ---------- Memorial Day: the candle vigil ---------- */
const CANDLE = (lit) => `<svg viewBox="0 0 40 96"><defs><radialGradient id="cg"><stop offset="0" stop-color="#ffd27a" stop-opacity=".9"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></radialGradient></defs>${lit
  ? '<circle cx="20" cy="20" r="22" fill="url(#cg)"/><path d="M20 4c8 10 8 18 0 24-8-6-8-14 0-24z" fill="#ffb347"/><path d="M20 13c4 5 4 10 0 14-4-4-4-9 0-14z" fill="#fff6c0"/>' : ''
  }<path d="M20 34v-6" stroke="#444" stroke-width="2"/><rect x="11" y="34" width="18" height="56" rx="3" fill="#f4ead2" stroke="#c9b98f" stroke-width="1.5"/><ellipse cx="20" cy="90" rx="14" ry="4" fill="#8a7a5a"/></svg>`;

function renderTribute(ev) {
  syncSkinBtn(null); stopAmbient();
  setStats([{ icon: 'flame', label: 'Candles lit', value: ev.total.toLocaleString(), hot: true }, { icon: 'check', label: 'Your candle', value: ev.lit ? 'Lit' : 'Not yet' }]);
  const others = Math.min(Math.max(ev.total - (ev.lit ? 1 : 0), 0), 10), side = (n) => Array.from({ length: n }, () => CANDLE(true)).join('');
  main.innerHTML = `<div class="scene sc-${ev.id}"><div class="vigil l">${side(Math.ceil(others / 2))}</div>
    <button class="candle-btn ${ev.lit ? 'lit' : ''}" ${ev.lit ? 'disabled' : ''}>${CANDLE(ev.lit)}<small>${ev.lit ? 'Your candle is lit' : 'Light a candle'}</small></button>
    <div class="vigil r">${side(Math.floor(others / 2))}</div></div>
    <div class="progress"><p>${esc(ev.text)} <b>${ev.total.toLocaleString()}</b> ${ev.total === 1 ? 'candle is' : 'candles are'} lit across the city.</p></div>`;
}
