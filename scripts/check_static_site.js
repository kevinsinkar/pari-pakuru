// Checks the published search page: runs docs/static/js/search.js against docs/data/dictionary.json
// with a stand-in for the browser page. Needs Node.js; nothing else.
//     node scripts/check_static_site.js          (after scripts/build_static_site.py)
// Exit code 0 when every check passes.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const docs = process.argv[2] || path.join(__dirname, '..', 'docs');
const data = JSON.parse(fs.readFileSync(path.join(docs, 'data', 'dictionary.json'), 'utf8'));
let html = '';
const container = { set innerHTML(v) { html = v; }, get innerHTML() { return html; } };
const listeners = {};
const sandbox = {
  console,
  URLSearchParams,
  encodeURIComponent,
  window: { location: { search: '' }, history: { replaceState() {} } },
  document: {
    getElementById: id => (id === 'search-results' ? container : id === 'hero-search-form' ? { addEventListener() {} } : null),
    querySelector: () => null,
    addEventListener: (name, fn) => { listeners[name] = fn; },
  },
  fetch: async () => ({ json: async () => data }),
  // a plain stand-in for Fuse: substring match over the same keys the page gives it
  Fuse: class {
    constructor(items, opts) { this.items = items; this.keys = opts.keys; }
    search(q) {
      q = q.toLowerCase();
      const get = (e, key) => {
        const [a, b] = key.split('.');
        const v = e[a];
        if (b === undefined) return [v];
        return (v || []).map(x => x[b]);
      };
      return this.items.filter(e => this.keys.some(k => get(e, k).some(v => v && String(v).toLowerCase().includes(q)))).map(item => ({ item }));
    }
  },
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(docs, 'static', 'js', 'search.js'), 'utf8'), sandbox);
(async () => {
  await listeners.DOMContentLoaded();
  const run = (q, lang) => vm.runInContext(`showResults(performSearch(${JSON.stringify(q)}, ${JSON.stringify(lang || 'auto')}), MAX_SHOWN); 0`, sandbox);
  const checks = [];
  const check = (name, ok) => checks.push((ok ? 'ok   ' : 'FAIL ') + name);

  run('sakuuruʔ', 'skiri');
  check('headword search finds sakuuruʔ', html.includes('sakuuruʔ') && html.includes('sun.'));
  check('page citation is a book page', /Parks Dictionary, p\. (3[4-9]\d|4\d\d|5[0-2]\d)/.test(html));
  check('correction link present and prefilled', html.includes('issues/new?title=Correction') && html.includes('Send a correction'));

  run('tihaakararuus', 'skiri');
  check('a verb form finds its verb (haakararuus)', html.includes('haakararuus') && html.includes('The forms Parks gives for this verb'));
  check('form labels shown', html.includes('3rd person singular, indicative, perfective'));
  check('etymology shown and escaped', html.includes('&lt;haaka+raruus, be a hairy mouth&gt;') && !html.includes('<haaka+raruus'));

  run('iit-', 'skiri');
  check('derived stems shown under a bound stem', html.includes('Stems Parks lists under this one') && html.includes('iituriirik (uur...)'));
  check('cognates named by language', html.includes('South Band Pawnee') && html.includes('Arikara'));

  run('haa', 'skiri');
  check('added examples shown (kuratiihaaʔu)', html.includes('kuratiihaaʔu') && html.includes('my child.'));

  // ceremony-tagged entries: detail held
  const held = data.filter(e => e.detail_held);
  const leaks = held.filter(e => e.verb_forms || e.etymology || e.cognates || e.other_forms || e.derived_stems);
  check(`ceremony entries carry no added detail (${held.length} held, ${leaks.length} leaks)`, held.length > 0 && leaks.length === 0);
  run(held[0].headword, 'skiri');
  check('held entry says why', html.includes('waiting for review by the Pawnee community'));

  // no file numbers left, no stray markup in any rendered card
  const parks = data.filter(e => e.source !== 'blue_book');
  check('every Parks entry cites a book page 349-529', parks.every(e => e.page_number >= 349 && e.page_number <= 529));
  let bad = 0;
  for (let i = 0; i < data.length; i += 60) {
    vm.runInContext('renderSearchResults(dictionaryData.slice(' + i + ',' + (i + 60) + '), 0); 0', sandbox);
    const stripped = html.replace(/<\/?(div|article|h3|h4|span|p|strong|em|small|details|summary|ul|li|table|tbody|tr|td|a)(\s[^<>]*)?>/g, '');
    if (/[<>]/.test(stripped)) bad += 1;
  }
  check('all ' + data.length + ' entries render with every value escaped', bad === 0);
  const counts = { entries: data.length, with_verb_forms: data.filter(e => (e.verb_forms || []).length).length,
    verb_forms: data.reduce((n, e) => n + (e.verb_forms || []).length, 0), with_etymology: data.filter(e => e.etymology).length,
    cognates: data.reduce((n, e) => n + (e.cognates || []).length, 0), derived_stems: data.reduce((n, e) => n + (e.derived_stems || []).length, 0),
    examples: data.reduce((n, e) => n + (e.examples || []).length, 0), held: held.length };
  console.log(checks.join('\n'));
  console.log(JSON.stringify(counts));
  process.exit(checks.some(c => c.startsWith('FAIL')) ? 1 : 0);
})();
