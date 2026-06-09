const SESSION_ID = new URLSearchParams(window.location.search).get('session') || 'default';

const KEYS = ['A', 'B', 'C', 'D'];

// ── SSE ──────────────────────────────────────────────────────────────────────

function connectSSE() {
  const es = new EventSource(`/api/events/${SESSION_ID}`);
  es.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'blocks') renderBlocks(msg.blocks);
    } catch (_) {}
  };
  es.onerror = () => setTimeout(connectSSE, 3000);
  return es;
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function submitPrompt(text, courseIds, docIds) {
  if (!text.trim()) return;
  await fetch(`/api/prompt/${SESSION_ID}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, course_ids: courseIds, doc_ids: docIds }),
  });
  appendUserMessage(text, courseIds, docIds);
}

// ── Sidebar sessions ──────────────────────────────────────────────────────────

async function loadSessions() {
  try {
    const res = await fetch('/api/sessions');
    const sessions = await res.json();
    const list = document.getElementById('session-list');
    if (!list) return;
    list.innerHTML = sessions.map(s => `
      <div class="nav-item" data-id="${s.id}">
        <i class="ph ph-book-open"></i>
        ${escHtml(s.title)}
      </div>`).join('');
  } catch (_) {}
}

// ── Course picker ─────────────────────────────────────────────────────────────

async function loadCourses() {
  try {
    const res = await fetch('/api/courses');
    const courses = await res.json();
    const pop = document.getElementById('course-list');
    if (!pop) return;
    pop.innerHTML = courses.map(c => `
      <div class="pop-item" data-course-id="${c.id}">
        <span class="ck"><i class="ph-bold ph-check"></i></span>
        <div><div>${escHtml(c.name)}</div></div>
      </div>`).join('');
    pop.querySelectorAll('.pop-item').forEach(el => {
      el.addEventListener('click', () => toggleCourse(el));
    });
  } catch (_) {}
}

function toggleCourse(el) {
  el.classList.toggle('sel');
  updateCourseChips();
}

function getSelectedCourseIds() {
  return [...document.querySelectorAll('#course-list .pop-item.sel')]
    .map(el => Number(el.dataset.courseId));
}

function getSelectedDocIds() {
  return [...document.querySelectorAll('.chip[data-doc-id]')]
    .map(el => el.dataset.docId);
}

function updateCourseChips() {
  const attached = document.querySelector('.attached');
  if (!attached) return;
  const existing = [...attached.querySelectorAll('.chip[data-course-id]')];
  existing.forEach(c => c.remove());
  document.querySelectorAll('#course-list .pop-item.sel').forEach(el => {
    const name = el.querySelector('div > div').textContent.trim();
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.dataset.courseId = el.dataset.courseId;
    chip.innerHTML = `<i class="ph lead ph-book-bookmark"></i> ${escHtml(name)} <span class="x"><i class="ph ph-x"></i></span>`;
    chip.querySelector('.x').addEventListener('click', () => {
      chip.remove();
      el.classList.remove('sel');
    });
    attached.appendChild(chip);
  });
}

// ── Thread rendering ──────────────────────────────────────────────────────────

function appendUserMessage(text, courseIds, docIds) {
  const thread = document.getElementById('thread');
  if (!thread) return;
  const courseNames = [...document.querySelectorAll('#course-list .pop-item.sel')]
    .map(el => el.querySelector('div > div').textContent.trim());
  const pillsHtml = courseNames.map(n =>
    `<span class="src-pill"><i class="ph ph-book-bookmark"></i> ${escHtml(n)}</span>`
  ).join('');
  const msg = document.createElement('div');
  msg.className = 'msg user-msg';
  msg.innerHTML = `
    <div class="msg-role"><div class="dot user">Y</div><div class="who">You</div></div>
    <div class="user-text">${escHtml(text)}</div>
    ${pillsHtml ? `<div class="source-pills">${pillsHtml}</div>` : ''}`;
  thread.appendChild(msg);
  thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
}

function renderBlocks(blocks) {
  const thread = document.getElementById('thread');
  if (!thread) return;
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ai-msg';
  wrapper.innerHTML = `<div class="msg-role"><div class="dot ai"><i class="ph-bold ph-graduation-cap"></i></div><div class="who">Smart LMS</div></div>`;
  blocks.forEach(block => {
    wrapper.appendChild(renderBlock(block));
  });
  thread.appendChild(wrapper);
  thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
}

function renderBlock(block) {
  switch (block.type) {
    case 'flashcard_set': return renderFlashcardSet(block);
    case 'quiz':          return renderQuiz(block);
    case 'summary':       return renderSummary(block);
    case 'exam':          return renderExam(block);
    default:              return renderUnknown(block);
  }
}

// ── Flashcard set ─────────────────────────────────────────────────────────────

function renderFlashcardSet(block) {
  const frag = document.createDocumentFragment();
  const head = mkBlockHead('ph-cards', `Flashcards · tap to flip${block.heading ? ' · ' + escHtml(block.heading) : ''}`);
  frag.appendChild(head);
  const grid = document.createElement('div');
  grid.className = 'card-grid';
  (block.cards || []).forEach(card => {
    const fc = document.createElement('div');
    fc.className = 'flashcard';
    fc.innerHTML = `
      <div class="flashcard-inner">
        <div class="face front">
          <div class="tag">${escHtml(card.tag || 'Term')}</div>
          <div class="q">${escHtml(card.front)}</div>
          <div class="hint"><i class="ph ph-hand-tap"></i> Tap to reveal</div>
        </div>
        <div class="face back">
          <div class="tag">Answer</div>
          <div class="a">${escHtml(card.back)}</div>
        </div>
      </div>`;
    fc.addEventListener('click', () => fc.classList.toggle('flipped'));
    grid.appendChild(fc);
  });
  frag.appendChild(grid);
  return frag;
}

// ── Quiz ──────────────────────────────────────────────────────────────────────

function renderQuiz(block) {
  const frag = document.createDocumentFragment();
  frag.appendChild(mkBlockHead('ph-exam', `Quiz yourself${block.heading ? ' · ' + escHtml(block.heading) : ''}`));
  (block.questions || []).forEach((q, i) => {
    frag.appendChild(renderQuestion(q, i + 1));
  });
  return frag;
}

function renderQuestion(q, num) {
  const card = document.createElement('div');
  card.className = 'qcard';
  if (q.kind === 'true_false') {
    card.innerHTML = `
      <div class="qnum">Question ${num} · True / False</div>
      <div class="qtext">${escHtml(q.text)}</div>
      <div class="opts"></div>
      <div class="explain"><i class="ph-bold ph-check-circle"></i><span>${escHtml(q.explanation || '')}</span></div>`;
    const opts = card.querySelector('.opts');
    [{ label: 'True', val: true }, { label: 'False', val: false }].forEach(o => {
      const correct = o.val === q.correct;
      const div = mkOpt(o.label, o.label, correct);
      div.addEventListener('click', () => gradeOpt(div, card, correct));
      opts.appendChild(div);
    });
  } else {
    const opts = (q.options || []).map((opt, i) => ({ label: KEYS[i] || String(i + 1), text: opt, correct: i === q.correct }));
    card.innerHTML = `
      <div class="qnum">Question ${num} · Multiple choice</div>
      <div class="qtext">${escHtml(q.text)}</div>
      <div class="opts"></div>
      <div class="explain"><i class="ph-bold ph-check-circle"></i><span>${escHtml(q.explanation || '')}</span></div>`;
    const optsEl = card.querySelector('.opts');
    opts.forEach(o => {
      const div = mkOpt(o.label, o.text, o.correct);
      div.addEventListener('click', () => gradeOpt(div, card, o.correct));
      optsEl.appendChild(div);
    });
  }
  return card;
}

function mkOpt(key, text, correct) {
  const div = document.createElement('div');
  div.className = 'opt';
  if (correct) div.dataset.correct = '1';
  div.innerHTML = `<span class="key">${escHtml(key)}</span>${escHtml(text)}<i class="ph-bold ph-check-circle res ok"></i><i class="ph-bold ph-x-circle res no"></i>`;
  return div;
}

function gradeOpt(el, card, isCorrect) {
  if (card.classList.contains('answered')) return;
  card.classList.add('answered');
  if (isCorrect) {
    el.classList.add('correct');
  } else {
    el.classList.add('wrong');
    card.querySelector('[data-correct]').classList.add('correct');
  }
}

// ── Summary ───────────────────────────────────────────────────────────────────

function renderSummary(block) {
  const frag = document.createDocumentFragment();
  frag.appendChild(mkBlockHead('ph-article', `Summary${block.heading ? ' · ' + escHtml(block.heading) : ''}`));
  const div = document.createElement('div');
  div.className = 'summary-block';
  (block.sections || []).forEach(sec => {
    div.innerHTML += `<div class="sec-title">${escHtml(sec.title)}</div><div class="sec-body">${escHtml(sec.body)}</div>`;
  });
  frag.appendChild(div);
  return frag;
}

// ── Exam ──────────────────────────────────────────────────────────────────────

function renderExam(block) {
  const frag = document.createDocumentFragment();
  frag.appendChild(mkBlockHead('ph-clock', `Mock Exam${block.heading ? ' · ' + escHtml(block.heading) : ''}`));
  if (block.duration_minutes) {
    const dur = document.createElement('div');
    dur.className = 'exam-duration';
    dur.innerHTML = `<i class="ph ph-clock"></i> ${block.duration_minutes} minutes`;
    frag.appendChild(dur);
  }
  (block.questions || []).forEach((q, i) => {
    frag.appendChild(renderQuestion(q, i + 1));
  });
  if (block.answer_key && block.answer_key.length) {
    const ak = document.createElement('div');
    ak.className = 'answer-key';
    ak.innerHTML = `<div class="ak-title">Answer Key</div><div class="ak-grid">${
      block.answer_key.map(k => `<span class="ak-item"><strong>Q${k.q}</strong> ${escHtml(String(k.answer))}</span>`).join('')
    }</div>`;
    frag.appendChild(ak);
  }
  return frag;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderUnknown(block) {
  const p = document.createElement('p');
  p.textContent = `[Unknown block type: ${block.type}]`;
  return p;
}

function mkBlockHead(icon, label) {
  const div = document.createElement('div');
  div.className = 'block-head';
  div.innerHTML = `<i class="ph ${icon}"></i> ${escHtml(label)}`;
  return div;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Theme ─────────────────────────────────────────────────────────────────────

function toggleTheme() {
  const h = document.documentElement;
  h.dataset.theme = h.dataset.theme === 'dark' ? 'light' : 'dark';
}

function togglePop() {
  document.getElementById('pop').classList.toggle('open');
}

// ── Textarea auto-resize ──────────────────────────────────────────────────────

function initTextarea() {
  const ta = document.querySelector('textarea');
  if (!ta) return;
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = ta.scrollHeight + 'px';
  });
  ta.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSend();
    }
  });
}

function doSend() {
  const ta = document.querySelector('textarea');
  if (!ta) return;
  const text = ta.value.trim();
  if (!text) return;
  submitPrompt(text, getSelectedCourseIds(), getSelectedDocIds());
  ta.value = '';
  ta.style.height = 'auto';
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  connectSSE();
  loadSessions();
  loadCourses();
  initTextarea();
  const sendBtn = document.querySelector('.send');
  if (sendBtn) sendBtn.addEventListener('click', doSend);
  const newChat = document.querySelector('.new-chat');
  if (newChat) newChat.addEventListener('click', () => {
    window.location.href = `/?session=${crypto.randomUUID()}`;
  });
});
