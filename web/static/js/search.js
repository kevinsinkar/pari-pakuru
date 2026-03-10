/* Pari Pakuru — Search helper (minimal vanilla JS) */

// Clear live results when navigating to full search results page
document.addEventListener('htmx:beforeRequest', function(evt) {
    // If search input is empty, clear live results
    if (evt.detail.elt && evt.detail.elt.name === 'q') {
        const val = evt.detail.elt.value.trim();
        if (!val) {
            document.getElementById('live-results').innerHTML = '';
            evt.preventDefault();
        }
    }
});

// Clear live results when form is submitted (full page search)
document.addEventListener('submit', function(evt) {
    const form = evt.target;
    if (form.classList.contains('nav-search') || form.classList.contains('hero-search-form')) {
        const liveResults = document.getElementById('live-results');
        if (liveResults) liveResults.innerHTML = '';
    }
});
