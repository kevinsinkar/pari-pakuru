/**
 * The word-building page: Parks's tables 4 and 5, six example derivations, and a finder
 * for the words in which the dictionary prints the same piece.
 * Data: data/wordbuilding.json (web/learning.py, wordbuilding_data).
 */
(() => {
  const { esc, pieceChips, literalHtml, entryLink, load } = Skiri;
  const MAX_ROWS = 80;
  let data = null;
  let byKey = new Map();      // piece key -> indexes into data.entries
  let byId = new Map();

  function plainKey(text) {
    return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
      .replace(/[\s\-()]/g, '').replace(/ø/g, 'Ø');
  }

  function wordRow(entry, highlight) {
    return `<li class="family-item">
      <div class="family-head"><a class="family-word" lang="x-paw" href="${esc(entryLink(entry.id))}">${esc(entry.w)}</a>
        ${entry.cls ? `<span class="gram-class">${esc(entry.cls)}</span>` : ''}
        <span class="family-gloss">${esc(entry.g)}</span></div>
      <div class="family-build">${pieceChips({ u: entry.u, k: entry.k, words: entry.words }, { link: '?piece=', highlight })}
        ${entry.lit ? `<span class="family-lit">“${literalHtml(entry.lit, data.labels)}”</span>` : ''}
        ${entry.unsure ? '<span class="result-usage">(Parks is not sure)</span>' : ''}</div>
    </li>`;
  }

  function list(entries, highlight, shownAll) {
    const shown = shownAll ? entries : entries.slice(0, MAX_ROWS);
    return `<ol class="family-list">${shown.map(e => wordRow(e, highlight)).join('')}</ol>` +
      (entries.length > shown.length
        ? `<p><button type="button" class="outline secondary" id="wb-all">Show all ${entries.length}</button></p>` : '');
  }

  function spelledLike(key) {
    const heads = data.heads[key.replace(/\./g, '')] || [];
    if (!heads.length) return '';
    return `<details class="learn-details"><summary>${heads.length === 1 ? 'One dictionary entry is' : heads.length + ' dictionary entries are'} spelled like this piece</summary>
      <ul class="spelled-list">${heads.map(h =>
        `<li><a lang="x-paw" class="family-word" href="${esc(entryLink(h.id))}">${esc(h.w)}</a>
         ${h.cls ? `<span class="gram-class">${esc(h.cls)}</span>` : ''} ${esc(h.g)}</li>`).join('')}</ul>
      <p class="result-usage">The dictionary does not say which entry a piece is. Compare these meanings with the literal translations in the list.</p>
    </details>`;
  }

  function showPiece(key, all) {
    const indexes = byKey.get(key) || [];
    const entries = indexes.map(i => data.entries[i]);
    const out = document.getElementById('wb-result');
    if (!entries.length) return false;
    out.innerHTML = `<h4 class="family-title"><span class="piece piece--on" lang="x-paw">${esc(key)}</span>
        is printed in ${entries.length} ${entries.length === 1 ? 'word' : 'words'}</h4>
      ${spelledLike(key)}${list(entries, key, all)}`;
    const more = document.getElementById('wb-all');
    if (more) more.addEventListener('click', () => showPiece(key, true));
    return true;
  }

  function showEnglish(text, all) {
    const q = text.toLowerCase();
    const word = new RegExp('\\b' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const entries = data.entries.filter(e => word.test((e.g || '').toLowerCase()) || word.test((e.lit || '').toLowerCase()));
    const out = document.getElementById('wb-result');
    if (!entries.length) return false;
    out.innerHTML = `<h4 class="family-title">${entries.length} ${entries.length === 1 ? 'word' : 'words'} with
        “${esc(text)}” in the meaning or the literal translation</h4>${list(entries, null, all)}`;
    const more = document.getElementById('wb-all');
    if (more) more.addEventListener('click', () => showEnglish(text, true));
    return true;
  }

  function find(text, pieceOnly) {
    const raw = (text || '').trim();
    const out = document.getElementById('wb-result');
    if (!raw) { out.innerHTML = ''; return; }
    const key = plainKey(raw);
    let found = showPiece(key);
    if (!found && !pieceOnly && raw.length > 1) found = showEnglish(raw);
    if (!found) {
      out.innerHTML = `<p class="result-usage">Nothing found for “${esc(raw)}”. A piece is typed in the dictionary's letters
        (<span lang="x-paw">kaa</span>, <span lang="x-paw">raʔuk</span>); an English word is looked up in the meanings.</p>`;
    }
    const url = new URL(window.location.href);
    url.searchParams.set(found && byKey.has(key) ? 'piece' : 'q', raw);
    url.searchParams.delete(found && byKey.has(key) ? 'q' : 'piece');
    window.history.replaceState({}, '', url);
  }

  function renderTable5(table) {
    const box = document.getElementById('wb-table5');
    if (!table) { box.innerHTML = ''; return; }
    box.innerHTML = table.rows.slice(1).map(row => `<div class="affix-card">
        <span class="affix-form" lang="x-paw">${esc(row[1])}</span>
        <span class="affix-name">${esc(row[0])}</span>
        <span class="affix-meaning">${esc(row[2])}</span>
        <span class="affix-example" lang="x-paw">${esc(row[3])}</span>
      </div>`).join('');
  }

  function renderPlainTable(id, table) {
    const box = document.getElementById(id);
    if (!box || !table) return;
    const [head, ...rows] = table.rows;
    box.innerHTML = `<table class="guide-table"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td${i ? ' lang="x-paw"' : ''}>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }

  function renderExamples() {
    const box = document.getElementById('wb-examples');
    box.innerHTML = data.examples.map(id => byId.get(id)).filter(Boolean).map(e => `<div class="example-card">
        <a class="example-word" lang="x-paw" href="${esc(entryLink(e.id))}">${esc(e.w)}</a>
        <span class="example-gloss">${esc(e.g)}</span>
        ${pieceChips({ u: e.u, k: e.k, words: e.words }, { link: '?piece=' })}
        <span class="family-lit">“${literalHtml(e.lit, data.labels)}”</span>
      </div>`).join('');
  }

  function renderCommon() {
    const top = Array.from(byKey.entries()).sort((a, b) => b[1].length - a[1].length).slice(0, 36);
    document.getElementById('wb-common').innerHTML = '<span class="section-label">Printed most often</span>' + top.map(([key, idx]) =>
      `<a class="piece" lang="x-paw" href="?piece=${encodeURIComponent(key)}">${esc(key)} <small>${idx.length}</small></a>`).join('');
  }

  function renderLabels() {
    const body = document.querySelector('#wb-labels tbody');
    body.innerHTML = Object.keys(data.labels).sort().map(k =>
      `<tr><td><strong>${esc(k)}</strong></td><td>${esc(data.labels[k].meaning)}</td>
       <td lang="x-paw" class="result-skiri">${esc(data.labels[k].forms || '')}</td></tr>`).join('');
  }

  // A click on a piece anywhere on the page looks that piece up here, without leaving the page.
  function onPieceClick(event) {
    const link = event.target.closest('a.piece');
    if (!link) return;
    const key = new URL(link.href, window.location.href).searchParams.get('piece');
    if (!key) return;
    event.preventDefault();
    document.getElementById('wb-q').value = key;
    find(key, true);
    document.getElementById('explorer').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try {
      data = await load('wordbuilding');
    } catch (error) {
      document.getElementById('wb-table5').innerHTML = '<p class="result-usage">The word-building data could not be loaded.</p>';
      return;
    }
    data.entries.forEach((entry, i) => {
      byId.set(entry.id, entry);
      new Set(entry.k).forEach(key => {
        if (!byKey.has(key)) byKey.set(key, []);
        byKey.get(key).push(i);
      });
    });
    renderTable5(data.tables['5']);
    renderPlainTable('wb-table4', data.tables['4']);
    renderExamples();
    renderCommon();
    renderLabels();

    const input = document.getElementById('wb-q');
    let timer = null;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => find(input.value), 250);
    });
    document.querySelectorAll('.key-btn[data-insert]').forEach(btn => btn.addEventListener('click', () => {
      const at = input.selectionStart == null ? input.value.length : input.selectionStart;
      input.value = input.value.slice(0, at) + btn.dataset.insert + input.value.slice(input.selectionEnd == null ? at : input.selectionEnd);
      input.focus();
      find(input.value);
    }));
    document.querySelector('.learn-page').addEventListener('click', onPieceClick);

    const params = new URLSearchParams(window.location.search);
    const start = params.get('piece') || params.get('q');
    if (start) {
      input.value = start;
      find(start, Boolean(params.get('piece')));
      document.getElementById('explorer').scrollIntoView({ block: 'start' });
    }
  });
})();
