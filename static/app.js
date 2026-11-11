'use strict';

const $ = id => document.getElementById(id);
const filters = ['search', 'category', 'status'];
const state = { notices: [], selected: null };
const money = new Intl.NumberFormat('en-CA', {
  style: 'currency', currency: 'CAD', maximumFractionDigits: 0,
});

function element(tag, text = '', className = '') {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

async function api(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error('Local demo API unavailable');
  return response.json();
}

function setMessage(message) {
  const row = element('tr');
  const cell = element('td', message);
  cell.colSpan = 4;
  row.append(cell);
  $('rows').replaceChildren(row);
}

async function load() {
  $('load-error').hidden = true;
  $('result-count').textContent = 'Loading';
  setMessage('Loading fictional records…');
  try {
    const [summary, result] = await Promise.all([api('/api/summary'), api('/api/notices')]);
    state.notices = result.items;
    $('snapshot').textContent = 'Snapshot ' + summary.as_of;
    $('total').textContent = summary.total;
    $('open').textContent = summary.open;
    $('soon').textContent = summary.deadline_14d;
    $('conflicts').textContent = summary.conflicts;
    const max = Math.max(1, ...Object.values(summary.categories));
    for (const [name, count] of Object.entries(summary.categories)) {
      const item = element('div', '', 'barline');
      const top = element('div', '', 'bar-top');
      top.append(element('span', name), element('strong', String(count)));
      const bar = element('progress');
      bar.max = max;
      bar.value = count;
      bar.setAttribute('aria-hidden', 'true');
      item.append(top, bar);
      $('category-bars').append(item);
      $('category').append(new Option(name, name));
    }
    for (const id of [...filters, 'reset']) $(id).disabled = false;
    render();
  } catch {
    $('result-count').textContent = 'Unavailable';
    setMessage('Fictional records unavailable.');
    $('load-error').hidden = false;
  }
}

function render() {
  const q = $('search').value.trim().toLowerCase();
  const category = $('category').value;
  const status = $('status').value;
  const matches = state.notices.filter(n =>
    (!category || category === n.category) && (!status || status === n.status) &&
    [n.title, n.buyer, n.id, n.summary].some(value => value.toLowerCase().includes(q))
  );
  if (!matches.some(n => n.id === state.selected)) showDetails(null);
  $('result-count').textContent = matches.length + (matches.length === 1 ? ' notice' : ' notices');
  $('rows').replaceChildren();
  if (!matches.length) setMessage('No fictional notices match. Reset filters to see all records.');

  for (const notice of matches) {
    const row = element('tr');
    const title = element('button', notice.title, 'record-title');
    title.id = notice.id;
    title.type = 'button';
    title.setAttribute('aria-controls', 'detail-body');
    title.setAttribute('aria-expanded', String(notice.id === state.selected));
    title.addEventListener('click', () => {
      showDetails(notice);
      $('detail-title').focus();
    });
    const first = element('td');
    first.append(title, element('span', notice.buyer + ' · ' + notice.id, 'record-buyer'));
    const statusCell = element('td');
    statusCell.append(element('span', notice.status, 'tag ' + notice.status.toLowerCase()));
    row.append(first, element('td', notice.category), element('td', notice.deadline ?? 'Disputed'), statusCell);
    $('rows').append(row);
  }
}

function showDetails(notice) {
  if (state.selected) $(state.selected)?.setAttribute('aria-expanded', 'false');
  state.selected = notice?.id ?? null;
  $('back-to-record').hidden = !notice;
  const body = $('detail-body');
  body.className = notice ? 'inspector' : 'detail-empty';
  body.replaceChildren();
  if (!notice) {
    body.textContent = 'Select an opportunity from the register to view its details.';
    return;
  }

  $(notice.id).setAttribute('aria-expanded', 'true');
  body.append(element('h3', notice.title));
  const fields = [
    ['Notice', notice.id], ['Buyer', notice.buyer], ['Region', notice.region],
    ['Indicative budget', money.format(notice.budget_cad)], ['Eligibility', notice.eligibility],
  ];
  for (const [label, value] of fields) {
    const line = element('div', '', 'line');
    line.append(element('span', label), element('strong', value));
    body.append(line);
  }
  if (notice.deadline_evidence.length) {
    body.append(element('h4', 'Disputed deadline', 'history-head'));
    body.append(element('p', 'Manual review required. This notice is excluded from deadline reporting.', 'flag'));
    const evidence = element('ul', '', 'evidence');
    for (const source of notice.deadline_evidence) {
      const item = element('li');
      item.append(element('strong', source.deadline), element('span', source.source + ' · observed ' + source.observed));
      evidence.append(item);
    }
    body.append(evidence);
  }
  body.append(element('h4', 'Observation history', 'history-head'));
  for (const history of notice.history.slice().reverse()) {
    const event = element('div', '', 'event');
    event.append(element('strong', history.event), element('small', history.date), element('p', history.detail));
    body.append(event);
  }
}

for (const id of filters) {
  $(id).disabled = true;
  $(id).addEventListener('input', render);
}
$('reset').disabled = true;
$('reset').addEventListener('click', () => {
  for (const id of filters) $(id).value = '';
  showDetails(null);
  render();
  $('search').focus();
});
$('retry').addEventListener('click', async () => {
  await load();
  if ($('load-error').hidden) $('search').focus();
  else $('retry').focus();
});
$('back-to-record').addEventListener('click', () => $(state.selected)?.focus());
load();
