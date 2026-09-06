#!/usr/bin/env node
'use strict';

// Run from any directory: node scripts/check_frontend.cjs
// Executes the real application scripts with narrow DOM/event stubs. These are
// regressions for observed state/privacy bugs, not browser or layout validation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const staticPath = path.join(__dirname, '..', 'src', 'scientist_os', 'static');
const sources = ['app.js', 'studio.js'].map(name => ({
  name, source: fs.readFileSync(path.join(staticPath, name), 'utf8'),
}));
const copy = value => JSON.parse(JSON.stringify(value));

class Element {
  constructor(selector, elements) {
    this.selector = selector;
    this.elements = elements;
    this.value = '';
    this.innerHTML = '';
    this.textContent = '';
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.matches = new Map();
    this.fields = {};
    this.selectedOptions = [];
    this.inert = false;
    this.open = false;
    this.isConnected = true;
    const classes = new Set();
    this.classList = {
      add: name => classes.add(name), remove: name => classes.delete(name),
      contains: name => classes.has(name),
      toggle(name, enabled) { if (enabled) classes.add(name); else classes.delete(name); },
    };
  }
  querySelector(selector) { return this.elements(selector); }
  querySelectorAll(selector) { return this.matches.get(selector) || []; }
  setAttribute(name, value) { this.attributes.set(name, value); }
  removeAttribute(name) { this.attributes.delete(name); }
  addEventListener(name, callback) { this.listeners.set(name, callback); }
  showModal() { this.open = true; }
  close() { this.open = false; }
  scrollIntoView() {}
  focus() {}
  closest() { return this; }
}

function harness(records) {
  const elements = new Map();
  const get = selector => {
    if (!elements.has(selector)) elements.set(selector, new Element(selector, get));
    return elements.get(selector);
  };
  get('meta[name="scientist-token"]').content = 'test-only-token';
  const documentEvents = new Map();
  const notifications = [];
  const requests = [];
  const context = {
    document: {
      querySelector: get, querySelectorAll: () => [],
      addEventListener(name, callback) {
        const callbacks = documentEvents.get(name) || [];
        callbacks.push(callback);
        documentEvents.set(name, callbacks);
      },
    },
    location: {hash: ''}, history: {replaceState() {}},
    addEventListener() {}, setTimeout: () => 0, clearTimeout() {},
    confirm: () => true, console, TextDecoder,
    FormData: class {
      constructor(form) { this.fields = form.fields; }
      get(name) { return this.fields[name] ?? null; }
      getAll(name) { const value = this.fields[name]; return value == null ? [] : Array.isArray(value) ? value : [value]; }
      has(name) { return Object.hasOwn(this.fields, name); }
    },
    fetch() { throw Error('Unexpected network request in the frontend regression check'); },
  };
  context.window = context;
  vm.createContext(context);
  for (const {name, source} of sources) vm.runInContext(source, context, {filename: name});
  // Keep real templates, bindings, routing and escaping. A browser normally
  // parses innerHTML; tests supply only the individual controls they exercise.
  context.render = () => {};
  context.notify = (message, error = false) => notifications.push({message, error});
  context.refresh = async () => {};
  let respond = () => { throw Error('Unexpected API call'); };
  context.api = async (endpoint, method = 'GET', body) => {
    requests.push({endpoint, method, body: body === undefined ? undefined : copy(body)});
    return respond(endpoint, method, body);
  };
  const evaluate = expression => vm.runInContext(expression, context);
  const setRecords = values => {
    context.fixtureRecords = copy(values);
    evaluate('state = {records: fixtureRecords, runs: [], stages: [], provider_configured: false}');
  };
  setRecords(records);
  return {
    get, context, evaluate, setRecords, notifications, requests,
    studio: context.Studio,
    respond(callback) { respond = callback; },
    async click(dataset) {
      const button = new Element('clicked button', get);
      button.dataset = dataset;
      button.textContent = 'Test action';
      const event = {target: button, preventDefault() {}};
      // Event delivery starts every listener before awaiting its async work.
      await Promise.all(documentEvents.get('click').map(callback => callback(event)));
    },
    async submit(selector, fields) {
      const form = get(selector);
      form.fields = fields;
      assert.equal(typeof form.onsubmit, 'function', `${selector} must have a submit handler`);
      await form.onsubmit({target: form, preventDefault() {}});
    },
  };
}

function manuscript(overrides = {}) {
  return {
    id: 'manuscript_' + '1'.repeat(32), kind: 'manuscript', title: 'Fictional study',
    content: 'Fictional study text', revision: 1, review_status: 'approved', links: [],
    metadata: {studio_type: 'manuscript', external_allowed: false, sections: [{
      id: '2'.repeat(32), title: 'Results', text: 'A 🧫 observation. PRIVATE_OTHER_TEXT',
      figure_ids: [], reference_ids: [], supplementary: false,
    }]}, ...overrides,
  };
}

async function openManuscript(env, record) {
  await env.click({studioOpen: 'manuscript', id: record.id});
  env.studio.bind('manuscripts');
  env.get('#manuscript-text').value = record.metadata.sections[0].text;
}

const checks = [];
const check = (name, run) => checks.push({name, run});

check('reference metadata cannot become markup in the list or editor', async () => {
  const attack = '<button data-studio-action="writing-example">untrusted-control</button>';
  const reference = {
    id: 'reference_' + '3'.repeat(32), kind: 'reference', title: 'Example reference',
    revision: 1, review_status: 'unreviewed', links: [],
    metadata: {year: attack, authors: [null, 42, '<em>Author text</em>'], full_text_ids: []},
  };
  const valid = {...reference, id: 'reference_' + '4'.repeat(32), metadata: {year: 2026, authors: ['Example author']}};
  const env = harness([reference, valid]);
  env.studio.bind('references');
  const rendered = env.get('#reference-results').innerHTML;
  assert.ok(!rendered.includes(attack));
  assert.ok(!rendered.includes('<em>Author text</em>'));
  assert.ok(rendered.includes('&lt;em&gt;Author text&lt;/em&gt;'));
  assert.ok(rendered.includes('2026'), 'valid publication years must still display');
  await env.click({referenceEdit: reference.id});
  assert.ok(!env.get('#studio-dialog').innerHTML.includes(attack));
  assert.match(env.get('#studio-dialog').innerHTML, /name="year"[^>]*value=""/);
  env.setRecords([{...reference, metadata: {...reference.metadata, full_text_ids: {length: attack}}}]);
  env.studio.bind('references');
  assert.ok(!env.get('#reference-results').innerHTML.includes(attack));
  assert.equal(env.notifications.length, 0, 'malformed display metadata should not crash the reference library');
});

check('legacy free-text manuscripts stay readable without corrupting the studio', async () => {
  const legacy = manuscript({metadata: {}, content: 'A manuscript written in the previous beta.'});
  const env = harness([legacy]);
  const overview = env.evaluate('overview()');
  assert.ok(overview.includes(`data-record="${legacy.id}"`));
  assert.ok(!overview.includes('data-studio-open="manuscript"'));
  await env.click({record: legacy.id});
  assert.ok(env.get('#record-detail').innerHTML.includes(legacy.content));
  // A stale bookmarked action must also route safely, not half-initialize draft.
  await env.click({studioOpen: 'manuscript', id: legacy.id});
  assert.doesNotThrow(() => env.studio.views.manuscripts());
  assert.equal(env.notifications.length, 0);
});

check('clean draft refreshes its review status while dirty text survives a newer revision', async () => {
  const original = manuscript();
  const env = harness([original]);
  await openManuscript(env, original);
  const current = {...original, revision: 2, review_status: 'unreviewed'};
  env.setRecords([current]);
  let view = env.studio.views.manuscripts();
  assert.ok(view.includes('Revision 2 · unreviewed'));
  assert.ok(!view.includes('Revision 1 · approved'));
  env.studio.bind('manuscripts');
  const editor = env.get('#manuscript-text');
  editor.value = 'Unsaved scientist correction';
  editor.selectionStart = editor.selectionEnd = editor.value.length;
  editor.oninput();
  env.setRecords([{...current, revision: 3}]);
  view = env.studio.views.manuscripts();
  assert.ok(view.includes('Unsaved scientist correction'));
  assert.ok(view.includes('Unsaved changes'));
  env.context.confirm = () => false;
  assert.equal(env.studio.canLeave(), false);
  assert.equal(env.requests.length, 0, 'view refresh cannot silently save or approve anything');
});

check('passage request preserves UTF-16 boundaries and sends only the selection', async () => {
  const record = manuscript();
  const evidence = {id: 'source_' + '5'.repeat(32), kind: 'source', title: 'Chosen evidence', metadata: {}};
  const env = harness([record, evidence]);
  await openManuscript(env, record);
  const editor = env.get('#manuscript-text');
  editor.selectionStart = 2;
  editor.selectionEnd = 4;
  editor.listeners.get('select')();
  env.get('#passage-instruction').value = 'Check this selected term.';
  env.get('#passage-sources').matches.set('input:checked', [{value: evidence.id}]);
  env.respond(() => ({proposal: null, run: {status: 'failed', error: {code: 'test_only'}, trace: []}}));
  await env.click({studioAction: 'propose-passage'});
  assert.equal(env.requests.length, 1);
  const request = env.requests[0];
  assert.equal(request.endpoint, `manuscripts/${record.id}/proposals`);
  assert.deepEqual([request.body.start, request.body.end, request.body.selected_text], [2, 4, '🧫']);
  assert.equal(request.body.section_id, record.metadata.sections[0].id);
  assert.deepEqual(request.body.source_ids, [evidence.id]);
  assert.ok(!JSON.stringify(request.body).includes('PRIVATE_OTHER_TEXT'));
  assert.ok(!env.requests.some(item => item.endpoint.endsWith('/apply')));
});

check('library excerpts map normalized CRLF text to the displayed original revision', async () => {
  const original = '[Lines 1-4]\r\nPreface 🧫\r\nTarget β\r\nPRIVATE_TAIL';
  const document = {
    id: 'document_' + '6'.repeat(32), kind: 'document', title: 'Fictional proposal',
    content: original, revision: 1, review_status: 'unreviewed', links: [],
    metadata: {filename: 'proposal.txt', category: 'proposal', external_allowed: false},
  };
  const env = harness([document]);
  await env.click({libraryId: document.id});
  const reader = env.get('#library-extracted-text');
  // DOM textarea.value normalizes CRLF to LF. This is a platform contract, not
  // a copy of the application's offset-conversion algorithm.
  reader.value = original.replace(/\r\n/g, '\n');
  const visibleSelection = '🧫\nTarget β';
  reader.selectionStart = reader.value.indexOf(visibleSelection);
  reader.selectionEnd = reader.selectionStart + visibleSelection.length;
  // A background refresh changes state, but the on-screen text is still rev 1.
  env.setRecords([{...document, revision: 2, content: 'New text that was not displayed'}]);
  await env.click({studioAction: 'register-excerpt'});
  env.respond(() => ({id: 'source_' + '7'.repeat(32)}));
  await env.submit('#excerpt-form', {title: 'Chosen passage'});
  assert.equal(env.requests.length, 1);
  const request = env.requests[0];
  assert.equal(request.endpoint, `library/${document.id}/excerpts`);
  assert.equal(request.body.expected_revision, 1);
  assert.equal(request.body.selected_text, '🧫\r\nTarget β');
  assert.equal(request.body.start, original.indexOf('🧫'));
  assert.equal(request.body.end, original.indexOf('\r\nPRIVATE_TAIL'));
  assert.equal(request.body.external_allowed, false);
  assert.ok(!JSON.stringify(request.body).includes('PRIVATE_TAIL'));
});

for (const fail of [false, true]) {
  check(`pending save freezes editing and ${fail ? 'failure retains unsaved text' : 'success restores editing'}`, async () => {
    const record = manuscript();
    const env = harness([record]);
    await openManuscript(env, record);
    const editor = env.get('#manuscript-text');
    editor.value = 'Scientist edit before saving';
    editor.selectionStart = editor.selectionEnd = editor.value.length;
    editor.oninput();
    let resolve, reject;
    const pendingResponse = new Promise((yes, no) => { resolve = yes; reject = no; });
    env.respond(() => pendingResponse);
    const saving = env.click({studioAction: 'save-document'});
    assert.equal(env.get('#main').inert, true, 'editors must be noninteractive while their snapshot is saving');
    assert.equal(env.get('#main').attributes.get('aria-busy'), 'true');
    assert.equal(env.studio.canLeave(), false, 'sidebar navigation must honor the same pending operation');
    await env.click({studioAction: 'save-document'});
    assert.equal(env.requests.length, 1, 'a second save cannot race the pending save');
    if (fail) reject(Error('Synthetic save conflict'));
    else {
      const saved = copy(record);
      saved.revision = 2;
      saved.review_status = 'unreviewed';
      saved.metadata.sections[0].text = editor.value;
      env.setRecords([saved]);
      resolve(saved);
    }
    await saving;
    assert.equal(env.get('#main').inert, false);
    assert.equal(env.get('#main').attributes.has('aria-busy'), false);
    const view = env.studio.views.manuscripts();
    assert.ok(view.includes('Scientist edit before saving'));
    if (fail) {
      assert.ok(view.includes('Unsaved changes'));
      assert.ok(env.notifications.some(item => item.message === 'Synthetic save conflict' && item.error));
    } else assert.ok(view.includes('Revision 2 · unreviewed'));
  });
}

(async () => {
  for (const {name, run} of checks) {
    let timeout;
    try {
      await Promise.race([
        run(),
        new Promise((_, reject) => { timeout = setTimeout(() => reject(Error('Check did not settle within five seconds')), 5000); }),
      ]);
      console.log(`PASS ${name}`);
    } catch (error) {
      console.error(`FAIL ${name}\n${error.stack}`);
      process.exitCode = 1;
      return;
    } finally { clearTimeout(timeout); }
  }
  console.log(`${checks.length} frontend regression checks passed (DOM stubs; browser verification remains separate).`);
})();
