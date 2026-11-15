// Checks the published site. It runs docs/static/js/skiri.js and search.js against docs/data/dictionary.json
// with a stand-in for the browser page, then checks the learning pages and their data files: that every
// piece shown for a word stands in the derivation the dictionary prints, that the seven verbs agree with
// their dictionary entries, that nothing held for community review is in the files, and that every link
// between the pages leads to a file. Needs Node.js; nothing else.
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
sandbox.window.localStorage = { getItem: () => null, setItem() {} };
vm.runInContext(fs.readFileSync(path.join(docs, 'static', 'js', 'skiri.js'), 'utf8'), sandbox);
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
  const leaks = held.filter(e => e.verb_forms || e.etymology || e.cognates || e.other_forms || e.derived_stems || e.build);
  check(`ceremony entries carry no added detail (${held.length} held, ${leaks.length} leaks)`, held.length > 0 && leaks.length === 0);
  run(held[0].headword, 'skiri');
  check('held entry says why', html.includes('waiting for review by the Pawnee community'));

  // ---- the two openings that help a learner read an entry
  run('sakuuruʔ', 'skiri');
  check('syllable view: sakuuruʔ in three syllables, the second accented',
    html.includes('Say it, syllable by syllable') && /class="syl syl--accent"><span class="syl-ipa" lang="x-paw">kuú</.test(html) &&
    (html.match(/class="syl[ "]/g) || []).length >= 3);
  run('asaaki', 'skiri');
  check('word pieces: asaaki as asaa + kis, with the literal translation',
    html.includes('How the word is built') && html.includes('words.html?piece=asaa') && html.includes('words.html?piece=kis') &&
    html.includes('dog + <abbr class="gram-label"'));
  const one = data.find(e => e.headword === 'asaaki');
  vm.runInContext(`showEntry(${JSON.stringify(one.entry_id)}); 0`, sandbox);
  check('index.html?id= shows one entry, opened', (html.match(/<article class="result-card">/g) || []).length === 1 &&
    html.includes('<details class="result-more result-built" open>'));

  // every piece shown is in the derivation the dictionary prints (nothing is made)
  const tight = t => String(t).replace(/\s/g, '');
  const built = data.filter(e => e.build);
  const strays = built.filter(e => !e.build.u.every(u => tight(e.etymology.raw).includes(tight(u))));
  check(`pieces stand in the printed derivation (${built.length} entries, ${strays.length} not)`, built.length > 3000 && strays.length === 0);
  if (strays.length) console.log('  e.g. ' + strays.slice(0, 5).map(e => e.headword + ' ' + JSON.stringify(e.build.u) + ' ' + e.etymology.raw).join('\n       '));

  // ---- the learning pages and their data
  const read = name => JSON.parse(fs.readFileSync(path.join(docs, 'data', name + '.json'), 'utf8'));
  const byId = new Map(data.map(e => [e.entry_id, e]));
  const heldIds = new Set(held.map(e => e.entry_id));
  const wb = read('wordbuilding');
  check(`word building: ${wb.entries.length} entries, each the same pieces as its search result`,
    wb.entries.length === built.length && wb.entries.every(w => byId.has(w.id) && JSON.stringify(byId.get(w.id).build.u) === JSON.stringify(w.u)));
  check('word building: no entry held for review', wb.entries.every(w => !heldIds.has(w.id)));
  check('word building: tables 4 and 5 and the labels are there', Boolean(wb.tables['4'] && wb.tables['5'] && wb.labels.NOM && wb.examples.length >= 4));

  const vb = read('verbs');
  const forms = vb.verbs.reduce((n, v) => n + Object.values(v.modes).reduce((m, row) => m + Object.values(row).filter(Boolean).length, 0), 0);
  check(`verbs: seven verbs, 770 forms of Appendix 1 (${vb.verbs.length}, ${forms})`, vb.verbs.length === 7 && forms === 770);
  check('verbs: each verb is tied to the entry that prints the same forms 1 and 2', vb.verbs.every(v => {
    const e = v.entry && byId.get(v.entry.id);
    const f = n => ((e && e.verb_forms) || []).find(x => x.n === n);
    return e && f(1) && f(2) && f(1).form === v.modes.indicative_perfective['1sg'] && f(2).form === v.modes.indicative_perfective['3sg'];
  }));
  check('verbs: no English line of the extraction is carried', !JSON.stringify(vb.verbs).includes('"english"'));
  check('verbs: every mode has its row of Table 8', vb.modes.length === 10 && vb.modes.every(m => m.table8 && m.table8.forms));

  const pr = read('practice');
  const cards = pr.weeks.reduce((a, w) => a.concat(w.cards), []);
  check(`practice: ${cards.length} words in ${pr.weeks.length} weeks, week 20 held back`,
    cards.length > 300 && !pr.weeks.some(w => w.week === 20) && cards.every(c => byId.has(c.id) && c.w && c.def));

  // every page is there, has no link left over from the local app, and links only to files that exist
  const pages = fs.readdirSync(docs).filter(f => f.endsWith('.html'));
  const wanted = ['index', 'learn', 'guide', 'words', 'verbs', 'practice', 'topics', 'lessons', 'flashcards', 'about'];
  check('the ten main pages are built', wanted.every(p => pages.includes(p + '.html')));
  const broken = [];
  for (const page of pages) {
    const text = fs.readFileSync(path.join(docs, page), 'utf8');
    for (const m of text.matchAll(/(?:href|src)="([^"]*)"/g)) {
      const target = m[1];
      if (/^(https?:|mailto:|#|data:|javascript:)/.test(target) || target === '') continue;
      if (target.startsWith('/')) { broken.push(page + ' -> ' + target); continue; }
      const file = decodeURIComponent(target.split(/[?#]/)[0]);
      if (file && !fs.existsSync(path.join(docs, file))) broken.push(page + ' -> ' + target);
    }
  }
  check(`links between the pages lead to files (${pages.length} pages, ${broken.length} broken)`, broken.length === 0);
  if (broken.length) console.log('  ' + Array.from(new Set(broken)).slice(0, 12).join('\n  '));
  check('entry links open one entry (index.html?id=)', /href="index\.html\?id=[^"]+"/.test(fs.readFileSync(path.join(docs, 'lesson-1.html'), 'utf8')));

  // no file numbers left, no stray markup in any rendered card
  const parks = data.filter(e => e.source !== 'blue_book');
  check('every Parks entry cites a book page 349-529', parks.every(e => e.page_number >= 349 && e.page_number <= 529));
  let bad = 0;
  for (let i = 0; i < data.length; i += 60) {
    vm.runInContext('renderSearchResults(dictionaryData.slice(' + i + ',' + (i + 60) + '), 0); 0', sandbox);
    const stripped = html.replace(/<\/?(div|article|h3|h4|span|p|strong|em|small|details|summary|ul|li|table|tbody|tr|td|a|b|i|abbr)(\s[^<>]*)?>/g, '');
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
