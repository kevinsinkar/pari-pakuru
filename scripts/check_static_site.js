// Checks the published site. It runs docs/static/js/skiri.js and search.js against docs/data/dictionary.json
// with a stand-in for the browser page, then checks the learning pages and their data files: that every
// piece shown for a word stands in the derivation the dictionary prints, that the seven verbs agree with
// their dictionary entries, that nothing held for community review is in the files, and that every link
// between the pages leads to a file. It also reads sources/catalogue.json: the page "Learn with others" may
// list only what the register marks for learners. Needs Node.js; nothing else.
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

  // ---- the lessons, the phrases and the practice box (2026-11-15)
  const page = name => fs.readFileSync(path.join(docs, name), 'utf8');
  const text = h => h.replace(/<[^>]+>/g, ' ').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/\s+/g, ' ');
  // the row of a word list that begins with a form (an apostrophe may be written as it is or as &#39;)
  const row = (h, form) => {
    const i = [form, form.replace(/'/g, '&#39;')].map(f => h.indexOf('>' + f + '<')).find(k => k >= 0);
    return i === undefined ? '' : h.slice(i, h.indexOf('</tr>', i));
  };
  const l9 = page('lesson-9.html');
  const stemRow = row(l9, "ti•'at");
  check("lesson 9: ti•'at links to its verb and shows no pronunciation of the stem",
    stemRow.includes('a form of') && stemRow.includes('index.html?id=') && !/uht/.test(stemRow) && !stemRow.includes('ət'));
  check('lesson pages: the pronunciation columns stand under "In the Skiri dictionary", and the line on spelling is in view',
    l9.includes('In the Skiri dictionary') && l9.includes('class="spelling-line"') && !l9.includes('not in Parks dictionary'));
  check('lesson pages cite the pages printed in the book (lesson 1: pp. 1–5)', /pp\. 1–5</.test(page('lesson-1.html')));
  const l1 = page('lesson-1.html');
  check('lesson pages: the basic words stand before the dialogues, as in the book; one side can be covered',
    l1.indexOf('id="basic-words"') > 0 && l1.indexOf('id="basic-words"') < l1.indexOf('id="dialogues"') &&
    l1.includes('data-cover="eng"') && l1.includes('cover-paw') && l1.includes('cover-eng'));
  const l18 = text(page('lesson-18.html'));
  const l10 = text(row(page('lesson-10.html'), "asku•ra•wákahu'"));
  check('lessons 10 and 18: a word has the English of its own row of the page',
    /Sutsiks•áhut\. Hold this\./.test(l18) && /Kesku•rahúrihu'\. (SB spelling )?Forgive me\./.test(l18) && !/Sutsiks•áhut\. Who's been busy/.test(l18) &&
    l10.includes('judge') && !l10.includes('police'));
  const killing = byId.get('BB-tikuwtitiku-0083');
  check('the entry made from a mis-paired row has its own meaning', Boolean(killing) && killing.glosses[0].definition === 'he is killing it');

  const ph = page('phrases.html');
  const items = Array.from(ph.matchAll(/<li class="phrase">([\s\S]*?)<\/li>/g)).map(m => ({
    forms: Array.from(m[1].matchAll(/<span lang="x-paw" class="font-serif">([^<]*)<\/span>/g)).map(f => text(f[1]).trim()),
    lessons: Array.from(m[1].matchAll(/href="lesson-(\d+)\.html#phrases"/g)).map(l => Number(l[1])),
    english: Array.from(m[1].matchAll(/class="phrase-eng cover-eng">([^<]*)</g)).map(e => text(e[1]).trim()),
  }));
  const lessonText = {};
  const inLesson = (n, s) => { lessonText[n] = lessonText[n] || text(page('lesson-' + n + '.html')); return lessonText[n].includes(s); };
  const astray = items.filter(it => !it.forms.length || !it.lessons.length ||
    !it.forms.every(f => it.lessons.some(n => inLesson(n, f))) || !it.english.every(e => !e || it.lessons.some(n => inLesson(n, e))));
  check(`phrases: ${items.length} rows, every phrase and its English printed on the page of a lesson it names (${astray.length} not)`,
    items.length >= 95 && astray.length === 0);
  if (astray.length) console.log('  e.g. ' + astray.slice(0, 4).map(it => JSON.stringify(it)).join('\n       '));
  check('phrases: the two conversations, the line on spelling, and what the page is not',
    (ph.match(/lesson-dialogue__line--spoken/g) || []).length === 16 && ph.includes('class="spelling-line"') &&
    ph.includes('No speaker of Pawnee has reviewed this page') && /Hold this\./.test(text(ph)));

  // the box that says when a word is due again: a store that keeps what it is given, and days we choose
  const kept = new Map();
  sandbox.window.localStorage = { getItem: k => (kept.has(k) ? kept.get(k) : null), setItem: (k, v) => { kept.set(k, String(v)); } };
  const box = vm.runInContext('Skiri.box', sandbox);
  const day = n => new Date(2026, 10, 15 + n, 9, 30);
  const at = n => box.dayNumber(day(n)) - box.dayNumber(day(0));
  const moves = [];
  const step = (id, right, n) => { const w = box.answer(id, right, day(n)); moves.push([w[0], w[1] - box.dayNumber(day(0))]); return w; };
  step('a', true, 0); step('a', true, 0); step('a', true, 1); step('a', true, 2); step('a', true, 4);
  step('a', true, 11); step('a', true, 25); step('a', true, 55); step('a', false, 60); step('a', true, 60); step('a', true, 61);
  step('b', false, 0);
  const expect = [[1, 1], [1, 1], [2, 4], [2, 4], [3, 11], [4, 25], [5, 55], [5, 85], [1, 60], [1, 61], [2, 64], [1, 0]];
  check('practice box: a right answer brings a word back after 1, 3, 7, 14 and 30 days; a miss starts it again the same day',
    at(1) === 1 && JSON.stringify(moves) === JSON.stringify(expect));
  check('practice box: what is due, what is new, and the count for the day',
    JSON.stringify(box.due(['a', 'b', 'c'], day(0))) === '["b"]' && JSON.stringify(box.due(['a', 'b', 'c'], day(64))) === '["b","a"]' &&
    JSON.stringify(box.fresh(['a', 'b', 'c'])) === '["c"]' && box.counts(['a', 'b', 'c'], day(63)).due === 1 &&
    box.counts(['a', 'b', 'c'], day(63)).tomorrow === 1 && box.counts(null, day(0)).seen === 2);
  const prJs = page('static/js/practice.js');
  check('practice page: today\'s words are offered first, and the flashcards feed the same box',
    page('practice.html').includes('id="pr-today"') && prJs.includes("box.answer(id, wasRight)") && prJs.includes('value="today"') &&
    page('flashcard-1.html').includes('Skiri.box.answer(eid') && page('flashcard-1.html').includes('class="spelling-line"'));

  // ---- the register of sources, the two dialects, hearing a word (2026-11-15, second part)
  const register = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'sources', 'catalogue.json'), 'utf8')).records;
  const listed = register.filter(r => r.project.section);
  const res = page('resources.html');
  const shown = Array.from(res.matchAll(/class="source-name" href="([^"]*)"/g)).map(m => m[1].replace(/&amp;/g, '&'));
  const allowed = new Set(listed.filter(r => !r.project.sensitive && r.project.link).map(r => r.project.url || r.url));
  check(`learn with others: ${shown.length} sources, each one the register marks for learners; none of the ${register.filter(r => r.project.sensitive).length} held as ceremonial`,
    shown.length === listed.length && shown.length >= 6 && shown.every(u => allowed.has(u)) &&
    !register.some(r => r.project.sensitive && shown.includes(r.project.url || r.url)));
  const everyPage = fs.readdirSync(docs).filter(f => f.endsWith('.html')).map(f => page(f));
  const address = /[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}/;
  check('no e-mail address on any page, and every page points to "Learn with others"',
    !everyPage.some(h => address.test(h.replace(/<link[^>]*>|<script[^>]*>/g, ''))) && everyPage.every(h => h.includes('href="resources.html"')));

  const marks = h => Array.from(h.matchAll(/<abbr class="dialect( dialect--spelling)?" title="([^"]*)">([^<]*)<\/abbr>/g));
  const l1marks = marks(l1);
  const allMarks = [];
  for (let n = 1; n <= 20; n++) marks(page('lesson-' + n + '.html')).forEach(m => allMarks.push(m));
  check(`dialect: the lesson pages say what the textbook says of its dialects, and every mark carries its reason (${allMarks.length} marks)`,
    l1.includes('Skiri or South Band?') && l1.includes('The accent marked in this book is that of some South Band speakers') &&
    /Kiriké ru&#39;\?|Kiriké ru'\?/.test(l1) && l1marks.some(m => m[3] === 'SB spelling') &&
    allMarks.length > 150 && allMarks.every(m => m[2].length >= 8 && ['SK', 'SB', 'SB spelling'].includes(m[3])));
  check('dialect: the book\'s own marks are on the page (lesson 2: rutki SB, rutpátsat SK), and a Skiri-marked form is not called South Band',
    /rutki<\/span>\s*<abbr class="dialect" title="[^"]*">SB</.test(page('lesson-2.html')) &&
    /rutpátsat<\/span>\s*<abbr class="dialect" title="[^"]*">SK</.test(page('lesson-2.html')));

  const hear = vm.runInContext('Skiri.hearUrls', sandbox);
  const sun = hear('sakuuruʔ', 'sun.');
  const iik = 'https://aisri-language-database.webapps.iu.edu/dictsearch/';
  check('hear it: a word links to its search in Indiana University\'s Skiri dictionary, in plain letters',
    sun.word.startsWith(iik) && sun.word.includes('database=skiri') && sun.word.includes('srchlang=Indian') && sun.word.includes('srchstring=sakuuru&') &&
    sun.english.includes('srchstring=sun&') && data.every(e => hear(e.headword, '').word.startsWith(iik)));
  run('sakuuruʔ', 'skiri');
  const withLink = html.includes('Hear it at Indiana University') && html.includes('srchstring=sakuuru&amp;');
  const bookOnly = data.find(e => e.source === 'blue_book');
  vm.runInContext(`showEntry(${JSON.stringify(bookOnly.entry_id)}); 0`, sandbox);
  check('hear it: on a dictionary entry, and not on a word found only in the textbook', withLink && !html.includes('Hear it at Indiana University'));

  // ---- the word web: the word-building data as a picture (2026-11-15). Its model runs here without a page.
  const webBox = { console, document: { addEventListener() {}, getElementById: () => null } };
  vm.createContext(webBox);
  vm.runInContext(page('static/js/wordweb.js'), webBox);
  const WW = vm.runInContext('WordWeb', webBox);
  const pic = WW.createPicture(wb, WW.makeIndex(wb));
  const printedIn = key => wb.entries.filter(e => e.k.includes(key)).length;
  // a line only where the dictionary prints the piece in the word; every piece of a drawn word drawn; the count the dictionary's
  const honest = () => pic.links.length > 0 && pic.links.every(l => l.word.entry.k.includes(l.piece.key)) &&
    Array.from(pic.words.values()).every(w => new Set(w.entry.k).size === w.deg && !heldIds.has(w.entry.id)) &&
    Array.from(pic.pieces.values()).every(q => q.total === printedIn(q.key));
  const drawnWords = () => Array.from(pic.words.values()).map(w => w.entry.w);
  const bear = pic.startEnglish('bear');
  const bearWords = drawnWords();
  check(`word web: "bear" draws the ${bearWords.length} words with that word in the meaning or the literal translation, each joined to its printed pieces`,
    Boolean(bear) && honest() && ['kurukskaatiit', 'kurukstaakaa', 'kurukspahat'].every(w => bearWords.includes(w)) &&
    Array.from(pic.words.values()).every(w => /\bbears?\b/.test((w.entry.g + ' ' + (w.entry.lit || '')).toLowerCase())) &&
    !bearWords.includes('haakararuus') && bear.best === 'kuruks' && pic.pieces.get('kuruks').deg === bear.bestCount);
  const before = pic.words.size;
  const came = pic.expand('kaatiit');
  check(`word web: choosing an oval brings in words in which that piece is printed, and no others (${came} came for kaatiit)`,
    came > 0 && pic.words.size === before + came && honest() &&
    pic.links.filter(l => l.piece.key === 'kaatiit').length === pic.pieces.get('kaatiit').deg &&
    pic.hidden('kaatiit') === printedIn('kaatiit') - pic.pieces.get('kaatiit').deg);
  const places = () => { WW.sizes(pic); WW.settle(pic, 320, 1); return JSON.stringify(pic.nodes.map(n => [n.id, Math.round(n.x), Math.round(n.y)])); };
  pic.startEnglish('black');
  const once = places(), clear = WW.overlaps(pic);
  pic.startEnglish('black');
  check(`word web: no shape lies on another, and the same start gives the same picture (${pic.nodes.length} shapes for "black")`,
    honest() && clear === 0 && places() === once);
  const byPiece = pic.startPiece('kuruks'), pieceOk = Boolean(byPiece) && honest() && pic.words.size === printedIn('kuruks');
  const byWord = pic.startWord(wb.entries.findIndex(e => e.w === 'kurukskaatiit'));
  check('word web: a picture can start from a piece or from a word; a piece that is not printed gives none',
    pieceOk && Boolean(byWord) && honest() && drawnWords().includes('kurukstaakaa') && pic.startPiece('nosuchpiece') === null);
  // what stands in a box is the printed headword and meaning, whole or cut short with a mark, never changed
  const cut = (label, full) => label === full || (label.endsWith('…') && full.startsWith(label.slice(0, -1)));
  check('word web: a box shows the printed headword and meaning, whole or cut short with a mark',
    wb.entries.every(e => cut(WW.wordLabel(e), e.w) && cut(WW.glossLabel(e), e.g.split(' (')[0].replace(/[.;,:\s]+$/, ''))));
  const webPage = page('wordweb.html');
  check('word web: the page is there, says what a line means and what the page does not say, and the word-building page leads to it',
    webPage.includes('id="ww-svg"') && webPage.includes('static/js/wordweb.js') && webPage.includes('does not say what a piece') &&
    webPage.includes('are not always the same piece') && webPage.includes('href="words.html') &&
    page('words.html').includes('href="wordweb.html"') && page('static/js/words.js').includes('wordweb.html?piece='));

  // every page is there, has no link left over from the local app, and links only to files that exist
  const pages = fs.readdirSync(docs).filter(f => f.endsWith('.html'));
  const wanted = ['index', 'learn', 'guide', 'words', 'wordweb', 'verbs', 'practice', 'topics', 'lessons', 'phrases', 'flashcards', 'resources', 'about'];
  check('the thirteen main pages are built', wanted.every(p => pages.includes(p + '.html')));
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
