const SESSION_ID = new URLSearchParams(window.location.search).get('session') || 'default';

const KEYS = ['A', 'B', 'C', 'D'];

// ── SSE ──────────────────────────────────────────────────────────────────────

function connectSSE() {
  const es = new EventSource(`/api/events/${SESSION_ID}`);
  es.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'blocks') renderBlocks(msg.blocks, true);
    } catch (_) {}
  };
  es.onerror = () => setTimeout(connectSSE, 3000);
  
  // Load history on connect to ensure refresh doesn't wipe content
  loadHistory();
  return es;
}

async function loadHistory() {
  try {
    const res = await fetch(`/api/sessions/${SESSION_ID}`);
    if (!res.ok) return;
    const session = await res.json();
    const thread = document.getElementById('thread');
    if (!thread) return;
    thread.innerHTML = '';
    (session.turns || []).forEach(turn => {
      if (turn.role === 'user') {
        appendUserMessage(turn.text, [], [], false);
      } else {
        renderBlocks(turn.blocks || [], false);
      }
    });
    // Scroll to bottom after loading history
    setTimeout(() => {
      thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
    }, 50);
  } catch (_) {}
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function submitPrompt(text, courseIds, docIds) {
  if (!text.trim()) return;
  appendUserMessage(text, courseIds, docIds, true);
  showThinking();
  await fetch(`/api/prompt/${SESSION_ID}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, course_ids: courseIds, doc_ids: docIds }),
  });
}

// ── Sidebar sessions ──────────────────────────────────────────────────────────

async function loadSessions() {
  try {
    const res = await fetch('/api/sessions');
    const sessions = await res.json();
    const list = document.getElementById('session-list');
    if (!list) return;
    list.innerHTML = sessions.map(s => `
      <div class="nav-item ${s.id === SESSION_ID ? 'active' : ''}" data-id="${s.id}">
        <i class="ph ph-book-open"></i>
        <span class="session-title">${escHtml(s.title)}</span>
        <div class="session-actions">
          <button class="action-btn rename-btn" title="Rename"><i class="ph ph-pencil-simple"></i></button>
          <button class="action-btn delete-btn" title="Delete"><i class="ph ph-trash"></i></button>
        </div>
      </div>`).join('');
    
    list.querySelectorAll('.nav-item').forEach(el => {
      const sid = el.dataset.id;
      
      // Navigation: click anywhere on the item EXCEPT action buttons
      el.addEventListener('click', (e) => {
        if (!e.target.closest('.action-btn')) {
          window.location.href = `/?session=${sid}`;
        }
      });

      // Rename functionality: ONLY on pencil button
      const renameBtn = el.querySelector('.rename-btn');
      renameBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const titleSpan = el.querySelector('.session-title');
        const newTitle = prompt("Enter new session title:", titleSpan.textContent);
        if (newTitle && newTitle.trim()) {
          fetch(`/api/sessions/${sid}/rename`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle.trim() })
          }).then(() => loadSessions());
        }
      });

      // Delete functionality
      el.querySelector('.delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm("Are you sure you want to delete this session?")) {
          fetch(`/api/sessions/${sid}`, { method: 'DELETE' })
            .then(() => {
              if (sid === SESSION_ID) window.location.href = '/';
              else loadSessions();
            });
        }
      });
    });
  } catch (_) {}
}

function initUserRow() {
  const userRow = document.querySelector('.user-row');
  if (userRow) {
    userRow.addEventListener('click', () => {
      alert("Student Profile: 24soft1016@isik.edu.tr\nLMS connected successfully.");
    });
  }
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

function appendUserMessage(text, courseIds, docIds, scroll = true) {
  const thread = document.getElementById('thread');
  if (!thread) return;
  const courseNames = [...document.querySelectorAll('#course-list .pop-item.sel')]
    .map(el => el.querySelector('div > div').textContent.trim());
  const pillsHtml = (courseNames || []).map(n =>
    `<span class="src-pill"><i class="ph ph-book-bookmark"></i> ${escHtml(n)}</span>`
  ).join('');
  const msg = document.createElement('div');
  msg.className = 'msg user-msg';
  msg.innerHTML = `
    <div class="msg-role"><div class="dot user">Y</div><div class="who">You</div></div>
    <div class="user-text">${escHtml(text)}</div>
    ${pillsHtml ? `<div class="source-pills">${pillsHtml}</div>` : ''}`;
  thread.appendChild(msg);
  if (scroll) thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
}

function showThinking() {
  const thread = document.getElementById('thread');
  if (!thread) return;
  const msg = document.createElement('div');
  msg.className = 'msg ai-msg thinking-msg';
  msg.innerHTML = `
    <div class="msg-role"><div class="dot ai"><i class="ph-bold ph-graduation-cap"></i></div><div class="who">Smart LMS</div></div>
    <div class="ai-text thinking-dots"><span>.</span><span>.</span><span>.</span></div>
  `;
  thread.appendChild(msg);
  thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
}

function hideThinking() {
  const thread = document.getElementById('thread');
  if (!thread) return;
  const thinkingMsgs = thread.querySelectorAll('.thinking-msg');
  thinkingMsgs.forEach(m => m.remove());
}

function renderBlocks(blocks, scroll = true) {
  hideThinking();
  const thread = document.getElementById('thread');
  if (!thread) return;
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ai-msg';
  wrapper.innerHTML = `<div class="msg-role"><div class="dot ai"><i class="ph-bold ph-graduation-cap"></i></div><div class="who">Smart LMS</div></div>`;
  blocks.forEach(block => {
    wrapper.appendChild(renderBlock(block));
  });
  thread.appendChild(wrapper);
  if (scroll) thread.parentElement.scrollTop = thread.parentElement.scrollHeight;
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

function initTheme() {
  const savedTheme = localStorage.getItem('smart_lms_theme');
  if (savedTheme) {
    document.documentElement.dataset.theme = savedTheme;
  }
}

function toggleTheme() {
  const h = document.documentElement;
  const newTheme = h.dataset.theme === 'dark' ? 'light' : 'dark';
  h.dataset.theme = newTheme;
  localStorage.setItem('smart_lms_theme', newTheme);
}

function togglePop(e, id) {
  if (e) e.stopPropagation();
  // Close others
  document.querySelectorAll('.popover').forEach(p => {
    if (p.id !== id) p.classList.remove('open');
  });
  const pop = document.getElementById(id);
  if (pop) pop.classList.toggle('open');
}

// Close popover on outside click
window.addEventListener('click', (e) => {
  document.querySelectorAll('.popover').forEach(pop => {
    if (pop.classList.contains('open') && !pop.contains(e.target) && !e.target.closest('.tool-btn')) {
      pop.classList.remove('open');
    }
  });
});

async function loadMaterials(courseId) {
  const docList = document.getElementById('doc-list');
  if (!docList) return;
  docList.innerHTML = '<div class="pop-item"><div class="sub">Loading materials...</div></div>';
  try {
    const res = await fetch(`/api/materials/${courseId}`);
    const mats = await res.json();
    if (!mats.length) {
      docList.innerHTML = '<div class="pop-item"><div class="sub">No materials found.</div></div>';
      return;
    }
    
    // Add Select All button
    let html = `
      <div class="pop-item select-all" style="border-bottom: 1px solid var(--border); border-radius: 0; margin-bottom: 4px;">
        <span class="ck"><i class="ph-bold ph-check"></i></span>
        <div><div style="font-weight: 600;">Select / Deselect All</div></div>
      </div>
    `;
    
    html += mats.map(m => `
      <div class="pop-item doc-item sel" data-doc-id="${m.id}" data-doc-title="${escHtml(m.title)}">
        <span class="ck"><i class="ph-bold ph-check"></i></span>
        <div><div class="sub" style="color:var(--text);">${escHtml(m.title)}</div></div>
      </div>`).join('');
      
    docList.innerHTML = html;
    
    const selectAllBtn = docList.querySelector('.select-all');
    let allSelected = true;
    selectAllBtn.classList.add('sel'); // Initially all are selected
    
    selectAllBtn.addEventListener('click', () => {
      allSelected = !allSelected;
      if (allSelected) {
        selectAllBtn.classList.add('sel');
        docList.querySelectorAll('.doc-item').forEach(el => el.classList.add('sel'));
      } else {
        selectAllBtn.classList.remove('sel');
        docList.querySelectorAll('.doc-item').forEach(el => el.classList.remove('sel'));
      }
      updateCourseChips();
    });
    
    docList.querySelectorAll('.pop-item.doc-item').forEach(el => {
      el.addEventListener('click', () => {
        el.classList.toggle('sel');
        updateCourseChips();
        
        // Update select all button state
        const allItems = docList.querySelectorAll('.doc-item');
        const selItems = docList.querySelectorAll('.doc-item.sel');
        if (selItems.length === 0) {
            selectAllBtn.classList.remove('sel');
            allSelected = false;
        } else if (selItems.length === allItems.length) {
            selectAllBtn.classList.add('sel');
            allSelected = true;
        } else {
            // Partially selected state (can just remove the checkmark for simplicity)
            selectAllBtn.classList.remove('sel');
            allSelected = false;
        }
      });
    });
    updateCourseChips(); // Refresh chips to show docs
  } catch (_) {
    docList.innerHTML = '<div class="pop-item"><div class="sub">Failed to load.</div></div>';
  }
}


function toggleCourse(el) {
  // Deselect others (single course logic for now to keep materials simple)
  document.querySelectorAll('#course-list .pop-item').forEach(p => p.classList.remove('sel'));
  el.classList.add('sel');
  
  const courseId = el.dataset.courseId;
  const btnDocs = document.getElementById('btn-docs');
  if (btnDocs) btnDocs.style.display = 'inline-flex';
  
  loadMaterials(courseId);
  updateCourseChips();
}

function getSelectedDocIds() {
  return [...document.querySelectorAll('#doc-list .pop-item.sel')]
    .map(el => el.dataset.docId);
}

function updateCourseChips() {
  const attached = document.querySelector('.attached');
  if (!attached) return;
  attached.innerHTML = '';
  
  document.querySelectorAll('#course-list .pop-item.sel').forEach(el => {
    const name = el.querySelector('div > div').textContent.trim();
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.dataset.courseId = el.dataset.courseId;
    
    const docs = [...document.querySelectorAll('#doc-list .pop-item.sel')];
    const docText = docs.length ? ` (+${docs.length} docs)` : '';
    
    chip.innerHTML = `<i class="ph lead ph-book-bookmark"></i> ${escHtml(name)}${docText} <span class="x"><i class="ph ph-x"></i></span>`;
    chip.querySelector('.x').addEventListener('click', () => {
      chip.remove();
      el.classList.remove('sel');
      const btnDocs = document.getElementById('btn-docs');
      if (btnDocs) btnDocs.style.display = 'none';
      document.getElementById('doc-list').innerHTML = '<div class="pop-item"><div class="sub">Select a course first</div></div>';
    });
    attached.appendChild(chip);
  });
}


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
  initTheme();
  connectSSE();
  loadSessions();
  loadCourses();
  initTextarea();
  initUserRow();
  const sendBtn = document.querySelector('.send');
  if (sendBtn) sendBtn.addEventListener('click', doSend);
  const newChat = document.querySelector('.new-chat');
  if (newChat) newChat.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: "New Study Session" })
      });
      const data = await res.json();
      if (data.id) window.location.href = `/?session=${data.id}`;
    } catch (_) {
      window.location.href = `/?session=${crypto.randomUUID()}`;
    }
  });
});
