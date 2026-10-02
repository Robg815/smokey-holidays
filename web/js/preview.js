'use strict';
/* Browser preview and mock server. Skipped entirely in-game (GetParentResourceName exists there).
   index.html?holiday=<id>   halloween | valentines | easter | stpatricks | independence | thanksgiving | new_years_eve | new_years | memorial | veterans
   &force=trick              make the next pick a jump scare      &closed   Halloween contest after it closes (podium + prize)      &art / &skin=holo   advent options      ?admin   admin panel */
const PV = new URLSearchParams(location.search);

const ADM = {
  year: 2026, date: '2026-09-30', real: '2026-09-30', override: false, clock: null, advent: true, msg: '', ghosts: 2, ghostMax: 10,
  holidays: [['new_years', "New Year's Day", 'spots'], ['mlk', 'Martin Luther King Jr. Day', 'observance'], ['valentines', "Valentine's Day", 'spots'], ['presidents', "Presidents' Day", 'observance'],
    ['stpatricks', "St. Patrick's Day", 'spots'], ['easter', 'Easter', 'spots'], ['mothers_day', "Mother's Day", 'observance'], ['memorial', 'Memorial Day', 'tribute'], ['juneteenth', 'Juneteenth', 'observance'],
    ['fathers_day', "Father's Day", 'observance'], ['independence', 'Independence Day', 'spots'], ['labor', 'Labor Day', 'observance'], ['columbus', "Columbus / Indigenous Peoples' Day", 'observance'],
    ['halloween', 'Halloween', 'spots'], ['veterans', 'Veterans Day', 'tribute'], ['thanksgiving', 'Thanksgiving', 'feast'], ['christmas', 'Christmas', 'advent'], ['new_years_eve', "New Year's Eve", 'countdown'],
  ].map(([id, label, kind]) => ({ id, label, kind, natural: false, enabled: true, forced: false })),
};
function mockAdmin(d) {
  const h = ADM.holidays.find(x => x.id === d.id), a = d.action;
  if (a === 'toggle') { h.enabled = d.enabled; if (!d.enabled) h.forced = false; ADM.msg = d.enabled ? 'Holiday enabled.' : 'Holiday disabled.'; }
  else if (a === 'force') { h.forced = d.on; ADM.msg = d.on ? 'Forced on until restart.' : 'No longer forced.'; }
  else if (a === 'date') { ADM.override = !!d.value; ADM.date = d.value || ADM.real; ADM.msg = d.value ? 'Date override set.' : 'Using the real date.'; }
  else if (a === 'clock') { ADM.clock = d.value || null; ADM.msg = d.value ? 'Fake clock running.' : 'Using real time.'; }
  else if (a === 'resetClaims') ADM.msg = 'Removed 0 of your claims.';
  else if (a === 'playtime') ADM.msg = 'Added 30 minutes of playtime for today.';
  else if (a === 'spawnGhost') { ADM.ghosts++; ADM.msg = 'A ghost is on its way. Look around you.'; }
  else if (a === 'clearGhosts') { ADM.msg = `Cleared ${ADM.ghosts} ghosts.`; ADM.ghosts = 0; }
  else if (a === 'addPoints') ADM.msg = 'Added 100 Halloween points to you.';
  else if (a === 'resetContest') ADM.msg = 'Halloween contest reset (12 scores removed).';
  else if (a === 'advent') { ADM.advent = d.enabled; ADM.msg = `Advent calendar ${d.enabled ? 'enabled' : 'disabled'}.`; }
  return JSON.parse(JSON.stringify(ADM));
}

function mock(name, data) {
  if (name === 'claim') {
    const d = state.advent.doors[data.day - 1]; d.status = 'claimed'; d.label = 'Snack pack'; render(state);
    return Promise.resolve({ ok: true, day: data.day, label: 'Snack pack' });
  }
  if (name === 'play') {
    const ev = state.event;
    if (ev.kind === 'feast') return Promise.resolve({ ok: true, label: data.arg === 7 ? 'Give thanks' : ev.dishes[data.arg - 1].label, msg: 'Golden brown.' });
    if (ev.kind === 'tribute') return Promise.resolve({ ok: true, label: 'A candle burns for them', msg: 'Thank you for remembering.' });
    if (data.arg === 8) return Promise.resolve({ ok: true, kind: 'prize', label: 'Halloween Champion', msg: 'You ruled the night. Congratulations!' });
    const m = SCENES[ev.id].mock, o = data.arg === 9 ? ['ghost', 'Caught a ghost', 'It squeaked, then vanished.'] : m.find(x => x[0] === PV.get('force')) || pick(m);
    const res = { ok: true, kind: o[0], label: o[1], msg: o[2], spot: data.arg };
    if (ev.contest) { // mirror the server: points go on the board and come back with the result
      res.points = { treat: 10, trick: 5, ghost: data.arg === 9 ? 20 : 25, empty: 1 }[o[0]] || 0;
      const points = ev.contest.points + res.points, board = ev.contest.board.map(r => r.you ? { ...r, points } : r);
      if (!board.some(r => r.you)) board.push({ rank: 0, name: 'Jordan K.', points, you: true });
      board.sort((a, b) => b.points - a.points).forEach((r, i) => { r.rank = i + 1; });
      res.contest = { board, points, rank: board.find(r => r.you).rank };
    }
    return Promise.resolve(res);
  }
  if (name === 'adminDo') return Promise.resolve(mockAdmin(data));
  return Promise.resolve({});
}

if (!inGame) {
  const id = PV.get('holiday') || 'christmas';
  const T = { christmas: ['#ff5a6e', '#6dffb0'], halloween: ['#ff8a1f', '#b06cff'], valentines: ['#ff6fb5', '#ffc2e0'], easter: ['#c79bff', '#8affc7'], stpatricks: ['#4dff8a', '#e6ff7a'],
    independence: ['#5b8cff', '#ff6b6b'], thanksgiving: ['#ffb347', '#ff7a45'], new_years_eve: ['#8fd8ff', '#ffffff'], new_years: ['#8fd8ff', '#ffffff'], memorial: ['#7fa8ff', '#ff7a7a'], veterans: ['#7fa8ff', '#ff7a7a'] };
  const L = { christmas: 'Christmas', halloween: 'Halloween', valentines: "Valentine's Day", easter: 'Easter', stpatricks: "St. Patrick's Day", independence: 'Independence Day', thanksgiving: 'Thanksgiving',
    new_years_eve: "New Year's Eve", new_years: "New Year's Day", memorial: 'Memorial Day', veterans: 'Veterans Day' };
  const B = { christmas: 'Snow on the pier, lights on every block.', halloween: 'The city is not as empty as it looks after dark.', valentines: 'Flowers, dinners and questionable decisions.', easter: 'Egg hunts across the city.',
    stpatricks: 'Green everything. Pubs will be busy.', independence: 'Fireworks over the pier tonight.', thanksgiving: 'Turkey, family and a lot of traffic.', new_years_eve: 'Countdown at midnight.',
    new_years: 'A fresh year on the streets of Los Santos.', memorial: 'Remembering those who served.', veterans: 'Honoring all who served.' };
  const th = { a: T[id][0], b: T[id][1] };
  const BOARD = (me) => [['Marcus T.', 240], ['Priya S.', 198], ['Dee W.', 171], ['Sam O.', 150], ['Lena V.', 132], ['Rico M.', 101], ['Jordan K.', me]]
    .sort((a, b) => b[1] - a[1]).map(([name, points], i) => ({ rank: i + 1, name, points, you: name === 'Jordan K.' }));
  const PVE = {
    halloween: PV.has('closed')
      ? { kind: 'spots', spots: 5, picks: 5, used: 5, opened: [], ghost: false, world: { today: 0, cap: 8 },
          contest: { open: false, secondsLeft: 0, points: 265, rank: 1, hint: 'Treats +10, ghost loot +25, catch ghosts around the city +30.', board: BOARD(265),
            winners: [{ place: 1, name: 'Jordan K.', points: 265, you: true }, { place: 2, name: 'Marcus T.', points: 240, you: false }, { place: 3, name: 'Priya S.', points: 198, you: false }],
            prize: { place: 1, label: 'Halloween Champion', claimed: false } } }
      : { kind: 'spots', spots: 5, picks: 5, used: 2, opened: [{ n: 2, kind: 'treat', label: 'Candy haul' }, { n: 4, kind: 'empty', label: 'Nobody home' }], ghost: true, world: { today: 2, cap: 8 },
          contest: { open: true, secondsLeft: 1047600, points: 85, rank: 7, hint: 'Treats +10, ghost loot +25, catch ghosts around the city +30.', board: BOARD(85) } },
    valentines: { kind: 'spots', spots: 6, picks: 1, used: 0, opened: [] },
    easter: { kind: 'spots', spots: 8, picks: 3, used: 1, opened: [{ n: 3, kind: 'golden', label: 'Golden egg' }] },
    stpatricks: { kind: 'spots', spots: 5, picks: 2, used: 1, opened: [{ n: 2, kind: 'coins', label: 'Gold coins' }] },
    independence: { kind: 'spots', spots: 6, picks: 4, used: 2, opened: [{ n: 1, kind: 'burst', label: 'Big burst' }, { n: 5, kind: 'dud', label: 'Fizzled' }] },
    new_years: { kind: 'spots', spots: 3, picks: 1, used: 0, opened: [] },
    new_years_eve: { kind: 'countdown', secondsLeft: 754 },
    memorial: { kind: 'tribute', lit: false, total: 1204, text: 'Light a candle for those who gave everything.' },
    veterans: { kind: 'tribute', lit: true, total: 386, text: 'Light a candle for everyone who served.' },
    thanksgiving: { kind: 'feast', minutes: 18, final: 'locked', dishes: [['turkey', 'Roast turkey', 5, 'served'], ['stuffing', 'Stuffing', 10, 'served'], ['pie', 'Pumpkin pie', 15, 'served'],
      ['corn', 'Sweet corn', 20, 'ready'], ['rolls', 'Dinner rolls', 25, 'waiting'], ['cranberry', 'Cranberry sauce', 30, 'waiting']].map(([i, label, need, status]) => ({ id: i, label, need, status })) },
  };
  const s = {
    date: '2026-12-12', theme: th,
    active: [{ id, label: L[id], blurb: B[id], daysUntil: 0, date: '2026-12-12', theme: th }],
    upcoming: [{ label: "New Year's Eve", daysUntil: 19, date: '2026-12-31' }, { label: "New Year's Day", daysUntil: 20, date: '2027-01-01' }, { label: 'Martin Luther King Jr. Day', daysUntil: 41, date: '2027-01-18' }],
  };
  if (id === 'christmas') {
    s.advent = { skin: PV.get('skin') || 'wood', current: 12, days: 24, minutes: 12, doors: Array.from({ length: 24 }, (_, i) => {
      const day = i + 1, status = day < 4 ? 'claimed' : day < 12 ? 'waiting' : day === 12 ? 'ready' : 'locked';
      return { day, status, need: 30, image: PV.has('art') && [1, 4, 5, 7, 8, 11, 12, 13, 16, 19, 22].includes(day) ? `img/door${day}.svg` : undefined, label: status === 'claimed' ? 'Snack pack' : undefined };
    }) };
  } else s.event = { id, ...PVE[id] };

  if (PV.has('admin')) {
    Object.assign(ADM.holidays.find(h => h.id === 'halloween'), { forced: true });
    Object.assign(ADM.holidays.find(h => h.id === 'mlk'), { enabled: false });
    ADM.msg = 'Holiday enabled.'; showAdmin(JSON.parse(JSON.stringify(ADM)));
  } else show(s);
}
