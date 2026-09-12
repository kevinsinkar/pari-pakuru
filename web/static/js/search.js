/**
 * Client-side dictionary search using Fuse.js
 * Works entirely in the browser after data is loaded
 */

let dictionaryData = null;
let fuseIndex = null;

// Load dictionary data on page load
async function initializeSearch() {
  try {
    const response = await fetch('/data/dictionary.json');
    dictionaryData = await response.json();

    // Create Fuse index for fuzzy search
    fuseIndex = new Fuse(dictionaryData, {
      keys: ['headword', 'normalized_form', 'glosses.definition', 'examples.english_gloss'],
      threshold: 0.3,
      minMatchCharLength: 2,
    });

    console.log(`Loaded ${dictionaryData.length} dictionary entries`);
  } catch (error) {
    console.error('Failed to load dictionary data:', error);
  }
}

function performSearch(query, lang = 'auto', gramClass = null, tag = null) {
  if (!dictionaryData || !fuseIndex || !query) {
    return [];
  }

  let results = fuseIndex.search(query).map(r => r.item);

  if (lang === 'skiri') {
    results = results.filter(e =>
      e.headword.toLowerCase().includes(query.toLowerCase()) ||
      (e.normalized_form && e.normalized_form.toLowerCase().includes(query.toLowerCase()))
    );
  } else if (lang === 'english') {
    results = results.filter(e =>
      e.glosses.some(g => g.definition.toLowerCase().includes(query.toLowerCase())) ||
      e.examples.some(ex => ex.english_gloss.toLowerCase().includes(query.toLowerCase()))
    );
  }

  if (gramClass) {
    results = results.filter(e => e.grammatical_class === gramClass);
  }

  return results;
}

function renderSearchResults(results) {
  const container = document.getElementById('search-results');
  if (!container) return;

  if (results.length === 0) {
    container.innerHTML = '<article style="text-align:center; padding:2rem; color:var(--earth-500);"><p>No results found.</p></article>';
    return;
  }

  let html = '<div class="results-list">';
  for (const entry of results) {
    const primarySpelling = entry.normalized_form || entry.headword;
    const secondarySpelling = entry.normalized_form && entry.normalized_form !== entry.headword ? entry.headword : null;

    html += `<article class="result-card">
      <div class="result-header">
        <h3><a href="/entries/${entry.entry_id}.html">${primarySpelling}</a></h3>
        ${secondarySpelling ? `<span class="secondary-spelling">${secondarySpelling}</span>` : ''}
      </div>
      <div class="result-meta">
        <span class="gram-class">${entry.grammatical_class || 'word'}</span>
        ${entry.blue_book_attested ? '<span class="badge-attested">Blue Book</span>' : ''}
      </div>
      ${entry.glosses && entry.glosses[0] ? `<p class="result-gloss">${entry.glosses[0].definition}</p>` : ''}
      ${entry.simplified_pronunciation ? `<p class="result-pronunciation">${entry.simplified_pronunciation}</p>` : ''}
    </article>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

function handleSearchSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const query = form.querySelector('input[name="q"]').value.trim();
  const lang = form.querySelector('input[name="direction"]:checked')?.value || 'auto';

  if (!query) return;

  const results = performSearch(query, lang);
  renderSearchResults(results);

  const url = `/search?q=${encodeURIComponent(query)}&lang=${lang}`;
  window.history.replaceState({}, '', url);
}

function setDirection(direction) {
  const input = document.querySelector('input[name="direction"]');
  if (input) input.value = direction;
}

document.addEventListener('DOMContentLoaded', async () => {
  await initializeSearch();

  const searchForm = document.getElementById('hero-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', handleSearchSubmit);
  }

  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      if (query.length > 2) {
        const results = performSearch(query);
        renderSearchResults(results.slice(0, 10));
      }
    });
  }
});
