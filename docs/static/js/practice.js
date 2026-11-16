/**
 * The practice page: six games over printed forms.
 *   meaning / word / match / type   the flashcard words        (data/practice.json)
 *   verbs                           Appendix 1, seven verbs    (data/verbs.json)
 *   pieces                          the printed derivations    (data/wordbuilding.json)
 * A game only ever shows forms that are in those files; it makes none.
 * Missed words are kept in the visitor's browser (localStorage "practice-missed"), and so is the box that says
 * when a flashcard word is due again (Skiri.box in skiri.js: after 1 day, then 3, 7, 14 and 30).
 */
(() => {
  const { esc, shuffle, store, load, entryLink, pieceChips, literalHtml, box } = Skiri;
  const ROUND = 10;
  const PAIRS = 5;
  const BLURB = {
    meaning: 'You see a Skiri word. Choose what it means.',
    word: 'You see a meaning. Choose the Skiri word.',
    match: 'Five words and five meanings. Choose a word, then its meaning.',
    type: 'You see a meaning. Type the Skiri word, in the learner spelling or the dictionary\'s.',
    verbs: 'One of the seven verbs the dictionary writes out in full. Choose the form for the person asked.',
    pieces: 'You see the pieces the dictionary prints for a word, and its literal translation. Choose the word.',
  };
  const files = {};
  const state = { game: 'meaning', week: 'today', verbMode: 'indicative_perfective', questions: [], at: 0, right: 0, missed: [] };
  const stage = () => document.getElementById('pr-stage');

  async function need(name) {
    if (!files[name]) files[name] = await load(name);
    return files[name];
  }

  // ---------------------------------------------------------------- pools
  function allCards() {
    return files.practice.weeks.reduce((a, w) => a.concat(w.cards), []);
  }

  // Every flashcard word once, in the order of the weeks.
  function wordIds() {
    return Array.from(new Set(allCards().map(c => c.id)));
  }

  // Today's words: the words that are due, the longest overdue first; when fewer than a round are due,
  // words not met yet fill it up, in the order of the flashcard weeks.
  function todays() {
    const byId = new Map();
    allCards().forEach(c => { if (!byId.has(c.id)) byId.set(c.id, c); });
    const order = Array.from(byId.keys());
    const due = box.due(order).slice(0, ROUND);
    const fresh = box.fresh(order).slice(0, ROUND - due.length);
    return due.concat(fresh).map(id => byId.get(id));
  }

  function pool() {
    if (state.week === 'today') return todays();
    if (state.week === 'all') return allCards();
    if (state.week === 'missed') {
      const ids = new Set(store.get('practice-missed', []));
      return allCards().filter(c => ids.has(c.id));
    }
    const week = files.practice.weeks.find(w => String(w.week) === String(state.week));
    return week ? week.cards : allCards();
  }

  // Two meanings that share a word ("wolf" and "coyote, wolf") would make two answers look right.
  const COMMON = new Set(['with', 'that', 'this', 'from', 'have', 'being', 'which', 'used', 'such', 'into', 'when', 'like',
    'kind', 'type', 'small', 'large', 'someone', 'something', 'one\'s', 'person', 'thing']);
  function meaningWords(def) {
    return (String(def || '').toLowerCase().match(/[a-z']{4,}/g) || []).filter(w => !COMMON.has(w));
  }
  function overlap(a, b) {
    const words = new Set(meaningWords(a.def));
    return meaningWords(b.def).some(w => words.has(w));
  }

  // n items of `from` that are not `item` and differ from it (and each other) in the field shown;
  // items whose meaning shares a word with the right answer are passed over while others are left
  function others(item, from, field, n) {
    const taken = new Set([item[field]]);
    const out = [];
    for (const strict of [true, false]) {
      for (const c of shuffle(from)) {
        if (out.length === n) break;
        if (taken.has(c[field]) || (strict && item.def && c.def && overlap(item, c))) continue;
        taken.add(c[field]);
        out.push(c);
      }
    }
    return out;
  }

  function cardFace(card) {
    return `<span class="q-word" lang="x-paw">${esc(card.w)}</span>` +
      (card.say ? `<span class="q-say">${esc(card.say)}</span>` : '');
  }

  function cardAnswer(card) {
    return `<div class="answer-card"><span class="q-word" lang="x-paw">${esc(card.w)}</span>
      ${card.p ? `<span class="secondary-spelling" lang="x-paw">${esc(card.p)}</span>` : ''}
      ${card.say ? `<span class="q-say">${esc(card.say)}</span>` : ''}
      ${card.ipa ? `<span class="result-ipa" lang="x-paw">${esc(card.ipa)}</span>` : ''}
      <span class="answer-def">${esc(card.def)}</span>
      <a href="${esc(entryLink(card.id))}">See the entry</a>
      ${card.bb ? '' : `<a href="${esc(Skiri.hearUrls(card.p || card.w, card.def).word)}" target="_blank" rel="noopener">Hear it at Indiana University</a>`}</div>`;
  }

  // ---------------------------------------------------------------- building a round
  function buildChoice(game) {
    const cards = pool();
    const wide = cards.length >= 4 && state.week !== 'today' ? cards : allCards();
    return shuffle(cards).slice(0, ROUND).map(card => {
      const field = game === 'meaning' ? 'def' : 'w';
      const options = shuffle([card].concat(others(card, wide, field, 3)));
      return {
        id: card.id,
        prompt: game === 'meaning' ? cardFace(card) : `<span class="q-def">${esc(card.def)}</span>`,
        ask: game === 'meaning' ? 'What does it mean?' : 'Which word is it?',
        options: options.map(o => ({ html: game === 'meaning' ? esc(o.def) : `<span lang="x-paw">${esc(o.w)}</span>`, right: o.id === card.id })),
        after: cardAnswer(card),
      };
    });
  }

  function buildType() {
    return shuffle(pool()).slice(0, ROUND).map(card => ({ id: card.id, card, type: true }));
  }

  function buildVerbs() {
    const v = files.verbs;
    const modes = state.verbMode === 'all' ? v.modes.map(m => m.key) : [state.verbMode];
    const cells = [];
    v.verbs.forEach((verb, vi) => modes.forEach(mode => v.persons.forEach(p => {
      if (verb.modes[mode][p.key]) cells.push({ vi, mode, person: p });
    })));
    return shuffle(cells).slice(0, ROUND).map(c => {
      const verb = v.verbs[c.vi];
      const row = verb.modes[c.mode];
      const right = row[c.person.key];
      const wrong = shuffle(Array.from(new Set(Object.values(row).filter(f => f && f !== right)))).slice(0, 3);
      const m = v.modes.find(x => x.key === c.mode);
      return {
        prompt: `<span class="q-def">${esc(verb.gloss)}</span><span class="q-say">${esc(m.label)}${m.subordinate ? ' (subordinate)' : ''}</span>`,
        ask: `Which form is for “${c.person.label}”?`,
        options: shuffle([right].concat(wrong)).map(f => ({ html: `<span lang="x-paw">${esc(f)}</span>`, right: f === right })),
        after: `<div class="answer-card"><span class="q-word" lang="x-paw">${esc(right)}</span>
          <span class="answer-def">${esc(verb.gloss)}: ${esc(c.person.label)}, ${esc(m.label.toLowerCase())}</span>
          <a href="verbs.html#paradigms">See the whole verb</a></div>`,
      };
    });
  }

  function buildPieces() {
    const usable = files.wordbuilding.entries.filter(e => e.lit && e.u.length <= 3 && !e.words && !e.unsure && e.w.length <= 16);
    return shuffle(usable).slice(0, ROUND).map(entry => {
      // wrong answers that begin like the right one make the reader look at every piece
      const near = usable.filter(e => e.id !== entry.id && e.w[0] === entry.w[0]);
      const options = shuffle([entry].concat(others(entry, near.length >= 3 ? near : usable, 'w', 3)));
      return {
        prompt: pieceChips({ u: entry.u, k: entry.k }, { link: null }) +
          `<span class="q-say">“${literalHtml(entry.lit, files.wordbuilding.labels)}”</span>`,
        ask: 'Which word does the dictionary build from these pieces?',
        options: options.map(o => ({ html: `<span lang="x-paw">${esc(o.w)}</span>`, right: o.id === entry.id })),
        after: `<div class="answer-card"><span class="q-word" lang="x-paw">${esc(entry.w)}</span>
          <span class="answer-def">${esc(entry.g)}</span>
          <a href="words.html?piece=${encodeURIComponent(entry.k[0])}">Other words with <span lang="x-paw">${esc(entry.u[0])}</span></a></div>`,
      };
    });
  }

  // ---------------------------------------------------------------- playing
  function progress() {
    return `<div class="fc-progress"><span>Question ${state.at + 1} of ${state.questions.length}</span>
      <progress value="${state.at + 1}" max="${state.questions.length}"></progress></div>`;
  }

  function remember(id, wasRight) {
    if (!id) return;
    let missed = store.get('practice-missed', []).filter(x => x !== id);
    if (!wasRight) missed = [id].concat(missed).slice(0, 60);
    store.set('practice-missed', missed);
    box.answer(id, wasRight);          // when the word is due again
  }

  function nextButton() {
    const last = state.at === state.questions.length - 1;
    return `<p><button type="button" id="pr-next">${last ? 'See how you did' : 'Next'}</button></p>`;
  }

  function wireNext() {
    const next = document.getElementById('pr-next');
    next.addEventListener('click', () => { state.at += 1; state.at < state.questions.length ? ask() : summary(); });
    next.focus();
  }

  function answered(q, wasRight, label) {
    if (wasRight) state.right += 1; else state.missed.push(label || '');
    remember(q.id, wasRight);
  }

  function askChoice(q) {
    stage().innerHTML = `${progress()}<div class="question"><div class="q-prompt">${q.prompt}</div><p class="q-ask">${esc(q.ask)}</p>
      <div class="options">${q.options.map((o, i) => `<button type="button" class="option" data-i="${i}"><span class="option-n">${i + 1}</span>${o.html}</button>`).join('')}</div>
      <div id="pr-after"></div></div>`;
    const buttons = Array.from(stage().querySelectorAll('.option'));
    const choose = i => {
      if (buttons[0].disabled) return;
      const picked = q.options[i];
      buttons.forEach((b, n) => {
        b.disabled = true;
        if (q.options[n].right) b.classList.add('option--right');
        else if (n === i) b.classList.add('option--wrong');
      });
      answered(q, picked.right, q.after);
      document.getElementById('pr-after').innerHTML =
        `<p class="verdict ${picked.right ? 'verdict--right' : 'verdict--wrong'}">${picked.right ? 'Right.' : 'Not this time.'}</p>${q.after}${nextButton()}`;
      wireNext();
    };
    buttons.forEach((b, i) => b.addEventListener('click', () => choose(i)));
    stage().onkeydown = e => {
      const n = Number(e.key);
      if (n >= 1 && n <= buttons.length && e.target.tagName !== 'INPUT') choose(n - 1);
    };
  }

  // Both spellings count: the learner spelling (â, ') and the dictionary's (aa, ʔ).
  function spellingKey(text) {
    return text.normalize('NFC').toLowerCase().trim()
      .replace(/[’ʼ`ʔ]/g, "'").replace(/â/g, 'aa').replace(/î/g, 'ii').replace(/û/g, 'uu').replace(/č/g, 'c').replace(/\s+/g, ' ');
  }
  const noLength = key => key.replace(/aa/g, 'a').replace(/ii/g, 'i').replace(/uu/g, 'u').replace(/'/g, '');

  function askType(q) {
    const card = q.card;
    const wanted = [card.w, card.p].filter(Boolean).reduce((a, s) => a.concat(s.split(/\s*,\s*/)), []).map(spellingKey);
    stage().innerHTML = `${progress()}<div class="question"><div class="q-prompt"><span class="q-def">${esc(card.def)}</span></div>
      <p class="q-ask">Type the Skiri word.</p>
      <form id="pr-type" class="type-form" autocomplete="off">
        <input type="text" id="pr-input" lang="x-paw" spellcheck="false" autocapitalize="off" aria-label="The Skiri word">
        <div class="key-row" aria-label="Letters that are not on a keyboard">
          ${['â', 'î', 'û', "'", 'č', 'ʔ'].map(k => `<button type="button" class="key-btn" data-insert="${esc(k)}">${esc(k)}</button>`).join('')}
          <button type="button" class="key-btn key-btn--wide" id="pr-hint">How is it said?</button>
        </div>
        <button type="submit">Check</button>
      </form>
      <div id="pr-after"></div></div>`;
    const input = document.getElementById('pr-input');
    input.focus();
    stage().onkeydown = null;
    stage().querySelectorAll('.key-btn[data-insert]').forEach(b => b.addEventListener('click', () => {
      const at = input.selectionStart == null ? input.value.length : input.selectionStart;
      input.value = input.value.slice(0, at) + b.dataset.insert + input.value.slice(input.selectionEnd == null ? at : input.selectionEnd);
      input.focus();
      input.setSelectionRange(at + 1, at + 1);
    }));
    document.getElementById('pr-hint').addEventListener('click', e => {
      e.currentTarget.outerHTML = `<span class="q-say">${esc(card.say || 'No guide for this word.')}</span>`;
    });
    document.getElementById('pr-type').addEventListener('submit', e => {
      e.preventDefault();
      if (input.disabled || !input.value.trim()) return;
      const typed = spellingKey(input.value);
      const right = wanted.includes(typed);
      const close = !right && wanted.some(w => noLength(w) === noLength(typed));
      input.disabled = true;
      e.target.querySelectorAll('button').forEach(b => { b.disabled = true; });
      answered(q, right, cardAnswer(card));
      document.getElementById('pr-after').innerHTML =
        `<p class="verdict ${right ? 'verdict--right' : 'verdict--wrong'}">${right ? 'Right.'
          : close ? 'Nearly: the letters are right, but check the long vowels and the glottal stop.' : 'Not this time.'}</p>${cardAnswer(card)}${nextButton()}`;
      wireNext();
    });
  }

  function ask() {
    const q = state.questions[state.at];
    q.type ? askType(q) : askChoice(q);
  }

  // The matching game is one board after another, not question by question.
  function playMatch() {
    const cards = others({ def: null }, pool(), 'def', ROUND);
    const boards = [];
    for (let i = 0; i < cards.length; i += PAIRS) boards.push(cards.slice(i, i + PAIRS));
    let board = 0, slips = 0, pairs = 0;
    const show = () => {
      const set = boards[board];
      const left = shuffle(set), right = shuffle(set);
      stage().innerHTML = `<div class="fc-progress"><span>Board ${board + 1} of ${boards.length}</span>
          <progress value="${board + 1}" max="${boards.length}"></progress></div>
        <div class="match-board">
          <div class="match-col">${left.map(c => `<button type="button" class="match-tile" data-side="w" data-id="${esc(c.id)}"><span lang="x-paw">${esc(c.w)}</span></button>`).join('')}</div>
          <div class="match-col">${right.map(c => `<button type="button" class="match-tile" data-side="d" data-id="${esc(c.id)}">${esc(c.def)}</button>`).join('')}</div>
        </div><p class="result-usage" id="pr-match-note">Choose a word, then its meaning.</p>`;
      stage().onkeydown = null;
      let picked = null, done = 0;
      stage().querySelectorAll('.match-tile').forEach(tile => tile.addEventListener('click', () => {
        if (tile.disabled) return;
        if (!picked || picked.dataset.side === tile.dataset.side) {
          if (picked) picked.classList.remove('match-tile--picked');
          picked = tile;
          tile.classList.add('match-tile--picked');
          return;
        }
        const first = picked;
        picked = null;
        first.classList.remove('match-tile--picked');
        if (first.dataset.id === tile.dataset.id) {
          [first, tile].forEach(t => { t.disabled = true; t.classList.add('match-tile--done'); });
          done += 1; pairs += 1;
          remember(tile.dataset.id, true);
          if (done === set.length) {
            board += 1;
            setTimeout(() => (board < boards.length ? show() : finish()), 600);
          }
        } else {
          slips += 1;
          remember(first.dataset.side === 'w' ? first.dataset.id : tile.dataset.id, false);
          [first, tile].forEach(t => { t.classList.add('match-tile--no'); setTimeout(() => t.classList.remove('match-tile--no'), 500); });
        }
      }));
    };
    const finish = () => {
      stage().innerHTML = `<div class="summary"><h3>${pairs} pairs matched${slips ? `, ${slips} ${slips === 1 ? 'slip' : 'slips'}` : ', no slips'}</h3>
        <p>${slips ? 'The words you slipped on are kept under “Words I missed”.' : 'Try a week you have not done yet.'}</p>${todayLine()}${againButtons()}</div>`;
      wireAgain();
    };
    if (!boards.length) { empty(); return; }
    show();
  }

  // After a round of today's words: what is left for today.
  function todayLine() {
    if (state.week !== 'today') return '';
    const n = box.counts(wordIds());
    return `<p class="today-line">${n.due
      ? `${n.due} ${n.due === 1 ? 'word is' : 'words are'} still due today.`
      : 'Nothing more is due today. That is enough for one day: come back tomorrow.'}</p>`;
  }

  function againButtons() {
    let label = 'Another round';
    if (state.week === 'today' && !box.counts(wordIds()).due) {
      label = box.fresh(wordIds()).length ? 'Ten new words' : '';
    }
    return '<p class="choice-row">' + (label ? `<button type="button" id="pr-again">${label}</button>` : '') +
      '<a role="button" class="outline" href="flashcards.html">Go to the flashcards</a></p>';
  }
  function wireAgain() {
    const again = document.getElementById('pr-again');
    if (again) again.addEventListener('click', start);
    fillWeeks();
    showToday();
  }

  function summary() {
    const total = state.questions.length;
    stage().onkeydown = null;
    stage().innerHTML = `<div class="summary"><h3>${state.right} of ${total} right</h3>
      ${state.missed.length ? `<p>Look once more at the ones you missed:</p><div class="missed-list">${state.missed.join('')}</div>` : '<p>All of them. Try another game, or another week.</p>'}
      ${todayLine()}${againButtons()}</div>`;
    wireAgain();
  }

  function empty() {
    stage().innerHTML = state.week === 'today'
      ? '<p class="result-usage">Nothing is due today, and you have met every word. Come back tomorrow, or choose a week.</p>'
      : '<p class="result-usage">There are no words in this choice yet. Choose a week, or play a round first.</p>';
  }

  async function start() {
    stage().innerHTML = '<p class="loading-note">Loading…</p>';
    try {
      await need('practice');
      if (state.game === 'verbs') await need('verbs');
      if (state.game === 'pieces') await need('wordbuilding');
    } catch (error) {
      stage().innerHTML = '<p class="result-usage">The practice data could not be loaded.</p>';
      return;
    }
    state.at = 0; state.right = 0; state.missed = [];
    if (state.game === 'match') { playMatch(); return; }
    state.questions = state.game === 'type' ? buildType()
      : state.game === 'verbs' ? buildVerbs()
      : state.game === 'pieces' ? buildPieces() : buildChoice(state.game);
    if (!state.questions.length) { empty(); return; }
    ask();
    stage().scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // ---------------------------------------------------------------- setup
  function fillWeeks() {
    const select = document.getElementById('pr-week');
    if (!files.practice) return;
    const missed = store.get('practice-missed', []).length;
    const due = box.counts(wordIds()).due;
    select.innerHTML = `<option value="today">Today’s words${due ? ` (${due} due)` : ''}</option>` +
      '<option value="all">All the flashcard words</option>' +
      (missed ? `<option value="missed">Words I missed (${missed})</option>` : '') +
      files.practice.weeks.map(w => `<option value="${w.week}">Week ${w.week}: ${esc(w.label)} (${w.cards.length})</option>`).join('');
    select.value = Array.from(select.options).some(o => o.value === String(state.week)) ? String(state.week) : 'today';
    state.week = select.value;
  }

  // The panel at the top of the page: what is due today, and where the words stand.
  function showToday() {
    const host = document.getElementById('pr-today');
    if (!host || !files.practice) return;
    const ids = wordIds();
    const n = box.counts(ids);
    const fresh = box.fresh(ids).length;
    const words = k => `${k} ${k === 1 ? 'word' : 'words'}`;
    let lead, action;
    if (!n.seen) {
      lead = 'Start with ten words. A word you get right comes back tomorrow, then after three days, a week, two weeks and a month. A word you miss comes back the same day.';
      action = 'Start with ten words';
    } else if (n.due) {
      lead = `<strong>${words(n.due)} ${n.due === 1 ? 'is' : 'are'} due today.</strong> A round asks up to ten of them.`;
      action = 'Practise today’s words';
    } else {
      lead = '<strong>Nothing is due today.</strong> ' + (n.tomorrow ? `${words(n.tomorrow)} ${n.tomorrow === 1 ? 'comes' : 'come'} back tomorrow. ` : '') +
        (fresh ? 'You can stop here, or meet ten new words.' : 'You have met every word.');
      action = fresh ? 'Ten new words' : '';
    }
    const back = ['', 'the next day', 'after 3 days', 'after a week', 'after 2 weeks', 'after a month'];
    const boxes = !n.seen ? '' : '<ol class="box-row" aria-label="Where your words stand">' +
      [1, 2, 3, 4, 5].map(b => `<li><span class="box-n">${n.boxes[b]}</span><span class="box-label">box ${b}<br>${back[b]}</span></li>`).join('') +
      `<li class="box-new"><span class="box-n">${fresh}</span><span class="box-label">not met<br>yet</span></li></ol>` +
      '<p class="box-note">A right answer on a word that is due moves it one box up; a miss sends it back to box 1. ' +
      'This is kept in this browser only. <button type="button" class="link-btn" id="pr-box-reset">Empty the boxes</button></p>';
    host.innerHTML = `<h3>Today</h3><p>${lead}</p>` +
      (action ? `<p><button type="button" id="pr-today-go">${action}</button></p>` : '') + boxes;
    const go = document.getElementById('pr-today-go');
    if (go) {
      go.addEventListener('click', () => {
        if (state.game === 'verbs' || state.game === 'pieces') setGame('meaning');
        state.week = 'today';
        fillWeeks();
        start();
      });
    }
    const reset = document.getElementById('pr-box-reset');
    if (reset) {
      reset.addEventListener('click', () => {
        if (window.confirm('Empty the boxes? Every word will count as not met yet.')) { box.reset(); fillWeeks(); showToday(); }
      });
    }
  }

  function setGame(game) {
    state.game = game;
    document.querySelectorAll('[data-game]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.game === game)));
    document.getElementById('pr-blurb').textContent = BLURB[game];
    document.getElementById('pr-week-label').style.display = (game === 'verbs' || game === 'pieces') ? 'none' : '';
    document.getElementById('pr-verbmode-label').style.display = game === 'verbs' ? '' : 'none';
    store.set('practice-game', game);
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    const wanted = params.get('mode') || store.get('practice-game', 'meaning');
    setGame(BLURB[wanted] ? wanted : 'meaning');
    if (params.get('week')) state.week = params.get('week');
    try {
      await need('practice');
      fillWeeks();
      showToday();
      const verbs = await need('verbs');
      document.getElementById('pr-verbmode').innerHTML = verbs.modes.map(m =>
        `<option value="${esc(m.key)}">${esc(m.label)}${m.subordinate ? ' (subordinate)' : ''}</option>`).join('') +
        '<option value="all">All ten modes</option>';
    } catch (error) {
      stage().innerHTML = '<p class="result-usage">The practice data could not be loaded.</p>';
      return;
    }
    document.getElementById('pr-games').addEventListener('click', e => {
      const b = e.target.closest('[data-game]');
      if (b) { setGame(b.dataset.game); stage().innerHTML = ''; }
    });
    document.getElementById('pr-week').addEventListener('change', e => { state.week = e.target.value; });
    document.getElementById('pr-verbmode').addEventListener('change', e => { state.verbMode = e.target.value; });
    document.getElementById('pr-start').addEventListener('click', start);
    if (params.get('mode')) start();
  });
})();
