/**
 * Dictionary search for the published site. It runs in the visitor's browser:
 * the whole dictionary is one file, data/dictionary.json, written by
 * scripts/build_static_site.py, and Fuse.js searches it.
 *
 * A result shows the entry as Parks prints it: headword, phonetic form,
 * class, senses, and, behind "More from this entry", the examples, the
 * numbered verb forms, the other forms he gives, the stems listed under a
 * bound stem, his analysis of the word and the forms he cites from related
 * languages. Nothing shown here is computed; it is all stored text.
 *
 * Two more openings help a learner read the entry (helpers in skiri.js):
 * "Say it, syllable by syllable" cuts the printed phonetic form at its
 * syllable dots, and "How the word is built" shows the pieces of the printed
 * derivation, cut at Parks's plus signs. Both arrange what is printed.
 *
 * index.html?id=<entry id> shows one entry, opened; other pages link to it.
 */

// Where a visitor sends a correction: a new issue in the project's repository.
const CORRECTIONS_URL = 'https://github.com/kevinsinkar/pari-pakuru/issues/new';

// What the five numbered forms of a verb entry are. The same labels as the local app
// shows (DB/query_api.py, FORM_DESCRIPTIONS); keep the two in step.
const FORM_LABELS = {
  1: '1st person singular, indicative, perfective',
  2: '3rd person singular, indicative, perfective',
  3: '3rd person singular, indicative, imperfective',
  4: '3rd person singular, absolutive, subordinate perfective',
  5: '3rd person singular, indicative, perfective intentive',
};

// Parks's abbreviations for the languages he cites.
const LANGUAGES = {
  'SB': 'South Band Pawnee', 'Ar': 'Arikara', 'Ar.': 'Arikara', 'Ki': 'Kitsai', 'Ki.': 'Kitsai',
  'Wi': 'Wichita', 'Wi.': 'Wichita', 'Sk': 'Skiri Pawnee', 'Sk.': 'Skiri Pawnee', 'Pa': 'Pawnee', 'Pa.': 'Pawnee',
};

const MAX_SHOWN = 60;

let dictionaryData = null;
let fuseIndex = null;

function esc(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function initializeSearch() {
  try {
    const response = await fetch('data/dictionary.json');
    dictionaryData = await response.json();
    fuseIndex = new Fuse(dictionaryData, {
      keys: ['headword', 'normalized_form', 'glosses.definition', 'examples.english_translation',
             'verb_forms.form', 'other_forms.form', 'derived_stems.form'],
      threshold: 0.3,
      minMatchCharLength: 2,
    });
  } catch (error) {
    console.error('Failed to load dictionary data:', error);
  }
}

function performSearch(query, lang = 'auto', gramClass = null) {
  if (!dictionaryData || !fuseIndex || !query) {
    return [];
  }
  let results = fuseIndex.search(query).map(r => r.item);
  const q = query.toLowerCase();
  const has = text => Boolean(text) && text.toLowerCase().includes(q);

  if (lang === 'skiri') {
    results = results.filter(e =>
      has(e.headword) || has(e.normalized_form) ||
      (e.verb_forms || []).some(f => has(f.form)) ||
      (e.other_forms || []).some(f => has(f.form)) ||
      (e.derived_stems || []).some(f => has(f.form)));
  } else if (lang === 'english') {
    results = results.filter(e =>
      (e.glosses || []).some(g => has(g.definition)) ||
      (e.examples || []).some(ex => has(ex.english_translation)));
  }
  if (gramClass) {
    results = results.filter(e => e.grammatical_class === gramClass);
  }
  return results;
}

function correctionLink(entry) {
  const name = entry.headword + (entry.stem_preverb ? ' ' + entry.stem_preverb : '');
  const where = entry.source === 'blue_book' ? "Pâri Pakûru' textbook"
    : (entry.page_number ? `Parks Dictionary, p. ${entry.page_number}` : 'Parks Dictionary');
  const title = `Correction: ${name}`;
  const body = `Entry: ${name}\nEntry id: ${entry.entry_id}\nSource: ${where}\n\n` +
    'What is wrong on the site:\n\n\nWhat the source says (page, and the form as printed):\n\n';
  return `${CORRECTIONS_URL}?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
}

// A word taken from the textbook: the form the book prints, and the dictionary's entry for the same word if it has one.
function textbookLine(entry) {
  if (entry.source !== 'blue_book') return '';
  const printed = (entry.bb_printed || []).map(p =>
    `<span lang="x-paw">${esc(p.form)}</span>${p.page ? ` (p. ${esc(p.page)})` : ''}`).join(', ');
  const same = entry.bb_variant_of
    ? ` The dictionary has this word as <span lang="x-paw">${esc(entry.bb_variant_of.headword)}</span>.` : '';
  if (!printed && !same) return '';
  return `<p class="result-usage">${printed ? `As the textbook prints it: ${printed}.` : ''}${same}</p>`;
}

// "Say it, syllable by syllable": the printed phonetic form cut at its dots, each symbol with a hint.
function sayItBlock(entry, open) {
  if (typeof Skiri === 'undefined' || !entry.phonetic_form) return '';
  const body = Skiri.soundItOut(entry.phonetic_form, entry.simplified_pronunciation);
  if (!body) return '';
  return `<details class="result-more result-say"${open ? ' open' : ''}><summary>Say it, syllable by syllable</summary>${body}` +
    '<p class="result-usage"><a href="guide.html">All the sounds, with examples</a></p></details>';
}

// "How the word is built": the pieces of Parks's derivation and his literal translation.
function builtBlock(entry, open) {
  if (typeof Skiri === 'undefined' || !entry.build) return '';
  const body = Skiri.buildBlock(entry.build);
  if (!body) return '';
  // the word web draws this word with the other words in which the dictionary prints the same pieces
  const web = `<p class="result-usage"><a href="wordweb.html?word=${encodeURIComponent(entry.entry_id)}">See it in a picture, with the words that share its pieces</a></p>`;
  return `<details class="result-more result-built"${open ? ' open' : ''}><summary>How the word is built</summary>${body}${web}</details>`;
}

// The topics an entry is filed under (a rough sorting by English keywords), as links to the topic lists.
// "Hear it": a link to a search for the word in Indiana University's online Skiri dictionary, where some entries have a
// recording (Skiri.hearUrls). Only for the dictionary's own entries: a word found only in the textbook is not there.
function hearLine(entry) {
  if (entry.source === 'blue_book' || !entry.headword) return '';
  const urls = Skiri.hearUrls(entry.headword, ((entry.glosses || [])[0] || {}).definition);
  return `<p class="result-hear"><a href="${esc(urls.word)}" target="_blank" rel="noopener">Hear it at Indiana University</a>` +
    '<span class="result-usage"> opens a search for this word in their Skiri dictionary; some entries there have a recording.' +
    `${urls.english ? ` If the word is not found, <a href="${esc(urls.english)}" target="_blank" rel="noopener">search its English</a>.` : ''}</span></p>`;
}

function topicLine(entry) {
  const tags = (entry.tags || []).filter(t => t !== 'ceremony');
  if (!tags.length) return '';
  return '<p class="result-topics">' + tags.map(t =>
    `<a class="cat-tag" href="topics.html?tag=${encodeURIComponent(t)}">${esc(t)}</a>`).join(' ') + '</p>';
}

function moreOfEntry(entry, open) {
  const parts = [];

  const examples = entry.examples || [];
  if (examples.length) {
    parts.push('<h4>Examples</h4><ul class="result-examples">' + examples.map(ex =>
      `<li><span lang="x-paw" class="result-skiri">${esc(ex.skiri_text)}</span>` +
      `${ex.english_translation ? ` &mdash; ${esc(ex.english_translation)}` : ''}` +
      `${ex.usage_context ? ` <em class="result-usage">${esc(ex.usage_context)}</em>` : ''}` +
      `${ex.source === 'blue_book' ? ' <small class="result-usage">(Blue Book)</small>' : ''}</li>`
    ).join('') + '</ul>');
  }

  const forms = entry.verb_forms || [];
  if (forms.length) {
    parts.push('<h4>The forms Parks gives for this verb</h4><table class="result-forms"><tbody>' + forms.map(f =>
      `<tr><td>${esc(f.n)}.</td><td lang="x-paw" class="result-skiri">${esc(f.form)}</td>` +
      `<td><small>${esc(FORM_LABELS[f.n] || '')}</small></td></tr>`
    ).join('') + '</tbody></table>');
  }

  const others = entry.other_forms || [];
  if (others.length) {
    parts.push('<h4>Other forms</h4><ul class="result-examples">' + others.map(f =>
      `<li>${f.type ? `<em>${esc(f.type)}</em> ` : ''}<span lang="x-paw" class="result-skiri">${esc(f.form)}</span></li>`
    ).join('') + '</ul>');
  }

  const stems = entry.derived_stems || [];
  if (stems.length) {
    parts.push('<h4>Stems Parks lists under this one</h4><ul class="result-examples">' + stems.map(s =>
      `<li><span lang="x-paw" class="result-skiri">${esc(s.form)}</span>${s.definition ? ` &mdash; ${esc(s.definition)}` : ''}</li>`
    ).join('') + '</ul>');
  }

  if (entry.etymology && entry.etymology.raw) {
    parts.push(`<h4>Parks's analysis of the word</h4><p class="result-etymology" lang="x-paw">${esc(entry.etymology.raw)}</p>`);
  }

  const cognates = entry.cognates || [];
  if (cognates.length) {
    parts.push('<h4>Forms Parks cites from related languages</h4><ul class="result-examples">' + cognates.map(c =>
      `<li>${esc(LANGUAGES[c.language] || c.language)}: <span class="result-skiri">${esc(c.form)}</span></li>`
    ).join('') + '</ul>');
  }

  if (entry.detail_held) {
    parts.push('<p class="result-usage">The verb forms and the analysis of this word are not shown here. ' +
      'Words to do with ceremony are waiting for review by the Pawnee community.</p>');
  }

  if (!parts.length) {
    return '';
  }
  return `<details class="result-more"${open ? ' open' : ''}><summary>More from this entry</summary>${parts.join('')}</details>`;
}

function renderSearchResults(results, total, open) {
  const container = document.getElementById('search-results');
  if (!container) return;

  if (results.length === 0) {
    container.innerHTML = '<article style="text-align:center; padding:2rem; color:var(--earth-500);"><p>No results found.</p></article>';
    return;
  }

  let html = '<div class="results-list">';
  if (total && total > results.length) {
    html += `<p class="result-citation">Showing the first ${results.length} of ${total} results. Add a letter or a word to narrow the search.</p>`;
  }
  for (const entry of results) {
    // Both spellings of the headword are written; the page shows the dictionary's unless the visitor chose the
    // learner spelling with the switch at the top (Skiri.spell). A word found only in the textbook has one.
    const parks = entry.headword + (entry.stem_preverb ? ' ' + entry.stem_preverb : '');
    const learner = entry.normalized_form && entry.normalized_form !== entry.headword ? entry.normalized_form : '';

    // All senses, numbered when there is more than one; usage notes inline
    const glosses = entry.glosses || [];
    const glossHtml = glosses.map(g =>
      `<p class="result-gloss">${glosses.length > 1 ? `<strong>${esc(g.sense_number)}.</strong> ` : ''}${esc(g.definition)}` +
      `${g.usage_notes ? ` <em class="result-usage">(${esc(g.usage_notes)})</em>` : ''}</p>`
    ).join('');

    // Where the entry stands in the printed source
    const citation = entry.source === 'blue_book'
      ? "Pâri Pakûru' textbook"
      : (entry.page_number ? `Parks Dictionary, p. ${esc(entry.page_number)}` : '');
    const wordClass = [entry.grammatical_class, entry.verb_class].filter(Boolean).join(' ');

    html += `<article class="result-card">
      <div class="result-header">
        <h3 lang="x-paw">${Skiri.spell(parks, learner)}</h3>
        ${learner ? `<span class="secondary-spelling" lang="x-paw">${Skiri.spellOther(parks, learner)}</span>` : ''}
      </div>
      <div class="result-meta">
        <span class="gram-class">${esc(wordClass || 'word')}</span>
        ${entry.blue_book_attested ? '<span class="badge-attested">Blue Book</span>' : ''}
      </div>
      ${glossHtml}
      ${textbookLine(entry)}
      ${entry.simplified_pronunciation ? `<p class="result-pronunciation">${esc(entry.simplified_pronunciation)}</p>` : ''}
      ${entry.phonetic_form ? `<p class="result-ipa" lang="x-paw">${esc(entry.phonetic_form)}</p>` : ''}
      ${hearLine(entry)}
      ${sayItBlock(entry, open)}
      ${builtBlock(entry, open)}
      ${moreOfEntry(entry, open)}
      ${topicLine(entry)}
      <p class="result-citation">${citation ? citation + ' &middot; ' : ''}<a href="index.html?id=${encodeURIComponent(entry.entry_id)}">Link to this entry</a> &middot; <a href="${esc(correctionLink(entry))}" target="_blank" rel="noopener">Send a correction</a></p>
    </article>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

function showResults(results, limit) {
  renderSearchResults(results.slice(0, limit), results.length);
}

// One entry by its id, with everything opened (index.html?id=...).
function showEntry(entryId) {
  const entry = (dictionaryData || []).find(e => e.entry_id === entryId);
  if (!entry) return false;
  renderSearchResults([entry], 1, true);
  return true;
}

function handleSearchSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const query = form.querySelector('input[name="q"]').value.trim();
  const lang = form.querySelector('input[name="direction"]:checked')?.value || 'auto';

  if (!query) return;

  showResults(performSearch(query, lang), MAX_SHOWN);

  const url = `?q=${encodeURIComponent(query)}&lang=${lang}`;
  window.history.replaceState({}, '', url);
}

function setDirection(direction) {
  const input = document.querySelector('input[name="direction"]');
  if (input) input.value = direction;
}

document.addEventListener('DOMContentLoaded', async () => {
  // Only the published site carries data/dictionary.json; the local app searches on the server.
  if (!document.getElementById('hero-search-form') && !document.getElementById('search-results')) return;
  await initializeSearch();
  if (!dictionaryData) return;

  const searchForm = document.getElementById('hero-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', handleSearchSubmit);
  }

  // Run search from ?q= URL parameter (quick-word chips, shared links)
  const params = new URLSearchParams(window.location.search);
  const urlQuery = (params.get('q') || '').trim();
  const urlId = (params.get('id') || '').trim();
  if (urlId && showEntry(urlId)) {
    const shown = document.getElementById('search-results');
    if (shown && shown.scrollIntoView) shown.scrollIntoView({ block: 'start' });
  } else if (urlQuery) {
    const input = document.querySelector('input[name="q"]');
    if (input) input.value = urlQuery;
    showResults(performSearch(urlQuery, params.get('lang') || 'auto'), MAX_SHOWN);
  }

  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      if (query.length > 2) {
        showResults(performSearch(query), 10);
      }
    });
  }
});
