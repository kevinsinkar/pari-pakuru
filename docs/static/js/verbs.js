/**
 * The verbs page: the five numbered forms of a verb entry, Parks's Table 6 as a row of
 * positions, Appendix 1 (seven verbs in ten modes and eleven persons) with three ways
 * of reading it, Appendix 2, and the reference tables of chapter 4.
 * Data: data/verbs.json (web/learning.py, verbs_data). Every form is a printed form.
 */
(() => {
  const { esc, entryLink, load, store } = Skiri;
  let data = null;
  const state = { view: 'one', verb: 0, mode: 'indicative_perfective', test: false, formVerb: 0 };

  const cap = text => text ? text[0].toUpperCase() + text.slice(1) : '';
  const modeOf = key => data.modes.find(m => m.key === key);
  const modeLabel = m => m.label + (m.subordinate ? ' (subordinate)' : '');

  // ------------------------------------------------------------ five forms
  function renderFormVerbs() {
    const box = document.getElementById('vb-form-verbs');
    box.innerHTML = data.verbs.map((v, i) => v.entry
      ? `<button type="button" class="choice-btn" data-form-verb="${i}" aria-pressed="${i === state.formVerb}">${esc(v.gloss)}</button>` : '').join('');
  }

  function renderForms() {
    const verb = data.verbs[state.formVerb];
    const box = document.getElementById('vb-forms');
    if (!verb || !verb.entry) { box.innerHTML = ''; return; }
    const e = verb.entry;
    const rows = [1, 2, 3, 4, 5].map(n => {
      const f = e.forms.find(x => x.n === n);
      return `<tr${f ? '' : ' class="form-missing"'}><td class="form-n">${n}</td>
        <td lang="x-paw" class="form-word">${f ? esc(f.form) : '<span class="result-usage">not given for this verb</span>'}</td>
        <td><span class="form-plain">${esc(data.form_plain[n])}</span><br><small class="result-usage">${esc(data.form_labels[n])}</small></td></tr>`;
    }).join('');
    box.innerHTML = `<div class="stem-card">
        <span class="section-label">The entry</span>
        <a class="stem-word" lang="x-paw" href="${esc(entryLink(e.id))}">${esc(e.w)}</a>
        <span class="gram-class">${esc(e.cls)}</span>
        <span class="stem-gloss">${esc(e.g)}</span>
      </div>
      <table class="forms-table"><thead><tr><th></th><th>The word</th><th>What it says</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  // ------------------------------------------------------------ positions, tables 8 and 9
  function renderPositions() {
    const t = data.tables['6'];
    const box = document.getElementById('vb-positions');
    if (!t || t.rows.length < 3) { box.innerHTML = ''; return; }
    const names = t.rows[1], notes = t.rows[2];
    box.innerHTML = names.map((name, i) => `<div class="position${name === 'STEM' ? ' position--stem' : ''}">
        <span class="position-name">${esc(name)}</span>
        ${notes[i] ? `<span class="position-note">${esc(notes[i])}</span>` : ''}</div>`).join('<span class="position-arrow" aria-hidden="true">+</span>');
  }

  function plainTable(table, skiriFrom) {
    const [head, ...rows] = table.rows;
    const width = Math.max(...table.rows.map(r => r.length));
    return `<table class="guide-table"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>` +
      rows.map(r => '<tr>' + r.map((c, i) => {
        const span = i === r.length - 1 && r.length < width ? ` colspan="${width - r.length + 1}"` : '';
        return `<td${span}${i >= (skiriFrom || 1) ? ' lang="x-paw"' : ''}>${esc(c)}</td>`;
      }).join('') + '</tr>').join('') + '</tbody></table>';
  }

  // Tables 15 and 16 print a row of numbered positions over a row of what stands there.
  function slotTable(table) {
    const cards = [];
    for (let r = 0; r + 1 < table.rows.length; r += 2) {
      table.rows[r].forEach((title, i) => cards.push(
        `<div class="slot-card"><span class="slot-title">${esc(title)}</span><span class="slot-body" lang="x-paw">${esc(table.rows[r + 1][i] || '')}</span></div>`));
    }
    return `<div class="slot-row">${cards.join('')}</div>`;
  }

  function renderModesList() {
    document.getElementById('vb-modes-list').innerHTML = '<ul class="mode-list">' + data.modes.map(m => m.table8
      ? `<li><a href="#paradigms" data-mode="${esc(m.key)}"><strong>${esc(modeLabel(m))}</strong></a>
           <span lang="x-paw" class="result-skiri">${esc(m.table8.forms)}</span>
           <span class="result-usage">${esc(m.table8.functions.join('; '))}</span></li>` : '').join('') + '</ul>';
  }

  // ------------------------------------------------------------ Appendix 1
  function cell(form) {
    if (!form) return '<td class="pcell pcell--empty"></td>';
    return `<td class="pcell${state.test ? ' pcell--hidden' : ''}" lang="x-paw" tabindex="${state.test ? 0 : -1}"><span>${esc(form)}</span></td>`;
  }

  function renderModeCard() {
    const box = document.getElementById('vb-mode-card');
    if (state.view === 'modes') { box.innerHTML = ''; return; }
    const m = modeOf(state.mode);
    const t = m.table8;
    box.innerHTML = `<div class="mode-card"><strong>${esc(modeLabel(m))}</strong>` +
      (t ? ` <span class="mode-prefix">mode prefix: <span lang="x-paw" class="result-skiri">${esc(t.forms)}</span></span>
            <span class="mode-use">Used for: ${esc(t.functions.join('; ').toLowerCase())}.</span>` : '') + '</div>';
  }

  function renderParadigm() {
    const box = document.getElementById('vb-table');
    const persons = data.persons;
    let head, body;
    if (state.view === 'one') {
      const verb = data.verbs[state.verb];
      head = `<th>Who</th><th>${esc(cap(verb.gloss))}</th>`;
      body = persons.map(p => `<tr><th scope="row">${esc(p.label)}</th>${cell(verb.modes[state.mode][p.key])}</tr>`).join('');
    } else if (state.view === 'verbs') {
      head = '<th>Who</th>' + data.verbs.map(v => `<th>${esc(cap(v.gloss))}</th>`).join('');
      body = persons.map(p => `<tr><th scope="row">${esc(p.label)}</th>${data.verbs.map(v => cell(v.modes[state.mode][p.key])).join('')}</tr>`).join('');
    } else {
      const verb = data.verbs[state.verb];
      head = '<th>Who</th>' + data.modes.map(m => `<th>${esc(modeLabel(m))}</th>`).join('');
      body = persons.map(p => `<tr><th scope="row">${esc(p.label)}</th>${data.modes.map(m => cell(verb.modes[m.key][p.key])).join('')}</tr>`).join('');
    }
    box.innerHTML = `<table class="paradigm paradigm--${state.view}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>` +
      (state.test ? '<p class="result-usage">Say the form, then choose the cell to check yourself.</p>' : '');
    document.getElementById('vb-verb-label').style.display = state.view === 'verbs' ? 'none' : '';
    document.getElementById('vb-mode-label').style.display = state.view === 'modes' ? 'none' : '';
    renderModeCard();
  }

  function renderControls() {
    document.getElementById('vb-verb').innerHTML = data.verbs.map((v, i) =>
      `<option value="${i}"${i === state.verb ? ' selected' : ''}>${esc(cap(v.gloss))}${v.entry ? ' — ' + esc(v.entry.w) : ''}</option>`).join('');
    const group = sub => data.modes.filter(m => m.subordinate === sub).map(m =>
      `<option value="${esc(m.key)}"${m.key === state.mode ? ' selected' : ''}>${esc(m.label)}</option>`).join('');
    document.getElementById('vb-mode').innerHTML =
      `<optgroup label="Main statements">${group(false)}</optgroup><optgroup label="Inside a longer sentence (subordinate)">${group(true)}</optgroup>`;
  }

  // ------------------------------------------------------------ Appendix 2 and the reference tables
  function renderRoots() {
    document.getElementById('vb-roots').innerHTML = `<table class="guide-table"><thead><tr>
      <th>Verb</th><th>Meaning</th><th>One</th><th>Two</th><th>More than two</th></tr></thead><tbody>` +
      data.irregular_roots.map(r => `<tr><td lang="x-paw" class="result-skiri">${esc(r.w)}${r.note ? ' ' + esc(r.note) : ''}</td><td>${esc(r.g)}</td>
        <td lang="x-paw">${esc(r.sg)}</td><td lang="x-paw">${esc(r.du)}</td><td lang="x-paw">${esc(r.pl)}</td></tr>`).join('') + '</tbody></table>';
  }

  function renderReference() {
    const order = ['10', '13', '15', '16', '17'];
    document.getElementById('vb-reference').innerHTML = order.filter(n => data.tables[n]).map(n => {
      const t = data.tables[n];
      const body = (n === '15' || n === '16') ? slotTable(t) : `<div class="guide-table-wrap">${plainTable(t, n === '17' ? 99 : 1)}</div>`;
      return `<details class="learn-details"><summary>${esc(t.title)} <small class="result-usage">p. ${esc(t.pages.join(', '))}</small></summary>${body}</details>`;
    }).join('');
  }

  function setPressed(selector, attr, value) {
    document.querySelectorAll(selector).forEach(b => b.setAttribute('aria-pressed', String(b.getAttribute(attr) === String(value))));
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try {
      data = await load('verbs');
    } catch (error) {
      document.getElementById('vb-forms').innerHTML = '<p class="result-usage">The verb data could not be loaded.</p>';
      return;
    }
    const saved = store.get('verbs-view', null);
    if (saved && ['one', 'verbs', 'modes'].includes(saved.view)) state.view = saved.view;
    state.formVerb = Math.max(0, data.verbs.findIndex(v => v.gloss === 'to go' && v.entry));
    state.verb = state.formVerb;

    renderFormVerbs(); renderForms(); renderPositions(); renderModesList();
    document.getElementById('vb-table9').innerHTML = plainTable(data.tables['9'], 1);
    renderControls(); renderParadigm(); renderRoots(); renderReference();
    setPressed('[data-view]', 'data-view', state.view);

    document.getElementById('vb-form-verbs').addEventListener('click', e => {
      const b = e.target.closest('[data-form-verb]');
      if (!b) return;
      state.formVerb = Number(b.dataset.formVerb);
      setPressed('[data-form-verb]', 'data-form-verb', state.formVerb);
      renderForms();
    });
    document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => {
      state.view = b.dataset.view;
      store.set('verbs-view', { view: state.view });
      setPressed('[data-view]', 'data-view', state.view);
      renderParadigm();
    }));
    document.getElementById('vb-verb').addEventListener('change', e => { state.verb = Number(e.target.value); renderParadigm(); });
    document.getElementById('vb-mode').addEventListener('change', e => { state.mode = e.target.value; renderParadigm(); });
    document.getElementById('vb-test').addEventListener('click', e => {
      state.test = !state.test;
      e.currentTarget.setAttribute('aria-pressed', String(state.test));
      e.currentTarget.textContent = state.test ? 'Show the forms' : 'Hide the forms: test yourself';
      renderParadigm();
    });
    const reveal = e => {
      const td = e.target.closest('.pcell--hidden');
      if (td && (e.type === 'click' || e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); td.classList.remove('pcell--hidden'); }
    };
    document.getElementById('vb-table').addEventListener('click', reveal);
    document.getElementById('vb-table').addEventListener('keydown', reveal);
    document.getElementById('vb-modes-list').addEventListener('click', e => {
      const a = e.target.closest('[data-mode]');
      if (!a) return;
      state.mode = a.dataset.mode;
      if (state.view === 'modes') { state.view = 'one'; setPressed('[data-view]', 'data-view', state.view); }
      renderControls(); renderParadigm();
    });
  });
})();
