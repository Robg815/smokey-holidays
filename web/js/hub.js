'use strict';
/* City hub: what is happening around Los Santos today, your progress, and a waypoint to the nearest spot.
   The activities themselves happen in the world (client/world.lua); this only reports on them. */
const TYPE_LABEL = { spots: 'Around the city', delivery: 'Delivery job', gathering: 'Live event', ghosts: 'Night hunt', advent: 'Daily calendar' };

function dur(s) {
  s = Math.max(0, Math.floor(s));
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return h ? `${h}h ${m}m` : m ? `${m}m ${String(x).padStart(2, '0')}s` : `${x}s`;
}
const cd = (secs, suffix = '') => `<b class="cd" data-end="${Date.now() + secs * 1000}" data-suffix="${suffix}">${dur(secs)}${suffix}</b>`;

const banner = (art, i, ic) => `<div class="banner" style="background-image:url(${art});background-position:${[15, 85, 50, 30, 70][i % 5]}% ${[70, 40, 55, 30, 85][i % 5]}%"><span class="ai">${icon(ic)}</span></div>`;

function actCard(a, i, art) {
  const full = a.today >= a.cap;
  let status = 'Open now', cls = 'open', when = '';
  if (a.type === 'gathering') {
    if (a.today >= 1) { status = 'You were there'; cls = 'done'; }
    else if (a.startsIn > 0) { status = `Today at ${a.at}`; cls = 'soon'; when = `<div class="when-row">${icon('clock')}<span>Starts in</span>${cd(a.startsIn)}</div>`; }
    else if (a.startsIn > -60) { status = 'Happening now'; cls = 'live'; }
    else { status = 'Missed today'; cls = 'off'; }
  } else if (a.type === 'delivery' && a.job) {
    status = 'Carrying'; cls = 'live'; when = `<div class="when-row">${icon('clock')}<span>Deliver within</span>${cd(a.job.left)}</div>`;
  } else if (full) { status = 'Done for today'; cls = 'done'; }
  const how = a.type === 'spots' ? `${a.total} spots on the map` : a.type === 'delivery' ? `Deliver within ${Math.round((a.timeLimit || 600) / 60)} min` : 'Stand inside the circle on your map';
  const meter = a.type === 'gathering' ? '' : `<div class="ap"><div class="bar"><i style="width:${Math.min(100, a.today / a.cap * 100)}%"></i></div><span>${a.today}/${a.cap} today</span></div>`;
  const off = (full && a.type !== 'gathering') || cls === 'off';
  return `<article class="act s-${cls}" data-type="${esc(a.type)}">${banner(art, i, a.icon)}
    <header><div class="at"><b>${esc(a.title)}</b><small>${TYPE_LABEL[a.type] || ''}</small></div><span class="st">${esc(status)}</span></header>
    <p>${esc(a.desc)}</p>${when}${meter}
    <footer><span class="how">${icon(a.type === 'gathering' ? 'users' : a.type === 'delivery' ? 'box' : 'pin')}${how}</span>
      <button class="wp" data-key="${esc(a.key)}" ${off ? 'disabled' : ''}>${icon('pin')}Set waypoint</button></footer></article>`;
}

function ghostCard(g, i, art) {
  const full = g.today >= g.cap;
  return `<article class="act s-${full ? 'done' : 'open'}" data-type="ghosts">${banner(art, i, 'ghost')}
    <header><div class="at"><b>Ghost hunt</b><small>${TYPE_LABEL.ghosts}</small></div><span class="st">${full ? 'Done for today' : 'After dark'}</span></header>
    <p>${g.flashlight === false ? 'Ghosts drift in near you at night. Walk up to one and catch it.' : 'Ghosts drift in near you at night. Equip a flashlight, aim it at the ghost and hold the beam on it until it is trapped.'}</p>
    <div class="ap"><div class="bar"><i style="width:${Math.min(100, g.today / g.cap * 100)}%"></i></div><span>${g.today}/${g.cap} today</span></div>
    <footer><span class="how">${icon('flashlight')}${g.flashlight === false ? 'They come to you' : 'Flashlight required'}</span><button class="wp" disabled>${icon('ghost')}They find you</button></footer></article>`;
}

function adventCard(adv, i, art) {
  const t = adv.doors[adv.current - 1], opened = adv.doors.filter(d => d.status === 'claimed').length;
  const st = !t ? 'Closed' : t.status === 'claimed' ? 'Opened today' : t.status === 'ready' ? 'Door ready' : `${adv.minutes}/${t.need} min`;
  return `<article class="act s-${t && t.status === 'ready' ? 'live' : t && t.status === 'claimed' ? 'done' : 'open'}" data-type="advent">${banner(art, i, 'gift')}
    <header><div class="at"><b>Advent calendar</b><small>${TYPE_LABEL.advent}</small></div><span class="st">${esc(st)}</span></header>
    <p>Play each day to unlock that day's drawer. Door ${adv.current} is today's.</p>
    <div class="ap"><div class="bar"><i style="width:${opened / adv.days * 100}%"></i></div><span>${opened}/${adv.days} opened</span></div>
    <footer><span class="how">${icon('calendar')}One drawer a day</span><button class="wp" data-view="advent">${icon('gift')}Open calendar</button></footer></article>`;
}

function hubTick() { // countdowns on gathering and delivery cards (cancelled with every other timer when the UI hides)
  const els = main.querySelectorAll('.cd[data-end]'); if (!els.length) return;
  els.forEach(el => { el.textContent = dur((+el.dataset.end - Date.now()) / 1000) + (el.dataset.suffix || ''); });
  timers.push(setTimeout(hubTick, 1000));
}

function renderHub(s, h) {
  syncSkinBtn(null);
  const acts = (s.world && s.world[h.id]) || [], c = s.contest && s.contest[h.id];
  if (c) {
    renderBoard(c.board);
    if (!c.board.open) { s.event = { id: h.id, kind: 'spots', contest: c.board }; return renderResults(s.event); }
  }
  const advent = s.advent && h.id === 'christmas';
  if (!acts.length && !advent) return renderEmpty(s);

  const done = acts.reduce((n, a) => n + Math.min(a.today, a.cap), 0), cap = acts.reduce((n, a) => n + a.cap, 0);
  const next = acts.find(a => a.type === 'gathering' && a.today < 1 && a.startsIn > 0);
  setStats([
    c ? { icon: 'trophy', label: 'Contest score', value: ptsText(c.board.points), hot: true } : null,
    c ? { icon: 'rank', label: 'Leaderboard', value: c.board.rank ? `#${c.board.rank}` : 'Unranked' } : null,
    { icon: 'check', label: 'Done today', value: done, sub: `/ ${cap}`, hot: !c },
    next ? { icon: 'clock', label: next.title, value: `At ${next.at}` } : { icon: 'pin', label: 'Live in the city', value: acts.length + (c && c.ghosts ? 1 : 0) },
  ].filter(Boolean).slice(0, 4));

  const art = heroSrc(h.id), cards = acts.map((a, i) => actCard(a, i, art)).join('') + (c && c.ghosts ? ghostCard(c.ghosts, acts.length, art) : '') + (advent ? adventCard(s.advent, acts.length, art) : '');
  main.innerHTML = `<div class="hub"><div class="hub-bg" style="background-image:url(${heroSrc(h.id)})"></div>
    <div class="hub-head"><div><h3>In the city today</h3><p>Everything happens out in Los Santos. Progress resets every day. Use Set waypoint to head to the nearest spot.</p></div>
      <span class="live-pill"><i class="live"></i>${acts.length + (c && c.ghosts ? 1 : 0)} activities live</span></div>
    <div class="act-grid">${cards}</div></div>`;
  hubTick();
}

main.addEventListener('click', async (e) => {
  const v = e.target.closest('[data-view]');
  if (v && state) { state.view = v.dataset.view; return render(state); }
  const b = e.target.closest('.wp[data-key]:not([disabled])'); if (!b || !state) return;
  const h = current(state);
  const res = await post('waypoint', { holiday: h.id, key: b.dataset.key });
  say(res.msg || (res.ok ? 'Waypoint set.' : 'Could not set a waypoint.'), !res.ok);
});

$('#back').addEventListener('click', () => { if (state) { state.view = 'hub'; render(state); } });
const syncBack = (on) => { $('#back').hidden = !on; };
