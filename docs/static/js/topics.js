/**
 * Words by topic (published site): filters data/dictionary.json by the topic tag of an entry.
 * A row shows what a search result shows first: the word, how it is said, its class and first meaning.
 */
(() => {
  const { esc, entryLink } = Skiri;
  const STEP = 60;
  let entries = null;
  const state = { tag: null, label: '', kind: 'all', text: '', shown: STEP };

  function kindOf(entry) {
    const cls = entry.grammatical_class || '';
    if (/^N/.test(cls)) return 'noun';
    if (/^V/.test(cls)) return 'verb';
    return 'other';
  }

  function row(entry) {
    const parks = entry.headword + (entry.stem_preverb ? ' ' + entry.stem_preverb : '');
    const learner = entry.normalized_form || entry.headword;
    const glosses = entry.glosses || [];
    return `<li class="family-item">
      <div class="family-head"><a class="family-word" lang="x-paw" href="${esc(entryLink(entry.entry_id))}">${esc(learner)}</a>
        ${learner !== parks ? `<span class="secondary-spelling" lang="x-paw">${esc(parks)}</span>` : ''}
        ${entry.grammatical_class ? `<span class="gram-class">${esc(entry.grammatical_class)}</span>` : ''}
        ${entry.blue_book_attested ? '<span class="badge-attested">Blue Book</span>' : ''}</div>
      <div class="family-build"><span class="family-gloss">${esc(glosses.length ? glosses[0].definition : '')}</span>
        ${entry.simplified_pronunciation ? `<span class="q-say">${esc(entry.simplified_pronunciation)}</span>` : ''}</div>
    </li>`;
  }

  function render() {
    const text = state.text.toLowerCase();
    const found = entries.filter(e => (e.tags || []).includes(state.tag) &&
      (state.kind === 'all' || kindOf(e) === state.kind) &&
      (!text || [e.headword, e.normalized_form].concat((e.glosses || []).map(g => g.definition))
        .some(v => v && v.toLowerCase().includes(text))));
    // words the textbook teaches first, then the alphabet
    found.sort((a, b) => (Number(b.blue_book_attested) - Number(a.blue_book_attested)) || a.headword.localeCompare(b.headword));
    document.getElementById('tp-title').textContent = state.label;
    document.getElementById('tp-count').textContent =
      `${found.length} ${found.length === 1 ? 'word' : 'words'}. Words that are also in the textbook come first.`;
    document.getElementById('tp-list').innerHTML = found.slice(0, state.shown).map(row).join('');
    document.getElementById('tp-more').hidden = found.length <= state.shown;
  }

  function choose(tag, label, scroll) {
    state.tag = tag; state.label = label; state.shown = STEP;
    document.querySelectorAll('.topic-card').forEach(c => c.classList.toggle('topic-card--on', c.dataset.tag === tag));
    document.getElementById('tp-list-section').hidden = false;
    render();
    const url = new URL(window.location.href);
    url.searchParams.set('tag', tag);
    window.history.replaceState({}, '', url);
    if (scroll) document.getElementById('tp-list-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const cards = Array.from(document.querySelectorAll('.topic-card'));
    try {
      const response = await fetch('data/dictionary.json');
      entries = await response.json();
    } catch (error) {
      document.getElementById('tp-topics').insertAdjacentHTML('afterend', '<p class="result-usage">The dictionary could not be loaded.</p>');
      return;
    }
    cards.forEach(card => card.addEventListener('click', e => {
      e.preventDefault();
      choose(card.dataset.tag, card.dataset.label, true);
    }));
    document.querySelectorAll('[data-kind]').forEach(b => b.addEventListener('click', () => {
      state.kind = b.dataset.kind; state.shown = STEP;
      document.querySelectorAll('[data-kind]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      render();
    }));
    let timer = null;
    document.getElementById('tp-filter').addEventListener('input', e => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.text = e.target.value.trim(); state.shown = STEP; render(); }, 200);
    });
    document.getElementById('tp-more').addEventListener('click', () => { state.shown += STEP * 2; render(); });

    const wanted = new URLSearchParams(window.location.search).get('tag');
    const card = cards.find(c => c.dataset.tag === wanted);
    if (card) choose(card.dataset.tag, card.dataset.label, false);
  });
})();
