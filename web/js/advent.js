'use strict';
/* Advent calendar (Christmas): drawer layout, icons, skins, claim flow. */
const DEFAULT_ICONS = ['poinsettia','snowflake','snowflake','bell','gift','star','hat','ornament','snowflake','star','bell','deer','holly','star','snowflake','snowman','star','tree','candycane','star','ho','wreath','snowflake','tree'];
const DEFAULT_LAYOUT = [
  [[1,4.6],[2,2.4],[3,2.4],[4,4.4]],
  [[5,2.4],[6,2.4],[7,4.4,'flip'],[8,4.3]],
  [[9,2.3],[10,1.6],[11,2.4,'flip'],[12,4.4,'flip'],[13,2.4]],
  [[14,1.6],[15,1.6],[16,4.4,'flip'],[17,1.8],[18,1.6],[19,2.5,'flip']],
  [[20,1.6],[21,4.4],[22,4.4,'flip'],[23,1.7],[24,1.7]],
];
const ICONS = {
  snowflake: '<path d="M24 5v38M7.5 14.5l33 19M7.5 33.5l33-19M18 8l6 5 6-5M18 40l6-5 6 5"/>',
  star: '<path d="M24 5l5.5 12 13 1.5-9.7 8.8 2.7 12.9L24 33.5 12.5 40.2l2.7-12.9L5.5 18.5l13-1.5z"/>',
  bell: '<path d="M24 8c-7 0-11 5-11 12v8l-4 5h30l-4-5v-8c0-7-4-12-11-12zM20 37a4 4 0 008 0M24 5v3"/>',
  gift: '<path d="M8 20h32v6H8zM10 26h28v15H10zM24 20v21M24 20c-4-1-9-3-9-7s6-4 9 3c3-7 9-7 9-3s-5 6-9 7z"/>',
  holly: '<path d="M24 26c-3-8-11-10-16-8 1 6 8 12 16 8zM24 26c3-8 11-10 16-8-1 6-8 12-16 8z"/><circle cx="21" cy="31" r="2.6"/><circle cx="27" cy="31" r="2.6"/><circle cx="24" cy="36" r="2.6"/>',
  candycane: '<path d="M18 43V17a8 8 0 0116 0"/><path d="M14.5 39l7-3M14.5 31l7-3M14.5 23l7-3M27 9.5l5.5 3"/>',
  wreath: '<circle cx="24" cy="23" r="14"/><circle cx="24" cy="23" r="8"/><circle cx="24" cy="9" r="2"/><circle cx="38" cy="23" r="2"/><circle cx="10" cy="23" r="2"/><path d="M19 38l5 6 5-6"/>',
  tree: '<path d="M24 5l-9 13h5l-8 12h6l-9 12h30l-9-12h6l-8-12h5zM24 42v3"/>',
  snowman: '<circle cx="24" cy="34" r="9"/><circle cx="24" cy="18" r="6"/><path d="M19 11h10M21 11V6h6v5M24 20l3 1M24 31h.1M24 36h.1"/>',
  hat: '<path d="M9 36c0-13 6-24 18-26 4 0 6 3 4 6-6 2-8 8-8 20M7 36h30v6H7z"/><circle cx="35" cy="14" r="3"/>',
  ornament: '<circle cx="24" cy="29" r="12"/><path d="M20 17h8v-4h-8zM24 13V7M13 27c4 4 18 4 22 0"/>',
  deer: '<path d="M24 41c-5 0-8-4-8-9s3-9 8-9 8 4 8 9-3 9-8 9zM19 26l-5-9m0 0l-6 1m6-1V8m15 18l5-9m0 0l6 1m-6-1V8M24 34h.1"/>',
  poinsettia: '<path d="M24 24c-6-4-6-14 0-18 6 4 6 14 0 18zM24 24c4-6 14-6 18 0-4 6-14 6-18 0zM24 24c6 4 6 14 0 18-6-4-6-14 0-18zM24 24c-4 6-14 6-18 0 4-6 14-6 18 0z"/><circle cx="24" cy="24" r="3"/>',
  ho: '<text x="24" y="30" text-anchor="middle" font-size="17">Ho</text>',
};
let pending = null;

function door(d, w, a, f) {
  if (!d) return '';
  const today = d.day === a.current;
  const pct = d.status === 'waiting' ? Math.min(100, Math.round(a.minutes / d.need * 100)) : 0;
  const sub = { claimed: esc(d.label), ready: 'Open now', waiting: `${a.minutes}/${d.need} min`, missed: 'Missed', locked: 'Locked' }[d.status];
  const tip = { claimed: d.label, ready: 'Open this door', waiting: `${a.minutes} of ${d.need} minutes`, missed: 'Missed', locked: 'Not yet' }[d.status];
  const name = d.icon || DEFAULT_ICONS[d.day - 1];
  const art = d.image
    ? `<img class="art" src="${esc(d.image)}" alt="">`
    : `<svg class="ico i-${esc(name)}" viewBox="0 0 48 48" aria-hidden="true">${ICONS[name] || ICONS.star}</svg>`;
  const cls = [d.status, today ? 'today' : '', w >= 3 ? 'wide' : 'narrow', f === 'flip' ? 'flip' : '', pending === d.day ? 'pulled' : ''].join(' ');
  return `<button class="door ${cls}" data-day="${d.day}" title="${esc(tip)}" style="flex:${w} 1 0;--p:${pct}%" ${d.status === 'ready' ? '' : 'tabindex="-1"'}>
    <span class="n">${d.day}</span>${art}<span class="s">${sub}</span></button>`;
}

const SKIN_KEY = 's2-holidays:skin';
function skinNow(a) { let p = null; try { p = localStorage.getItem(SKIN_KEY); } catch (e) {} return p || (a && a.skin) || 'wood'; }
function syncSkinBtn(a) { const b = $('#skin'); b.hidden = !a; if (a) b.textContent = skinNow(a) === 'holo' ? 'Wood skin' : 'Holo skin'; }
$('#skin').addEventListener('click', () => {
  if (!state || !state.advent) return;
  try { localStorage.setItem(SKIN_KEY, skinNow(state.advent) === 'holo' ? 'wood' : 'holo'); } catch (e) {}
  renderAdvent(state.advent);
});

function renderAdvent(a) {
  syncSkinBtn(a);
  setStats([{ icon: 'gift', label: "Today's door", value: `Door ${a.current}`, hot: true }, { icon: 'clock', label: 'Played today', value: a.minutes, sub: 'min' },
    { icon: 'check', label: 'Doors opened', value: a.doors.filter(d => d.status === 'claimed').length, sub: `/ ${a.days}` }]);
  const by = Object.fromEntries(a.doors.map(d => [d.day, d]));
  const rows = (a.layout || DEFAULT_LAYOUT).map(r => `<div class="drow">${r.map(([day, w, f]) => door(by[day], w, a, f)).join('')}</div>`).join('');

  const t = by[a.current];
  const need = t ? t.need : 0;
  const line = !t ? '' : t.status === 'claimed' ? "You've opened today's door. Come back tomorrow."
    : t.status === 'ready' ? "Today's door is ready to open."
    : `You've played ${a.minutes} of ${need} minutes today. Today's door opens at ${need}.`;
  main.innerHTML = `<div class="drows skin-${skinNow(a)}">${rows}</div>
    <div class="progress"><p>${line}</p><div class="bar"><i style="width:${need ? Math.min(100, a.minutes / need * 100) : 0}%"></i></div></div>`;
}

main.addEventListener('click', async (e) => {
  const el = e.target.closest('.door.ready');
  if (!el || busy) return;
  busy = true; say(''); pending = Number(el.dataset.day);
  const res = await post('claim', { day: pending });
  busy = false; pending = null;
  if (res.ok) { say(`Door ${res.day} opened: ${res.label}`); reveal({ head: `Door ${res.day} opened`, label: res.label, kind: 'door' }); } else say(res.msg, true);
});
